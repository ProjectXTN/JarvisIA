; Instalador do Jarvis (Inno Setup 6). Gera JarvisSetup.exe.
; Compilado pelo GitHub Actions (.github/workflows/installer.yml) ou à mão:
;   iscc /DAppVersion=1.0.0 installer\jarvis.iss
; Espera Jarvis.exe já gerado em installer\dist\Jarvis.exe (PyInstaller).

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{8F3C2B71-6A1E-4C5B-9D2A-4A7E9B1C0D55}
AppName=Jarvis
AppVersion={#AppVersion}
AppPublisher=Pedro Meireles
AppPublisherURL=https://pedromeireles.dev
DefaultDirName={localappdata}\Jarvis
DefaultGroupName=Jarvis
DisableProgramGroupPage=yes
; Pasta do usuário: sem pedir administrador e o Jarvis pode escrever (venv, logs, memória)
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=JarvisSetup
SetupIconFile=jarvis.ico
UninstallDisplayIcon={app}\Jarvis.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Atalho na área de trabalho"; GroupDescription: "Atalhos:"
Name: "startup"; Description: "Abrir o Jarvis junto com o Windows"; GroupDescription: "Inicialização:"; Flags: unchecked
Name: "startupapi"; Description: "Abrir a API do site (pedromeireles.dev) junto com o Windows"; GroupDescription: "Inicialização:"; Flags: unchecked

[Files]
Source: "dist\Jarvis.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "jarvis.ico"; DestDir: "{app}"; Flags: ignoreversion
; O projeto inteiro, menos o que é gerado no PC (venv, modelos, logs) e dados pessoais
Source: "..\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion; \
  Excludes: ".git,.github,venv,models,logs,dist,build,*.db,.env,__pycache__,*.pyc,codes,data,stable-diffusion-webui,jarvis_index,*.spec,jarvis.lock"

[Icons]
Name: "{group}\Jarvis"; Filename: "{app}\Jarvis.exe"; WorkingDir: "{app}"
Name: "{group}\Jarvis - painel do que ele sabe"; Filename: "{app}\Jarvis.exe"; Parameters: "--painel"; WorkingDir: "{app}"
Name: "{group}\Jarvis - API do site"; Filename: "{app}\Jarvis.exe"; Parameters: "--api"; WorkingDir: "{app}"
Name: "{group}\Jarvis - atualizar bibliotecas e modelos"; Filename: "{app}\Jarvis.exe"; Parameters: "--instalar"; WorkingDir: "{app}"
Name: "{group}\Desinstalar o Jarvis"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Jarvis"; Filename: "{app}\Jarvis.exe"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userstartup}\Jarvis"; Filename: "{app}\start_jarvis.vbs"; WorkingDir: "{app}"; Tasks: startup
Name: "{userstartup}\Jarvis API"; Filename: "{app}\start_api.vbs"; WorkingDir: "{app}"; Tasks: startupapi

[Run]
; Instala Python, bibliotecas, Ollama e modelos (pergunta as chaves da Brave/OpenWeather)
Filename: "{app}\install.bat"; WorkingDir: "{app}"; Description: "Instalar bibliotecas e modelos agora (necessário na primeira vez)"; \
  Flags: postinstall waituntilterminated shellexec
Filename: "{app}\Jarvis.exe"; WorkingDir: "{app}"; Description: "Abrir o Jarvis"; Flags: postinstall nowait skipifsilent unchecked

[UninstallDelete]
; Some o que foi gerado no PC. A memória (brain\learning\*.db) e o .env ficam,
; para não perder nada se reinstalar; apague a pasta à mão se quiser zerar.
Type: filesandordirs; Name: "{app}\venv"
Type: filesandordirs; Name: "{app}\models"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\__pycache__"
