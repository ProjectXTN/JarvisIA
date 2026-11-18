# Plano de refatoração do Jarvis (2026)

Acompanhamento do trabalho no branch `refactor-2026`.
`[x]` = feito · `[ ]` = pendente · `[-]` = descartado. A coluna "Onde" indica os arquivos alterados.

Última atualização: 2026-11-18

## Fase 0 — Preparar o terreno

- [x] 1. Criar o branch `refactor-2026`
- [x] 2. Apagar o `jarvis.lock` preso
- [x] 3. Criar `core/settings.py` com URL do Ollama, modelos e limites num só lugar
- [x] 4. Corrigir o `requirements.txt`
- [x] 5. Tirar do git os bancos `memoria_jarvis.db` e a pasta `piper/`
- [x] 6. Apagar duplicados e código morto

## Fase 1 — Bugs que derrubam ou atrapalham

- [x] 7. Desligar só com frase explícita (`commands/commands_systeme.py`)
- [x] 8. Corrigir `aprendizado_ativado` e unificar o modo de estudo (`jarvis.py`)
- [x] 9. Hotword: desempacotar a tupla e subir o limite de similaridade (`core/initializer.py`)
- [x] 10. Lock com PID, ignorando lock de processo morto (`core/initializer.py`)
- [x] 11. LLM: erro devolve `None`, com timeout (`brain/memory/memory.py`)
- [x] 12. `try/except` no fallback de busca e LLM (`jarvis_commands.py`)
- [x] 13. Padrões de "horas" e "coloque" (`commands_day_time.py`, `commands_music.py`)
- [x] 14. Apagar o `.wav` temporário após transcrever (`brain/audio.py`)

## Fase 2 — Cérebro novo

- [x] 15. Baixar `qwen3.8:27b` e `gemma4:26b`, comparar em português e escolher (principal: `gemma4:26b`; reserva de código: `qwen3.8:27b`)
- [ ] 16. Remover `llama3.2`, `llama3.3`, `codestral`, `llava`, `llama3.2-vision:90b`
- [x] 17. Reescrever `llama_query` para `/api/chat` (system, histórico, `options`, `keep_alive`, `think: false`)
- [x] 18. Unificar os prompts de sistema num "Jarvis de voz"
- [x] 19. Ligar o histórico de conversa no fluxo de voz
- [x] 20. Trocar `start_llava()` por um aquecimento HTTP do modelo escolhido (HTTP /api/chat; Qwen configurado provisoriamente)
- [x] 21. Visão: enviar imagem em base64 pelo `/api/chat`
- [x] 22. Modelo reserva de código quando o principal recusar

## Fase 3 — Velocidade e naturalidade da voz

- [x] 23. Whisper `large-v3-turbo` na GPU, com volta automática para a CPU (`brain/whisper_loader.py`)
- [x] 24. Manter o microfone aberto entre escutas (`brain/microphone.py`)
- [x] 25. TTS local com Kokoro (`brain/tts.py`), Google TTS como reserva
- [x] 26. Streaming LLM → TTS frase a frase (`brain/speech_stream.py`; falta confirmar por voz)
- [x] 27. Tocar áudio com `sounddevice`, sem `ffplay` (WAV do Kokoro; MP3 do Google continua no `ffplay`)
- [x] 28. Interrupção por voz enquanto o Jarvis fala (só com ordem de parar; perguntas não interrompem)
- [x] 29. Bip local no lugar de "Jarvis Ativado..." e remover `sleep(0.5)`
- [-] 30. Hotword dedicada com `openWakeWord` (descartado: ver registro de 18/11)

## Fase 4 — Inteligência: ferramentas no lugar de regex

- [ ] 31. Transformar cada comando em ferramenta com descrição
- [ ] 32. Roteamento por tool calling em `process_command` (parcial: o modelo já decide se precisa buscar na internet)
- [ ] 33. Atalhos sem LLM para música, volume e desligar
- [ ] 34. Comandos encadeados via múltiplas ferramentas; apagar `commands_multiples.py`
- [x] 35. Busca web: `params=`, `User-Agent`, 4 páginas com prazo de 2,5 s, resumos da Brave
- [ ] 36. Cache com validade e limite de tamanho

## Fase 5 — Memória e RAG

- [ ] 37. RAG: carregar o índice uma vez e usar `as_retriever()`
- [ ] 38. Trocar o modelo de embeddings e reindexar
- [ ] 39. Memória de longo prazo com busca por semelhança
- [ ] 40. `auto_learning`: resumir antes de salvar, rejeitar erros, limitar ciclos
- [ ] 41. Resumo automático da conversa ao encerrar

## Fase 6 — Imagem, API e acabamento

- [ ] 42. Stable Diffusion sob demanda, alternando VRAM com o LLM
- [ ] 43. `server.py`: token obrigatório, `hmac.compare_digest`, sem global, sem `lower()`
- [ ] 44. Servir a API com `waitress` e restringir o CORS
- [ ] 45. `logging` com níveis e medição de tempo por etapa
- [ ] 46. Testes automáticos (desligamento, hotword, roteamento)
- [ ] 47. Atualizar `README.md`, `Dockerfile` e `build_jarvis.bat`

## Fase 7 — Jarvis vivo: personalidade, memória e aprendizado autônomo

Depende da Fase 2 (modelo novo com ferramentas). Substitui os itens 39 a 41 da Fase 5.

