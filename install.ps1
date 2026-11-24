<#
  Instalador do Jarvis para um computador novo (Windows 10/11).

  Uso:  install.bat                  (pergunta o que for opcional)
        install.bat -Tudo            (instala também o modelo de código e o ComfyUI + FLUX)
        install.bat -SemPerguntas    (só o essencial, sem perguntar nada)

  Faz, nesta ordem (pode rodar de novo: o que já existe é pulado):
    1. Python 3.13, ffmpeg e Ollama (pelo winget)
    2. venv com as bibliotecas do requirements.txt
    3. arquivo .env (a partir do .env.example, com token aleatório)
    4. modelos do Ollama (gemma4:26b, qwen3-embedding:0.6b e, se quiser, qwen3.8:27b)
    5. modelos do Whisper e da voz Kokoro
    6. (opcional) ComfyUI portátil + FLUX.2 klein para imagens
    7. atalho "Jarvis" na área de trabalho e teste rápido
#>
param([switch]$Tudo, [switch]$SemPerguntas)

# "Continue": avisos que pip/ollama escrevem no stderr não podem derrubar o instalador
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"   # sem isso o Invoke-WebRequest fica muito lento
$Root = $PSScriptRoot
Set-Location $Root
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

function Passo($texto) { Write-Host ""; Write-Host "==> $texto" -ForegroundColor Cyan }
function Ok($texto)    { Write-Host "    OK  $texto" -ForegroundColor Green }
function Aviso($texto) { Write-Host "    !!  $texto" -ForegroundColor Yellow }
function Tem($cmd)     { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Recarregar-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}
function Perguntar($texto, $padrao) {
    if ($Tudo) { return $true }
    if ($SemPerguntas) { return $padrao }
    $sufixo = if ($padrao) { "[S/n]" } else { "[s/N]" }
    $r = Read-Host "    $texto $sufixo"
    if ([string]::IsNullOrWhiteSpace($r)) { return $padrao }
    return $r.Trim().ToLower().StartsWith("s")
}
function Winget-Instalar($id, $nome) {
    if (-not (Tem "winget")) { throw "winget não encontrado. Instale o 'App Installer' pela Microsoft Store e rode de novo." }
    Write-Host "    Instalando $nome..."
    winget install --id $id -e --accept-source-agreements --accept-package-agreements --silent | Out-Host
    Recarregar-Path
}

Write-Host "Instalador do Jarvis" -ForegroundColor Cyan
Write-Host "Pasta: $Root"

# ---------------------------------------------------------------- 1. programas
Passo "1/7 Programas: Python, ffmpeg, Ollama"
$Python = $null
function Achar-Python {
    foreach ($v in @("3.13", "3.12", "3.11")) {
        if (Tem "py") {
            $p = cmd /c "py -$v -c ""import sys; print(sys.executable)"" 2>nul"
            if ($LASTEXITCODE -eq 0 -and $p) { return "$p".Trim() }
        }
    }
    if (Tem "python") {
        $p = cmd /c "python -c ""import sys; print(sys.executable if (3,11) <= sys.version_info[:2] <= (3,13) else '')"" 2>nul"
        if ($LASTEXITCODE -eq 0 -and "$p".Trim() -and "$p" -notmatch "WindowsApps") { return "$p".Trim() }
    }
    return $null
}
$Python = Achar-Python
if (-not $Python) {
    Winget-Instalar "Python.Python.3.13" "Python 3.13"
    $Python = Achar-Python
    if (-not $Python) { throw "Python 3.13 instalado, mas não achei. Feche e abra o terminal e rode o install.bat de novo." }
}
Ok "Python: $Python"

if (Tem "ffmpeg") { Ok "ffmpeg" } else { Winget-Instalar "Gyan.FFmpeg" "ffmpeg"; Ok "ffmpeg instalado" }

if (Tem "ollama") { Ok "Ollama" } else { Winget-Instalar "Ollama.Ollama" "Ollama"; Ok "Ollama instalado" }