- [ ] 52. Personalidade própria em `brain/persona/`: traços fixos, humor do dia e opiniões que ele forma e guarda
- [ ] 53. Memória de longo prazo sobre o Pedro: fatos, preferências e projetos extraídos das conversas, com busca por semelhança
- [ ] 54. Diário: ao fim de cada dia, resumo do que conversaram e do que aprendeu, lido na próxima inicialização
- [ ] 55. Curiosidade: lista de temas a estudar, alimentada pelas conversas e pelos interesses do Pedro
- [ ] 56. Estudo autônomo quando o PC está ocioso: busca, lê, resume, confere em mais de uma fonte e guarda com a fonte
- [ ] 57. Reflexão noturna: revisa o que aprendeu, junta notas repetidas, marca contradições e atualiza opiniões
- [ ] 58. Iniciativa: puxa assunto sobre o que aprendeu, lembra compromissos, comenta novidades dos temas do Pedro
- [ ] 59. Painel "o que o Jarvis sabe": ver, corrigir e apagar memórias e aprendizados
- [ ] 60. Limites de segurança: internet só para leitura, nada de executar, comprar ou enviar sem permissão
- [ ] 61. (Opcional, avançado) Ajuste fino LoRA mensal com as conversas aprovadas pelo Pedro

## Fase 8 — Modo programador: criar apps de verdade

Depende da Fase 2 (modelo com ferramentas). Hoje o pedido de código só gera texto e é lido em voz alta.

- [ ] 62. Pasta de projetos `C:\Projetos\jarvis_apps\<nome-do-app>`, uma por pedido, com README do que foi pedido
- [ ] 63. Gerar o projeto em vários arquivos por ferramentas (`criar_arquivo`, `ler_arquivo`, `listar_pasta`); código nunca é falado
- [ ] 64. Ambiente isolado por projeto (venv próprio); comandos só dentro da pasta do projeto
- [ ] 65. Confirmação por voz antes de instalar pacotes, executar o app ou fazer build
- [ ] 66. Ciclo de correção: roda, lê o erro, corrige, até 5 tentativas; depois explica onde travou
- [ ] 67. Build quando fizer sentido (`pyinstaller` para .exe, `npm run build` para web) e abre a pasta ou o VS Code
- [ ] 68. Resumo falado curto: o que fez, onde salvou, como rodar
- [ ] 69. "Continue o app X": reabre um projeto antigo e altera em cima dele

## Extras pedidos durante o projeto

- [x] 48. Avatar holográfico 3D que fala (`brain/avatar/`, `commands/commands_avatar.py`)
- [x] 49. Avatar com anatomia humana: crânio, maxilar, nariz, lábios, pálpebras, orelhas e cabelo
- [x] 50. Avatar trocado por um núcleo neural de partículas (original), aberto sempre junto com o Jarvis
- [ ] 51. Novo gerador de imagens: ComfyUI com FLUX.2 [klein] 4B no lugar do Stable Diffusion 1.5

## Registro

### 2026-11-17 — Fases 0 e 1 concluídas

Feito no branch `refactor-2026` (nada foi enviado ao GitHub).

- **Configuração central:** `core/settings.py` passa a ser a única fonte da URL do Ollama e dos nomes de modelos. O RAG usava a porta 11500 fixa e o `initializer.py` testava a 11434; agora todos leem `OLLAMA_HOST` do `.env`.
- **Desligamento:** só frases inteiras de desligar ou de despedida encerram o Jarvis.
- **Hotword:** o modo passivo voltou a filtrar, e o limite de similaridade subiu de 0.6 para 0.8 (`HOTWORD_SIMILARITY`).
- **Lock:** guarda o PID e é ignorado quando o processo já morreu.
- **LLM:** falha do Ollama devolve `None` (não é mais falada, logada nem guardada em cache), há timeout, e a temperatura passou a ir em `options`.
- **Áudio:** o `.wav` temporário é apagado; `say()` ignora texto vazio e não trava sem rede.
- **Testes:** `tests/test_regressao.py` cobre os bugs acima (17 testes) e roda sem GPU nem microfone: `python -m unittest tests.test_regressao -v`.

Achados extras corrigidos no caminho:

- Um comando que devolvia `False` ("não era comigo") era confundido com pedido de desligar. Exemplo: "atualize o sistema" fechava o Jarvis. Agora a frase segue para o próximo comando ou para o LLM.
- A segunda instância apagava o lock da primeira ao desistir de iniciar.
- Os três `ollama run` da inicialização ficavam presos lendo o teclado do console; agora recebem prompt vazio e stdin fechado.
- O tempo de transcrição medido não incluía a transcrição de verdade (o faster-whisper só processa ao percorrer os segmentos).

Removidos: `commands/commands_emocionais.py` (cópia idêntica de `commands_emotions.py`), `temp.js`, `memoria_jarvis.db` vazio da raiz e 70 linhas mortas em `websearch.py`. O banco `brain/learning/memoria_jarvis.db` e a pasta `piper/` continuam no disco, só saíram do git.

Pendências para o Pedro:

- Testar no PC com microfone e GPU: hotword, "que horas são", desligar e uma pergunta ao LLM. Aqui só foi possível rodar os testes automáticos.
- Rodar `pip install -r requirements.txt` no venv (entrou `llama-index`).
- O `.gitattributes` tem comandos `git lfs track ...` no lugar de padrões; o git avisa a cada comando. Corrigir junto com a Fase 6.

### 2026-11-17 — Travamento no primeiro teste por voz

Sintoma: depois de "Jarvis, bom dia. Que horas é agora?" o console parou após a busca na web.