if (Tem "nvidia-smi") {
    $gpu = (cmd /c "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>nul" | Select-Object -First 1)
    Ok "Placa de vídeo: $gpu"
} else {
    Aviso "Não achei placa NVIDIA (nvidia-smi). O Jarvis funciona, mas o Whisper e os modelos ficam lentos."
}
$chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
            "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
            "$env:LocalAppData\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ }
if ($chrome) { Ok "Chrome" } else { Aviso "Chrome não encontrado: o Jarvis usa o Edge no lugar (avatar, YouTube, chat)." }

# ---------------------------------------------------------------- 2. venv
Passo "2/7 Bibliotecas Python (venv)"
$VenvPy = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) { & $Python -m venv venv; Ok "venv criado" } else { Ok "venv já existe" }
& $VenvPy -m pip install --upgrade pip --disable-pip-version-check -q
& $VenvPy -m pip install -r requirements.txt --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { throw "pip falhou. Veja a mensagem acima." }
Ok "bibliotecas instaladas"

# ---------------------------------------------------------------- 3. .env
Passo "3/7 Configuração (.env)"
$EnvFile = Join-Path $Root ".env"
if (-not (Test-Path $EnvFile)) {
    $texto = Get-Content (Join-Path $Root ".env.example") -Raw -Encoding UTF8
    $bytes = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $token = [Convert]::ToBase64String($bytes).Replace("+", "-").Replace("/", "_").TrimEnd("=")
    $texto = $texto -replace "(?m)^SECRET_TOKEN_JARVIS=.*$", "SECRET_TOKEN_JARVIS=$token"
    if (-not $SemPerguntas) {
        $brave = Read-Host "    Chave da Brave Search (Enter para pular)"
        if ($brave) { $texto = $texto -replace "(?m)^BRAVE_API_KEY=.*$", "BRAVE_API_KEY=$brave" }
        $weather = Read-Host "    Chave do OpenWeather (Enter para pular)"
        if ($weather) { $texto = $texto -replace "(?m)^OPENWEATHER_API_KEY=.*$", "OPENWEATHER_API_KEY=$weather" }
        $cidade = Read-Host "    Sua cidade para o clima (Enter = Lexy)"
        if ($cidade) { $texto = $texto -replace "(?m)^JARVIS_HOME_CITY=.*$", "JARVIS_HOME_CITY=$cidade" }
    }
    [IO.File]::WriteAllText($EnvFile, $texto, (New-Object Text.UTF8Encoding $false))
    Ok ".env criado (token da API gerado). Edite depois para trocar as chaves."
} else {
    Ok ".env já existe (não mexi)"
}

# ---------------------------------------------------------------- 4. Ollama
Passo "4/7 Modelos do Ollama"
$OllamaUrl = "http://127.0.0.1:11434"
$linha = Select-String -Path $EnvFile -Pattern "^OLLAMA_HOST=(.+)$" | Select-Object -First 1
if ($linha) { $OllamaUrl = $linha.Matches[0].Groups[1].Value.Trim() }
if ($OllamaUrl -notmatch "^https?://") { $OllamaUrl = "http://$OllamaUrl" }
$env:OLLAMA_HOST = $OllamaUrl -replace "^https?://", ""
try { Invoke-WebRequest "$OllamaUrl/api/tags" -UseBasicParsing -TimeoutSec 3 | Out-Null }
catch {
    Write-Host "    Abrindo o Ollama..."
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 6
}
$modelos = @("gemma4:26b", "qwen3-embedding:0.6b")
if (Perguntar "Baixar também o modelo de programação qwen3.8:27b (~17 GB, para o modo programador)?" $false) {
    $modelos += "qwen3.8:27b"
}
foreach ($m in $modelos) {
    Write-Host "    ollama pull $m"
    & ollama pull $m
    if ($LASTEXITCODE -ne 0) { Aviso "Não consegui baixar $m. Rode depois: ollama pull $m" } else { Ok $m }
}