- "que horas é agora" não era reconhecido como pedido de hora (só "que horas são") e caía na busca web. Corrigido em `commands_day_time.py`.
- A inicialização carregava três modelos (visão 90B, llama3.2 e llama3.3 70B). Hipótese para a espera: a pergunta ficava na fila do Ollama atrás desses carregamentos. Agora só o modelo de conversa é pré-carregado, por HTTP, em segundo plano (item 20).
- A consulta ao RAG ganhou limite de 15 s, e o console avisa cada etapa (`[RAG]`, `[LLM]`) para se ver onde está parado.

### 2026-11-17 — Clima: cidade "Lexy" não era reconhecida

Sintoma: o Whisper ouviu "Alexi"/"Lexi" e a resposta do país virou "Pronto."; a consulta falhou.

- O Jarvis não pergunta mais o país. A cidade é resolvida pela geocodificação da OpenWeather (`resolve_location` em `brain/weatherAPI/weatherAPI.py`).
- Nomes que soam como a cidade de casa viram a cidade de casa. Ela fica em `core/settings.py` (`HOME_CITY`, `HOME_COUNTRY`) e pode ser trocada pelo `.env`.
- O Whisper recebe uma lista de nomes próprios como dica de grafia (`WHISPER_VOCABULARY`).

### 2026-11-17 — Avatar holográfico (item 48)

- **O que é:** janela própria com um rosto 3D em malha de luz azul, gerado por fórmulas (sem imagens nem bibliotecas externas). Mostra o estado do Jarvis (ONLINE, OUVINDO, PROCESSANDO, FALANDO), a legenda da fala e mexe a boca no volume real da voz.
- **Como usar:** "Jarvis, mostre o avatar" e "Jarvis, feche o avatar". Para abrir sempre junto com o Jarvis, ponha `JARVIS_AVATAR_AUTO_OPEN=1` no `.env`.
- **Como funciona:** `brain/avatar/__init__.py` sobe um servidor local em `127.0.0.1:8765` e envia eventos à página `brain/avatar/static/index.html`. O volume da fala é medido com o `ffmpeg` antes de tocar. Sem `ffmpeg` no PATH, a boca usa um movimento genérico.
- **Ajuste fino:** se a boca mexer antes ou depois da voz, mude `AVATAR_AUDIO_DELAY_MS` em `core/settings.py`.
- **Ver sem o Jarvis:** abrir `brain/avatar/static/index.html` direto no navegador roda uma demonstração.
- **Testado:** servidor, eventos e medida de volume fora do Jarvis; visual conferido em Chrome. Falta o teste por voz no PC.

### 2026-11-17 — Rosto realista do avatar (item 49)

- O crânio deixou de ser uma esfera: largura, profundidade da face e da nuca seguem uma tabela de proporções humanas, e a frente do rosto é achatada.
- Novos detalhes de relevo: arco das sobrancelhas, órbitas, globo ocular, nariz com dorso, asas e narinas, lábios, queixo, maçãs do rosto, maxilar, orelhas e cabelo com topete.
- Traços em luz: sobrancelhas, pálpebras, nariz, sulco nasolabial, maxilar e orelhas.
- O pescoço fica atrás do rosto, como numa pessoa; a malha ficou mais densa.

### 2026-11-17 — Fase 7 planejada (Jarvis vivo)

O modelo do Ollama não muda sozinho ao ler a internet: os pesos são fixos. O que faz o Jarvis ficar mais inteligente com o tempo é a memória que cresce em volta do modelo (o que ele sabe sobre o Pedro, o que estudou, as opiniões que formou) e que entra em cada resposta. O ajuste fino (item 61) existe, mas é a última etapa e opcional.

### 2026-11-17 — Novo avatar e abertura automática (item 50)

- O rosto foi trocado por um núcleo neural original: 1.500 partículas ligadas como neurônios, núcleo de luz, filamentos internos e anéis em órbita.
- Repouso: respira devagar. Ouvindo: se contrai e recebe ondas. Processando: gira mais rápido, acende sinapses e filamentos. Falando: a superfície vibra no volume real da voz.
- `AVATAR_AUTO_OPEN` agora vem ligado: o avatar abre junto com o Jarvis. Para desligar, `JARVIS_AVATAR_AUTO_OPEN=0` no `.env`.
- O rosto anterior continua no histórico do git (commit `eabb5b6`).

### 2026-11-17 — Interrupção por voz e fala limpa (item 28)

- **Interromper:** enquanto fala, o Jarvis escuta o microfone com um Whisper pequeno (`base`). Só ordens de parar interrompem: "pare", "para", "pode parar", "parar de falar", "chega", "já entendi". A lista fica em `brain/speech_text.py` (`_STOP`).
- **Pergunta não é ordem:** "para que serve este item?", "o que significa pare?" e "como faço para parar o boss?" não interrompem. A diferença é o começo da frase e a pausa: "Para, que horas são?" (com pausa) é ordem; "Para que serve?" é pergunta.
- **Ordem com comando:** "Pare. Que horas são?" para a fala e já responde a hora.
- **Eco:** frases longas com a palavra no meio, iguais ao que o Jarvis está falando, são tratadas como a voz dele captada pela caixa de som.
- **Depois de interromper:** ele fica quieto até voltar a ouvir; avisos restantes do mesmo comando são descartados.
- **Fala limpa:** `prepare_for_speech` tira marcações como `[TÍTULO]`, links, setas e frases repetidas, e corta falas acima de 1.200 caracteres (`MAX_SPOKEN_CHARS`).
- **Busca na internet:** "pesquise na internet" passa a falar um resumo feito pelo modelo, não o texto cru das páginas.
- Para desligar a interrupção: `JARVIS_INTERRUPT=0` no `.env`.
- Testado só com os testes automáticos (28); falta o teste com microfone e caixa de som.

### 2026-11-17 — Pergunta sobre AION 2 travou 3 minutos

- "informações sobre a classe Ranger" foi tratada como pedido de código por causa da palavra "classe" e mandada ao `codestral` (22B, não carregado), que estourou os 180 s. `is_code_request` agora exige termos de programação ("código", "script", "regex", "html", "classe em python"...).
- O Whisper ouviu "AION II" como "dwayon ii". Criado `vocabulario.txt` na raiz: nomes de jogos, classes e termos que ele deve reconhecer. Edite e reinicie para acrescentar palavras.
- O console mostra na abertura se o Whisper roda na GPU ou na CPU (as transcrições de 4 a 10 s sugerem CPU).

### 2026-11-17 — Whisper na GPU (item 23)

- Causa da lentidão: o venv tem `torch 2.6.0+cpu`, e o código perguntava ao PyTorch se havia GPU. A resposta era sempre "não", e o Whisper rodava na CPU (5 a 6 s por frase).
- O faster-whisper roda pelo CTranslate2, que tem CUDA próprio. `brain/whisper_loader.py` detecta a GPU por ele, registra as DLLs do cuBLAS e do cuDNN instaladas pelo pip e confere com uma transcrição de teste. Se falhar, volta para a CPU e mostra o comando para instalar o que falta.
- Modelo na GPU: `large-v3-turbo` (ouve e interrompe); na CPU continua o `medium`.
- `import whisper` e `import torch` saíram do `audio.py`, o que também deixa a abertura mais rápida.
- Pendente do Pedro: `venv\Scripts\python.exe -m pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"`.


### 2026-11-17 - Fase 2: integração pronta; comparação aguardando Gemma

Trabalho no branch `refactor-2026`. **A Fase 2 ainda não está inteiramente concluída.**

- **Servidor confirmado:** Ollama `0.40.16`, em `http://127.0.0.1:11500`, conforme o `.env`. A porta 11434 não está em uso. O Qwen já estava instalado; o Gemma não constava em `/api/tags`.
- **Modelos:** `qwen3.8:27b` como principal provisório, também para visão e perguntas complexas; `gemma4:26b` como reserva de código assim que o download terminar. Os nomes continuam configuráveis em `core/settings.py`/`.env`. Nenhum modelo antigo foi apagado: item 16 depende da validação dos substitutos.
- **Chat (17–18):** `brain/memory/memory.py` usa `/api/chat`, mensagens system/user/assistant, `think: false`, `options`, `keep_alive`, limite de saída e um único prompt Jarvis de voz. Falhas retornam `None`; código preserva linhas e indentação. `JARVIS_NUM_CTX` controla o contexto (4096 por padrão), `JARVIS_OLLAMA_TIMEOUT` controla a espera (180 s por padrão).
- **Histórico (19):** o fallback de voz passou a guardar cinco turnos. Respostas de busca web guardam a pergunta original, sem gravar os documentos recuperados. API, traduções, visão e geração autônoma de temas ficam isoladas. O cache por texto foi retirado da conversa por voz porque devolvia respostas antigas para perguntas dependentes do contexto. Pedidos de código recebem o histórico de voz e guardam o resultado final.
- **Aquecimento (20):** `start_ollama()` consulta os modelos no mesmo servidor HTTP e aquece somente o principal, com o mesmo contexto da inferência. Não baixa modelos silenciosamente na abertura. `start_llava` permanece como alias de compatibilidade.
- **Visão (21):** `jarvis_vision.py` lê a imagem e envia bytes em base64 em `messages[].images`; respeita a pergunta do usuário, limita o arquivo a 20 MB e devolve `None` em falhas de leitura/inferência.
- **Reserva (22):** programação começa no principal e tenta a reserva uma única vez após recusa explícita. Respostas normais e erros de rede não acionam outro modelo. Se a reserva estiver ausente ou falhar, preserva a resposta original. Fluxo validado com testes simulados; validação real com Gemma ainda pendente.

#### Teste real do Qwen

Pedro confirmou que estava jogando AION 2 simultaneamente. Portanto, **os tempos não medem a velocidade com a GPU livre**. Testes iniciais em GPU automática excederam 180 s; não foi aplicado um ajuste permanente baseado nessa disputa de recursos. Para terminar a validação funcional durante o jogo, o script de teste usou `--num-gpu 32` e geração especulativa desligada somente nessa execução. A configuração normal do Jarvis mantém a alocação automática da GPU.

| Caso | Resultado observado | Tempo total |
| --- | --- | --- |
| Português | Explicação correta do céu azul em duas frases | 44,73 s (13,79 s de carga) |
| Cálculo | **Errou:** respondeu R$ 14,257; correto: 35/1000 × 109 + 0,447 = R$ 4,262 (R$ 4,26 arredondados) | 10,88 s |
| Histórico | Recuperou corretamente “Aurora” e “76 milímetros” | 7,54 s |
| Código | Gerou `soma_pares` com `sum(n for n in numeros if n % 2 == 0)` | 18,16 s |
| Visão | Identificou corretamente um quadrado vermelho em imagem sintética enviada em base64 | 13,16 s |

Resultados brutos em `logs/fase2_qwen.json`. Teste reproduzível: `venv\Scripts\python.exe -X utf8 -m tests.benchmark_ollama`. A opção `--num-gpu` só afeta o teste, não as configurações do aplicativo. Não declarar vencedor antes de comparar o Gemma; não confiar no cálculo de custos sem validação determinística.

#### Download e próximos passos