# ---------------------------------------------------------------- 5. Whisper e voz
Passo "5/7 Whisper (ouvir) e Kokoro (voz)"
& $VenvPy -X utf8 -m tests.prepare_whisper
if ($LASTEXITCODE -ne 0) { Aviso "Whisper não baixou; ele tenta de novo ao abrir o Jarvis." } else { Ok "Whisper" }
& $VenvPy -X utf8 -m tests.prepare_kokoro
if ($LASTEXITCODE -ne 0) { Aviso "Kokoro não baixou; o Jarvis usa a voz do Edge até lá." } else { Ok "Kokoro" }

# ---------------------------------------------------------------- 6. imagens
Passo "6/7 Imagens (ComfyUI + FLUX.2 klein, ~12 GB + 2 GB)"
$Comfy = "C:\ComfyUI"
if (Test-Path (Join-Path $Comfy "python_embeded")) {
    Ok "ComfyUI já está em $Comfy"
    & $VenvPy -X utf8 tests\prepare_flux.py $Comfy
} elseif (Perguntar "Instalar o gerador de imagens agora?" $false) {
    if (-not (Test-Path "$env:ProgramFiles\7-Zip\7z.exe")) { Winget-Instalar "7zip.7zip" "7-Zip" }
    $arquivo = Join-Path $env:TEMP "ComfyUI_windows_portable_nvidia.7z"
    Write-Host "    Baixando o ComfyUI portátil (~2 GB)..."
    Invoke-WebRequest "https://github.com/Comfy-Org/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z" -OutFile $arquivo -UseBasicParsing
    & "$env:ProgramFiles\7-Zip\7z.exe" x $arquivo "-oC:\" -y | Out-Null
    if (Test-Path "C:\ComfyUI_windows_portable") { Rename-Item "C:\ComfyUI_windows_portable" "ComfyUI" }
    Remove-Item $arquivo -ErrorAction SilentlyContinue
    & $VenvPy -X utf8 tests\prepare_flux.py $Comfy
    if ($LASTEXITCODE -eq 0) { Ok "ComfyUI + FLUX prontos" } else { Aviso "Modelos do FLUX não baixaram; rode depois: venv\Scripts\python.exe tests\prepare_flux.py" }
} else {
    Ok "pulado (depois: veja a seção Images do README)"
}

# ---------------------------------------------------------------- 7. atalho e teste
Passo "7/7 Atalho e teste rápido"
$desktop = [Environment]::GetFolderPath("Desktop")
$shell = New-Object -ComObject WScript.Shell
$atalho = $shell.CreateShortcut((Join-Path $desktop "Jarvis.lnk"))
$atalho.TargetPath = Join-Path $Root "start_jarvis.bat"
$atalho.WorkingDirectory = $Root
$atalho.Save()
Ok "atalho 'Jarvis' na área de trabalho"

$logTeste = Join-Path $env:TEMP "jarvis_testes.txt"
$proc = Start-Process -FilePath $VenvPy -ArgumentList "-X", "utf8", "tests\run_all.py" -WorkingDirectory $Root `
        -NoNewWindow -Wait -PassThru -RedirectStandardOutput $logTeste -RedirectStandardError "$logTeste.err"
$codigo = $proc.ExitCode
Get-Content "$logTeste.err", $logTeste -ErrorAction SilentlyContinue | Select-Object -Last 3 | Out-Host
if ($codigo -eq 0) { Ok "testes automáticos passaram" } else { Aviso "algum teste falhou (veja acima); o Jarvis ainda pode funcionar" }

Write-Host ""
Write-Host "Pronto! Para abrir o Jarvis: atalho 'Jarvis' na área de trabalho ou start_jarvis.bat" -ForegroundColor Green
Write-Host "Painel do que ele sabe: venv\Scripts\python.exe server.py  ->  http://127.0.0.1:11600/painel"