- Gemma: download iniciado pelo servidor configurado (aproximadamente 18 GB). Mantido em processo de segundo plano com `tests/pull_ollama_model.py gemma4:26b --benchmark`.
- Acompanhar `logs/gemma4_download.log`; erros em `logs/gemma4_download_error.log`. Ao concluir, o processo testa português, cálculo, histórico, código e visão e grava `logs/fase2_gemma.json`. Esse processo não altera modelos escolhidos nem marca tarefas como concluídas automaticamente.
- **Item 15 pendente:** terminar o download, conferir os resultados do Gemma, comparar e confirmar modelo principal/reserva. Os testes do Gemma usarão a configuração normal da GPU; repetir medidas de velocidade sem o jogo se for necessário compará-las.
- **Item 16 pendente:** só remover os modelos antigos listados no item após confirmar os substitutos.
- Teste completo com microfone/alto-falantes ainda não realizado nesta etapa. As alterações passam a valer na próxima inicialização do Jarvis.

#### Validação automatizada

42 testes: `tests.test_regressao` + `tests.test_fase2`, cobrindo erros, papéis de chat, histórico, isolamento da API, limite da memória, reserva de código, base64, aquecimento e cache de voz. No ambiente restrito do Codex/Windows, `TemporaryDirectory` com modo 0700 impediu acesso aos próprios diretórios de teste; a execução final usou um wrapper apenas de teste que cria esses diretórios com o modo padrão 0777. Nenhum ajuste de permissões foi aplicado ao aplicativo. Executar normalmente no terminal local: `venv\Scripts\python.exe -X utf8 -m unittest tests.test_regressao tests.test_fase2 -v`.


### 2026-11-17 - Travamento após falar a data: reprodução e interrupção

Pedro relatou que, após responder “Hoje é 17/11/2026”, o console não voltou a “Listening with VAD”. A data é um comando local: essa resposta não depende da inferência do Qwen. O log não inclui stack trace, portanto não prova em qual chamada nativa a instância parou.

- **Caminho de bloqueio identificado:** `_play_interruptible` executava a transcrição de interrupção sincronamente, dentro do laço do player, e compartilhava `transcribe_lock` com a escuta principal. Uma transcrição lenta podia impedir o retorno mesmo após terminar o som. A captura também usava `stream.read` bloqueante.
- **Correção:** `brain/playback.py` isola o reconhecimento em no máximo um worker daemon. O laço acompanha o fim de `ffplay`, recebe frames por callback/fila limitada e não espera a inferência. Cada pedido possui fila própria; resultados atrasados são descartados. Após 2 s, uma transcrição pendente é ignorada para aquela fala. O modelo de interrupção não segura mais o lock do modelo principal.
- **Limites e limpeza:** reprodução tem prazo proporcional ao texto (20–180 s); encerramento do player usa terminate/kill com waits de 2 s. A entrada do microfone de interrupção é abortada/fechada; `listen()` também fecha o stream ao concluir. O MP3 temporário é fechado antes de passar ao ffmpeg/ffplay e removido em `finally`. Console informa `[AUDIO] Reprodução encerrada; voltando à escuta.`
- **Whisper:** o erro `CAS service / IncompleteBody` do log foi falha de download, não evidência de CUDA ausente (o modelo base de interrupção chegou a funcionar na GPU). O aviso agora distingue modelo ausente/download de erros de DLL. Por padrão, a abertura usa somente modelos já em cache e volta ao medium CPU se o modelo GPU estiver incompleto, evitando novo download de vários minutos durante a inicialização. Para permitir o comportamento antigo: `JARVIS_WHISPER_ALLOW_DOWNLOAD=1`.
- **Preparação separada:** `venv\Scripts\python.exe -X utf8 -m tests.prepare_whisper` baixa o modelo configurado com até três tentativas. A tentativa iniciada pelo Codex falhou por conexão recusada ao proxy de rede deste ambiente; o modelo grande continua incompleto. O comando deve ser executado no PowerShell local com acesso ao Hugging Face. O script não altera as bibliotecas instaladas nem instala CUDA.
- **Validação:** 52 testes de regressão/Fase 2/reprodução/carregamento do Whisper passaram (mesmo wrapper de diretórios temporários descrito acima). Incluem transcrição presa após fim do áudio, resultado atrasado, ausência de frames, ordem de parar, timeout e kill do player, e cache incompleto sem aviso incorreto de CUDA. Sintaxe dos sete arquivos desta correção validada. Ainda é necessário repetir a conversa no PC com microfone/alto-falantes; nenhuma instância do Jarvis do usuário foi encerrada automaticamente.


### 2026-11-17 - Espera nas notícias após busca web/RAG

O novo log confirma que a reprodução voltou à escuta. A espera seguinte ocorre no caminho busca → RAG → Qwen. O log do Ollama consultado nesta sessão registrou uma tentativa recente de `/api/chat` cancelada após 4m10s, antes de terminar o carregamento do runner; não é prova de qual instância originou a chamada. O servidor estava sem modelos carregados ao consultar `/api/ps`.

- **Notícias:** novo `brain/websearch/news.py`, usado tanto pelo pipeline de atualidades quanto pelo comando explícito de busca. Busca até três títulos/resumos no índice de notícias da Brave, com `params=` e limite de rede. Pedidos de notícias do dia/hoje usam `freshness=pd`; o filtro não comprova que todos os fatos ocorreram hoje. Se o índice de notícias retornar 401/403/404, tenta o índice web. Texto é limpo e limitado por item; URLs são registradas no console.
- **Sem RAG para notícias:** não carrega embeddings nem consulta documentos internos nesse caminho. As demais consultas mantêm o comportamento anterior.
- **Resumo limitado:** modo `news` pede até 192 tokens e usa timeout de leitura de 45 s por padrão (`JARVIS_NEWS_LLM_TIMEOUT`). Se o LLM falhar/demorar, a resposta usa os títulos realmente retornados, informando que o resumo não ficou pronto. Se a busca falhar, informa indisponibilidade e não pede ao modelo que invente notícias. O histórico de voz recebe só a resposta entregue.
- **Progresso:** chamadas ao LLM agora mostram quantidade de caracteres, aviso a cada dez segundos e tempo até receber a resposta. Isso não acelera o carregamento nem resolve a disputa de GPU com o jogo; torna a espera visível.
- **Validação:** 59 testes passaram, incluindo sete novos casos de notícias: desvio do RAG, fallback sem LLM, busca vazia, limite dos trechos, parâmetros/recência, timeout do resumo e fallback do índice. Mesma adaptação de diretórios temporários da execução anterior. Sintaxe validada. Não foi realizada uma nova conversa pelo microfone nem uma consulta real à Brave nesta etapa.
- Reiniciar a instância do Jarvis para carregar as correções. A tarefa geral de otimização da busca (item 35) permanece pendente para os outros tipos de consulta.

### 2026-11-18 — Bip de ativação (item 29)

- Ao ouvir "Jarvis", toca um bip local de 0,19 s (dois tons subindo) em vez de falar "Jarvis Ativado..." pelo Google TTS, que custava mais de 1 s por comando.
- O bip termina antes de o microfone abrir, para não ser ouvido como fala.
- Saiu o `time.sleep(0.5)` depois de cada comando.
- Para voltar à frase falada: `JARVIS_ACTIVATION_SOUND=voz` no `.env`.
- Testes automáticos passando; falta ouvir no PC.

### 2026-11-18 — Pendências do item 15

- O download do `gemma4:26b` parou em 92% em 17/11 (`logs/gemma4_download.log`) e o teste dele não rodou.
- O teste do Qwen em `logs/fase2_qwen.json` foi feito com o AION 2 aberto e `num_gpu: 32` (só parte do modelo na GPU): 2 a 3 tokens/s. Não serve para comparar.
- Próximo passo: com o jogo fechado, terminar o download e rodar `venv\Scripts\python.exe -X utf8 -m tests.benchmark_ollama` (os dois modelos, GPU inteira), que grava `logs/fase2_modelos.json`.

### 2026-11-18 — Modelo escolhido (item 15)

Teste com a GPU inteira, em `logs/fase2_modelos.json`:

| Caso | qwen3.8:27b | gemma4:26b |
| --- | --- | --- |
| Velocidade | 58 a 131 tokens/s | 173 a 334 tokens/s |
| Português | correto | correto |
| Cálculo (R$ 4,26) | errou (R$ 14,26) | acertou |
| Histórico | correto | correto |
| Código | correto | correto |
| Visão | correto | correto |
| Primeira carga | 11,8 s | 20,9 s |

- **Principal (conversa e visão):** `gemma4:26b`.
- **Reserva de código:** `qwen3.8:27b`, usada só quando o principal recusa. Os dois não cabem juntos nos 24 GB; quando a reserva é chamada, o Ollama troca os modelos (alguns segundos a mais nesse caso).
- Ressalva: são cinco perguntas, uma de cada tipo. Se o Gemma errar com frequência em uso real, dá para inverter no `.env` (`JARVIS_MODEL` e `JARVIS_MODEL_CODE`) sem mexer no código.
- `tests/benchmark_ollama.py` não grava mais o aviso fixo "AION 2 aberto"; use `--note` quando houver algo a registrar.

### 2026-11-18 — Travamento em "novidades sobre IA hoje"

Sintoma: notícias responderam em 1 s, mas a pergunta seguinte ficou mais de 90 s esperando o `gemma4:26b`.

- Hipótese: o caminho geral consultava o RAG, que carrega o modelo de embeddings no Ollama. Com o Stable Diffusion aberto ocupando a GPU, o Gemma (18 GB) não cabia mais inteiro e parte foi para a CPU. Mesmo sintoma do primeiro teste do Qwen (2 tokens/s). Confirmar com `ollama ps` durante a espera.
- **RAG desligado por padrão** (`JARVIS_RAG=0`) até a Fase 5: o índice só tem `teste.txt`.
- **Stable Diffusion não abre mais com o Jarvis** (`JARVIS_SD_AUTOSTART=0`); abre ao pedir uma imagem, com aviso de que leva cerca de um minuto.
- **Limite de 60 s** para respostas com busca web (`JARVIS_WEB_LLM_TIMEOUT`); depois disso ele avisa que não conseguiu responder.
- **"Novidades" e "últimas sobre"** vão para o caminho rápido de notícias (três manchetes da Brave e resumo curto).
- 33 testes de regressão passando; falta repetir o teste por voz.

### 2026-11-18 — Whisper na GPU confirmado (item 23)

- O `large-v3-turbo` não estava no cache: com o download automático desligado (`JARVIS_WHISPER_ALLOW_DOWNLOAD=0`), o Jarvis voltava para o `medium` na CPU (3 a 4 s por frase).
- Resolvido com `venv\Scripts\python.exe -X utf8 -m tests.prepare_whisper` (1,62 GB).
- Abertura confirmada no PC do Pedro: `Whisper large-v3-turbo na GPU` e `Interrupção: Whisper base na GPU`; Gemma pronto na abertura.
- O aviso de symlinks do Hugging Face no Windows é inofensivo (o cache só ocupa mais espaço).

### 2026-11-18 — Busca que não buscava, contexto perdido e Whisper lento na GPU

Sintomas: "procure sobre a nova versão do ChatGPT Astra 6.2" foi respondida da memória do modelo, que disse ter pesquisado; "procure pelas atualizações mais recentes" buscou notícias gerais em vez da OpenAI; transcrições de 15 a 18 s.

- **Busca explícita:** "procure", "pesquise", "busque", "consulte" sempre vão à internet (`is_explicit_search` em `jarvis_commands.py`), sem precisar de "na internet".
- **Contexto da conversa:** antes de buscar, `contextualize_search` (`brain/pipeline/super_jarvis.py`) usa as últimas três trocas para completar continuações ("as mais recentes" vira "atualizações mais recentes da OpenAI"). Custa uma chamada curta ao modelo (até 64 tokens, limite de 15 s) e só acontece quando há conversa. O console mostra `[BUSCA] Pergunta com o contexto da conversa: ...`.
- **Whisper lento na GPU:** hipótese de falta de memória de vídeo (Gemma ~19 GB, dois Whispers, Windows e avatar). Quando acaba, o driver da NVIDIA usa a RAM do PC e fica muito lento. Whisper principal em `int8_float16` (cerca de metade da memória, `JARVIS_WHISPER_COMPUTE`) e Whisper de interrupção na CPU (`JARVIS_INTERRUPT_GPU=0`). Confirmar com `nvidia-smi` com o Jarvis aberto.
- 37 testes de regressão passando; falta o teste por voz.

### 2026-11-18 — Resultado do teste por voz e data de hoje

- Confirmado por voz: transcrição de 0,41 a 0,46 s (antes 15 a 18 s), "procure..." pesquisa de verdade e a continuação foi reescrita como "atualizações mais recentes sobre o GPT-6.2 Astra da OpenAI". Respostas completas em 3 a 4 s.
- O modelo disse "lançou hoje, dia 17" no dia 18: ele não sabe a data. A resposta com busca passa a receber a data do dia (`today_line` em `super_jarvis.py`); o caminho de notícias já recebia.

### 2026-11-18 — Fala em fluxo (item 26)

- **Como funciona:** o modelo responde em stream (`llama_stream` em `brain/memory/memory.py`). `brain/speech_stream.py` corta o texto em frases, gera o áudio da próxima enquanto a atual toca (até duas à frente) e toca na ordem. A primeira frase sai assim que termina; as seguintes são agrupadas em ~90 caracteres para a fala não ficar picotada.
- **Onde vale:** perguntas comuns e respostas com busca na web. Pedidos de código, notícias, comandos e a API continuam com o texto pronto.
- **Falas comuns também:** `say()` usa a mesma fila, então qualquer fala longa começa pela primeira frase.
- **Interrupção:** "pare" encerra a fala, a síntese e a conexão com o modelo; áudios gerados e não tocados são apagados. O histórico guarda a resposta inteira gerada.
- **Console:** `[LLM] Primeiras palavras em X s` e `⏱️ Áudio gerado em X s` por frase.
- Para desligar: `JARVIS_STREAMING=0` no `.env`.
- 44 testes de regressão e 6 de fala em fluxo passando, com modelo e áudio simulados. Falta o teste por voz no PC.

### 2026-11-18 — Teste da fala em fluxo e busca mais rápida (item 35)

- Teste por voz da fala em fluxo: primeiras palavras do modelo em 0,4 a 0,5 s, primeira frase em áudio logo depois; as frases seguintes ficaram prontas antes da anterior acabar. "Pode parar. Já entendi" interrompeu.
- O Whisper pequeno da interrupção escreveu "pare" como "Pari." e foi ignorado: "pari" passou a contar como ordem de parar.
- O console mostrava "voltando à escuta" depois de cada frase; agora mostra "Frase concluída".
- **Busca:** antes lia 10 páginas com até 5 s cada (2,8 a 3,2 s no total). Agora usa os resumos que a Brave já devolve (chegam com os links) e lê só 4 páginas em paralelo, com prazo total de 2,5 s; as que passam do prazo ficam de fora. Consulta com `params=` (acentos e símbolos corretos) e User-Agent de navegador. Ajustes: `JARVIS_WEB_MAX_PAGES` e `JARVIS_WEB_FETCH_BUDGET`.
- 46 testes de regressão passando; falta medir por voz.

### 2026-11-18 — Busca medida por voz e roteador de busca (começo do item 32)

- Medido por voz: 4 páginas lidas em 1,3 s (antes cerca de 3 s); "procure uma build de PvP" começou a falar menos de 2 s depois da pergunta.
- Falha: "O que é esse apagão que estão falando...?" foi tratada como atemporal e respondida da memória ("não tenho informações concretas"). Não tinha "procure" nem palavras da lista de assuntos atuais.
- **Roteador:** quando as regras fixas dizem "atemporal", `needs_web` (`jarvis_commands.py`) pergunta ao modelo, com a data de hoje e as duas últimas trocas, se a resposta precisa da internet. Ele responde uma palavra (BUSCAR ou RESPONDER; até 4 tokens, limite de 8 s). Em falha, responde sem buscar. O console mostra `[ROTA] Modelo decidiu: ...`.
- Custo: uma chamada curta (cerca de 0,2 a 0,3 s com o Gemma) só nas perguntas que as regras não classificam como atuais. Para desligar: `JARVIS_WEB_ROUTER=0`.
- É o primeiro passo do item 32; a troca dos comandos por ferramentas continua pendente.
- 50 testes de regressão passando.

### 2026-11-18 — Voz local Kokoro (item 25)

- `brain/tts.py`: Kokoro (`kokoro-onnx`, ONNX Runtime na CPU) é o motor padrão; o Google TTS fica de reserva. Se o pacote faltar, o modelo não estiver baixado ou uma frase falhar, aquela fala sai pelo Google.
- Roda na CPU para não disputar a memória da placa com o Gemma. Carrega em segundo plano na abertura.
- Voz padrão `pm_alex` (masculina); também há `pm_santa` e `pf_dora`. Velocidade 1,1. Ajustes no `.env`: `JARVIS_TTS=kokoro|google`, `JARVIS_KOKORO_VOICE`, `JARVIS_KOKORO_SPEED`.
- O console mostra qual motor gerou cada frase: `⏱️ Áudio gerado em X s (N caracteres, Kokoro)`.
- Instalação: `venv\Scripts\python.exe -m pip install kokoro-onnx` e `venv\Scripts\python.exe -X utf8 -m tests.prepare_kokoro` (baixa cerca de 340 MB para `models/kokoro/`, fora do git, e grava `logs/kokoro_teste.wav` com as três vozes).
- 4 testes novos (`tests/test_tts_engine.py`) para a escolha do motor e a reserva.

### 2026-11-18 — Kokoro confirmado no PC e pausa entre a 1ª e a 2ª frase

- Abertura: `Voz local Kokoro pronta (pm_alex) em 0.7s`; todas as frases geradas pelo Kokoro, 0,23 a 0,56 s nas curtas e 1,48 s numa de 161 caracteres (CPU).
- A 1ª frase costuma ser curta ("Bom dia, Pedro.", ~1 s de áudio) e o 2º trecho tinha ~90+ caracteres: ele não ficava pronto a tempo e sobrava uma pausa. Agora o 2º trecho tem ~40 caracteres; a partir do 3º volta a ~90 (`iter_sentences` em `brain/speech_stream.py`).

### 2026-11-18 — Voz pm_santa e áudio direto pela placa de som (item 27)

- Voz padrão trocada para `pm_santa`, a pedido do Pedro.
- `brain/player.py`: o WAV do Kokoro toca direto pela placa de som (`sounddevice`), sem abrir um processo `ffplay` por frase. O player imita `poll`/`terminate`/`kill`/`wait` do `Popen`, então o monitor de interrupção não mudou.
- MP3 do Google (reserva) continua pelo `ffplay`. Se a placa de som der erro, o WAV também volta para o `ffplay`.
- Avatar: o volume do WAV é medido direto, sem `ffmpeg`, e o atraso da boca usa 40 ms para a placa de som e 180 ms para o `ffplay`.
- 7 testes novos (`tests/test_player.py`) com uma placa de som simulada. Falta ouvir no PC.

### 2026-11-18 — Comando engolido após interrupção; aprender só quando pedido

Sintoma: "Pesquise sobre a Bolsa de Valores" caiu no comando antigo de aprendizado, que perguntava "Deseja que eu memorize isso?". Pedro interrompeu (a pergunta foi descartada), mas o comando ficou esperando resposta, e "Faça a pesquisa sobre o caso do CEO da Nvidia" foi tomado como "não".

- `ask()` em `brain/audio.py`: se a pergunta foi descartada por interrupção, não espera resposta. Usado na análise de imagem, no registro do dia e no clima.
- `learn_from_web` (`commands/commands_memorie.py`) só aciona com pedido explícito ("pesquise sobre X e aprenda", "aprenda/estude/memorize sobre X") e guarda sem perguntar. "Pesquise sobre X" vai para a busca normal, com contexto, data e fala em fluxo.
- Primeira frase longa: o primeiro trecho é cortado na primeira vírgula depois de ~35 caracteres, para o áudio começar mais cedo (Kokoro na CPU leva ~1 s para 120 caracteres).
- Observado: "Interrupção lenta" voltou a aparecer. Hipótese: o Kokoro e o Whisper de interrupção disputam a CPU. A interrupção funcionou mesmo assim; acompanhar.
- 52 testes de regressão e 7 de fala em fluxo passando.

### 2026-11-18 — Microfone sempre aberto (item 24) e Fase 3 encerrada

- `brain/microphone.py`: um único stream do microfone fica aberto e entrega blocos de 30 ms a quem estiver inscrito (escuta normal ou monitor de interrupção). Antes cada escuta e cada fala abriam e fechavam o dispositivo, e o começo da fala logo depois de o Jarvis terminar podia se perder. Se o dispositivo para de mandar áudio por 2 s, é reaberto.
- A transcrição passou a ser feita direto da memória, sem gravar um WAV no disco.
- 5 testes novos (`tests/test_microphone.py`) com um microfone simulado. Falta o teste por voz.

**Item 30 descartado.** Com o Whisper turbo na GPU, transcrever cada fala no modo passivo custa ~0,4 s e já reconhece "Jarvis, que horas são?" numa frase só. O modelo pronto do openWakeWord é "hey jarvis": exigiria mudar o jeito de chamar o Jarvis e treinar um modelo próprio para "Jarvis" sozinho, além de mais uma dependência, para um ganho pequeno (menos processamento com o PC parado). Se o reconhecimento passivo der problema (ruído de TV, por exemplo), reavaliar.

**Fase 3 encerrada:** Whisper turbo na GPU (23), microfone aberto (24), voz local Kokoro (25), fala em fluxo (26), áudio pela placa de som (27), interrupção por voz (28), bip de ativação (29).
