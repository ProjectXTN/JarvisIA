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

- [x] 31. Transformar cada comando em ferramenta com descrição (`brain/tools.py`, 24 ferramentas)
- [x] 32. Roteamento por tool calling em `process_command` (`brain/tool_router.py`)
- [x] 33. Atalhos sem LLM: desligar, hora, data, controle de música, avatar (volume ainda não existe)
- [x] 34. Comandos encadeados via múltiplas ferramentas; apagar `commands_multiples.py`
- [x] 35. Busca web: `params=`, `User-Agent`, 4 páginas com prazo de 2,5 s, resumos da Brave
- [x] 36. Cache com validade e limite de tamanho (API do site: 10 min, 200 respostas)

## Fase 5 — Memória e RAG

- [x] 37. RAG: carregar o índice uma vez e usar `as_retriever()` (llama-index trocado por índice próprio em SQLite, atualizado só quando o arquivo muda)
- [x] 38. Trocar o modelo de embeddings e reindexar (`qwen3-embedding:0.6b`, multilíngue; Pedro precisa rodar `ollama pull qwen3-embedding:0.6b`)
- [x] 39. Memória de longo prazo com busca por semelhança (base pronta; a extração automática das conversas fica no item 53)
- [x] 40. `auto_learning`: resumir antes de salvar, rejeitar erros, limitar ciclos (substituído pelo estudo autônomo, item 56)
- [x] 41. Resumo automático da conversa ao encerrar (substituído pelo perfil e pelo diário, itens 53 e 54)

## Fase 6 — Imagem, API e acabamento

- [x] 42. Stable Diffusion sob demanda, alternando VRAM com o LLM (feito com o FLUX, item 51)
- [x] 43. `server.py`: token obrigatório, `hmac.compare_digest`, sem global, sem `lower()`
- [x] 44. Servir a API com `waitress` e restringir o CORS
- [x] 45. `logging` com níveis e medição de tempo por etapa
- [x] 46. Testes automáticos (desligamento, hotword, roteamento)
- [x] 47. Atualizar `README.md`, `Dockerfile` e `build_jarvis.bat` (build e Docker ainda não testados)

## Fase 7 — Jarvis vivo: personalidade, memória e aprendizado autônomo

Depende da Fase 2 (modelo novo com ferramentas). Substitui os itens 39 a 41 da Fase 5.

- [x] 52. Personalidade própria em `brain/persona/`: traços fixos, humor do dia e opiniões que ele forma e guarda
- [x] 53. Memória de longo prazo sobre o Pedro: fatos, preferências e projetos extraídos das conversas, com busca por semelhança
- [x] 54. Diário: ao fim de cada dia, resumo do que conversaram e do que aprendeu, lido na próxima inicialização
- [x] 55. Curiosidade: lista de temas a estudar, alimentada pelas conversas e pelos interesses do Pedro
- [x] 56. Estudo autônomo quando o PC está ocioso: busca, lê, resume, confere em mais de uma fonte e guarda com a fonte
- [x] 57. Reflexão noturna: revisa o que aprendeu, junta notas repetidas, marca contradições e atualiza opiniões
- [x] 58. Iniciativa: puxa assunto sobre o que aprendeu, lembra compromissos, comenta novidades dos temas do Pedro
- [x] 59. Painel "o que o Jarvis sabe": ver, corrigir e apagar memórias e aprendizados
- [x] 60. Limites de segurança: internet só para leitura, nada de executar, comprar ou enviar sem permissão
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
- [x] 51. Novo gerador de imagens: ComfyUI com FLUX.2 [klein] 4B no lugar do Stable Diffusion 1.5 (código pronto; falta Pedro instalar o ComfyUI e baixar os modelos)

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

### 2026-11-18 — Fase 4: o modelo escolhe as ferramentas (itens 31 a 34 e 36)

Confirmado antes: o `gemma4:26b` tem a capacidade "tools" no Ollama.

- **Fluxo de uma fala** (`process_command`):
  1. Desligar e **atalhos sem modelo** (`SHORTCUT_HANDLERS`): hora, data, pausar/próxima/anterior música, mostrar/esconder avatar.
  2. **Roteador** (`brain/tool_router.py`): uma chamada ao Gemma com a conversa, a data e as 20 ferramentas, em stream. Resposta em texto já vai sendo falada.
  3. Ferramentas pedidas rodam na ordem ("abra o Steam e toque Queen" = duas chamadas). Ferramentas de **informação** (busca, notícias, clima, data, status do PC, memória, emoções) voltam para o Gemma numa segunda chamada, sem ferramentas, que formula a resposta falada. Ferramentas de **ação** (programa, pasta, música, imagem, memorizar, avatar...) executam e confirmam sozinhas.
  4. Se o Ollama recusar ferramentas ou der erro antes de começar (`RouterUnavailable`), usa o **caminho antigo** de regras de palavras, que continua no código.
- **Ferramentas** (`brain/tools.py`): buscar_na_internet, buscar_noticias, previsao_do_tempo, data_e_hora, status_do_computador, consultar_memoria, listar_memorias, consultar_emocoes, abrir_programa, abrir_pasta, musica, criar_imagem, descrever_imagem, memorizar, esquecer, aprender_da_internet, registrar_emocao, registrar_meu_dia, traduzir_legenda, avatar. Reaproveitam as funções dos comandos antigos.
- Se Pedro disser "pare" durante a parte inicial falada, as ferramentas pedidas não rodam.
- `commands_multiples.py` apagado (item 34). O gatilho dele ("comando_multiplo") nunca aparecia em frase nenhuma.
- **Cache da API (item 36):** validade de 10 min e no máximo 200 respostas.
- Para desligar o roteador: `JARVIS_TOOL_ROUTER=0` no `.env`.
- 13 testes novos (`tests/test_tool_router.py`) com respostas simuladas do Ollama; testes antigos que chamam `process_command` passaram a desligar o roteador para não chamar o modelo de verdade. Falta o teste por voz.
- Pendências: não existe comando de volume; "registrar_meu_dia" e "traduzir_legenda" ainda usam as funções antigas, sem teste com o modelo.

### 2026-11-18 — Teste por voz da Fase 4

Funcionou: fotossíntese respondida direto; "o que é esse apagão que estão falando" chamou `buscar_noticias`; "vai chover amanhã" chamou `previsao_do_tempo(periodo='amanha')`; Steam, Queen e Chrome com a ferramenta certa; memorizar, consultar e esquecer a impressora; "Já entendi" interrompeu. Transcrições de 0,1 a 0,4 s.

Corrigido:
- O primeiro trecho cortado na vírgula terminava com ponto ("...pelo qual plantas.") e a voz fazia entonação de fim de frase. Agora termina com vírgula.
- "Abra o site do YouTube": não havia ferramenta para sites, e o modelo disse "eu abri o navegador para você" sem ter chamado nada. Nova ferramenta `abrir_site` (só http/https; para buscar dentro de um site, o modelo monta a URL de busca).
- O log "Primeiras palavras em 0.0s" media a partir da resposta HTTP. Agora mede desde o pedido, e mostra também "Ferramentas escolhidas em X s".

### 2026-11-18 — YouTube

- Confirmado por voz: "abre o site do YouTube", "procure vídeos do Queen no YouTube" e "quero ouvir Bohemian Rhapsody no YouTube" chamaram `abrir_site`, com a busca montada pelo modelo (ferramentas escolhidas em 0,3 a 0,5 s).
- "Selecione o vídeo" não era possível, e o modelo disse isso em vez de fingir. Nova ferramenta `tocar_no_youtube`: lê a página de resultados, pega o primeiro vídeo e abre a página dele (o vídeo começa a tocar). Na Europa o YouTube pede consentimento; os cookies de consentimento vão junto. Se não achar o vídeo, abre a busca.
- `abrir_site` diz "Abrindo a busca em youtube.com" quando o endereço é uma busca.

### 2026-11-18 — Janela de mídia: um vídeo por vez

- Confirmado por voz: "quero ouvir Bohemian Rhapsody no YouTube" e "quero ouvir Empty Machines do Linkin Park" chamaram `tocar_no_youtube` e tocaram. Problema: cada pedido abria uma aba nova.
- `brain/media_window.py`: o Jarvis abre o próprio Chrome (Edge só sem Chrome) com perfil separado (`data/browser-media/`, fora do git) e controle remoto só em 127.0.0.1 (porta 9223, `JARVIS_MEDIA_PORT`). No primeiro pedido abre a janela com o vídeo; nos seguintes, abre o vídeo novo e fecha o anterior. Reprodução automática ligada nessa janela.
- Perfil separado: o YouTube começa deslogado; entrar na conta uma vez nessa janela fica lembrado.
- Se não houver Edge/Chrome ou o controle falhar, abre no navegador padrão, como antes.
- 4 testes novos (`tests/test_media_window.py`). Falta testar no PC.
- A pedido do Pedro, as janelas do Jarvis (mídia e avatar) usam o Chrome; o Edge só entra se o Chrome não estiver instalado (`_browser_for_app_window`).

### 2026-11-18 — Pesquisa visível no Chrome

- Pedro quer VER a pesquisa quando pede "abra o Chrome e pesquise X". Antes o modelo abria o navegador vazio e fazia a busca por dentro (`buscar_na_internet`), só respondendo em voz.
- Nova ferramenta `pesquisar_no_google`: abre a página de resultados do Google no Chrome de Pedro (perfil normal, nova aba). As descrições separam as duas: ver a pesquisa (`pesquisar_no_google`) e ouvir a resposta (`buscar_na_internet`).
- `abrir_site`, abrir o navegador e a pesquisa usam o Chrome (`open_in_chrome` em `brain/system.py`); Edge só sem Chrome; navegador padrão como último recurso.
- Se na mesma frase houver pesquisa, site ou vídeo, o roteador ignora o "abrir navegador" (evita uma janela vazia a mais).

### 2026-11-18 — Abrir a página de onde veio a resposta

- `search_web` e `buscar_noticias` guardam as páginas usadas na última busca (`LAST_SOURCES` em `brain/websearch/websearch.py`: endereço, site e título).
- `buscar_na_internet` entrega ao modelo as fontes numeradas e pede que ele cite o site na resposta.
- Nova ferramenta `abrir_fonte`: abre no Chrome a fonte principal, a de um número ("a segunda"), a de um site citado ("a da Fextralife") ou todas (até 4). Sem busca anterior, avisa.

### 2026-11-18 — Fase 5: memória por semelhança e documentos

- Novo `brain/semantic_memory.py`: tabela `memorias` no mesmo banco (`brain/learning/memoria_jarvis.db`) com o vetor de significado de cada lembrança, gerado no Ollama (`/api/embed`). A busca acha por semelhança: "qual o modelo da minha impressora?" encontra o que foi guardado como "minha impressora". Sem o modelo de embeddings, cai para comparação de palavras.
- Tipos: `fato` (o que Pedro mandou lembrar), `aprendido` (o que Jarvis pesquisou e guardou) e `documento` (trechos dos arquivos).
- Modelo de embeddings: `qwen3-embedding:0.6b` (multilíngue, ~640 MB, roda junto do gemma4:26b). Trocável por `JARVIS_EMBEDDING_MODEL`. Ao trocar de modelo, as lembranças antigas ficam sem vetor válido e a busca usa palavras até reindexar.
- Na abertura (em segundo plano): importa uma vez as 113 memórias da tabela antiga `conhecimento`, pulando o lixo do estudo automático antigo (mensagens de erro e textos curtos), e atualiza o índice da pasta de documentos.
- Documentos: `.txt`, `.md` e `.pdf` em `brain/data_jarvis/` (ou `JARVIS_DOCS_DIR`). Divididos em trechos de ~900 caracteres; só reprocessa arquivo que mudou e tira do índice arquivo apagado. O llama-index saiu do caminho (acabou o aviso "Using MockLLM" na abertura).
- Ferramentas: `memorizar`, `consultar_memoria`, `esquecer` e `listar_memorias` usam a memória nova; nova `consultar_documentos`. Os comandos antigos ("aprenda que...", "o que você sabe sobre...", "esqueça...", "aprenda sobre X") também.
- Testes: `tests/test_semantic_memory.py` (7).
- Para usar: `ollama pull qwen3-embedding:0.6b` e colocar arquivos em `brain/data_jarvis/`. Teste por voz: "guarde que a senha do wifi é ...", depois "qual é a senha da internet?"; "o que diz o meu documento sobre ...?".
- Faltam na Fase 5: 40 e 41 (cobertos pelos itens 53–56 da Fase 7).

### 2026-11-18 — Correção: Jarvis travava depois da Fase 5

- Causa provável: o modelo de embeddings era carregado na GPU ao indexar os documentos na abertura, e o Ollama tirava o gemma4:26b da VRAM; a pergunta seguinte ficava esperando o modelo grande recarregar.
- Embeddings agora rodam na CPU (`num_gpu: 0`, contexto 2048). Para voltar à GPU: `JARVIS_EMBEDDING_GPU=1`.
- `open_chat` avisa quando o Ollama demora mais de 3 s para começar a responder.
- Migração das memórias antigas agora é marcada na tabela `memorias_info` (antes, 3 linhas gravadas por um teste fizeram ela achar que já tinha rodado; linhas removidas).

### 2026-11-18 — Teste por voz da Fase 5 e ajustes

- Validado por voz: "guarde que a senha do wifi é teste 123" → "qual é a senha da internet?" respondeu certo (busca por semelhança). 110 memórias antigas importadas, 3 puladas.
- Documentos: o índice roda antes da importação das memórias antigas (antes, um arquivo novo só entrava depois de importar tudo). Aceita várias pastas em `JARVIS_DOCS_DIR`, separadas por `;`; ignora formatos que não sejam .txt, .md e .pdf.
- `should_save_to_file` (`brain/storage/file_saver.py`): só salva resposta em arquivo quando Pedro pede ("salve em um arquivo", "crie um documento..."). Antes qualquer frase com "documento", "receita" ou "escreva" virava um .txt em Documentos.
- Embeddings na CPU levam ~1 s por consulta; fica de olho se isso pesar na resposta.

### 2026-11-18 — Fase 6: API segura (itens 43 e 44)

- `server.py` reescrito. Antes: sem `SECRET_TOKEN_JARVIS` no .env, o cabeçalho `Bearer None` era aceito; escutava em 0.0.0.0 com CORS aberto para qualquer site; um pedido da API ligava o modo API global e o Jarvis de voz parava de falar enquanto isso; o texto das exceções voltava para quem chamou.
- Agora: token obrigatório (mínimo 16 caracteres; sem ele o servidor não abre e sugere um), comparado com `hmac.compare_digest`; escuta só em 127.0.0.1 (`JARVIS_API_HOST` para abrir na rede); CORS só para as origens de `JARVIS_API_ORIGINS`; pergunta validada (texto, até 2000 caracteres, idioma pt/en, corpo até 16 KB); um pedido por vez (429 se ficar ocupado 90 s); erro interno vai para o log e a resposta diz só "Erro interno"; 401 para token errado.
- `core/config.py`: `IS_API_REQUEST` vale só para a thread do pedido (`with config.api_request():`). Os módulos que leem `config.IS_API_REQUEST` não mudaram.
- Serve com `waitress` (adicionado ao requirements.txt); sem ele, cai para o servidor do Flask com aviso.
- Testes: `tests/test_server.py` (5).

### 2026-11-18 — Fase 6: imagens com ComfyUI + FLUX.2 [klein] 4B (itens 42 e 51)

- Novo `brain/image_gen.py`: monta o grafo do ComfyUI (formato API) igual ao modelo oficial de texto para imagem do klein 4B destilado: UNETLoader, CLIPLoader (`qwen_3_4b`, tipo `flux2`), VAELoader, CLIPTextEncode, ConditioningZeroOut, CFGGuider (cfg 1), KSamplerSelect (euler), Flux2Scheduler (4 passos), RandomNoise, EmptyFlux2LatentImage, SamplerCustomAdvanced, VAEDecode, SaveImage.
- VRAM: antes de gerar, tira o gemma4:26b da placa (`keep_alive: 0`); depois pede `/free` ao ComfyUI e recarrega o gemma4 em segundo plano. Também em caso de erro.
- Abre o ComfyUI sozinho se não estiver aberto (`JARVIS_COMFYUI_DIR`, padrão `C:\ComfyUI`, versão portátil ou com venv), só em 127.0.0.1:8188. Escolhe o arquivo klein 4B que existir na pasta.
- Ferramenta `criar_imagem`: o modelo de conversa já escreve o prompt em inglês detalhado (`prompt_em_ingles`) e escolhe o formato (quadrada 1024², retrato 832×1216, paisagem 1216×832). A imagem é salva em `Imagens\Jarvis` e aberta.
- `JARVIS_IMAGE_ENGINE=sd` volta ao Stable Diffusion antigo.
- `tests/prepare_flux.py` baixa os 3 arquivos (modelo fp8, codificador de texto, VAE) para a pasta models do ComfyUI.
- Testes: `tests/test_image_gen.py` (4).

### 2026-11-24 — Correção: Jarvis travava logo depois de ligar o PC

- Causa: com o PC recém-ligado, o Ollama abre frio e o gemma4:26b leva um tempo para sair do disco. O Ollama carrega um modelo por vez, então os embeddings da abertura e o primeiro comando ficavam na fila; os embeddings estouravam 30 s e o comando esperava junto.
- `core/config.py`: `MODEL_READY`, ligado quando o pré-carregamento do gemma4 termina (ou falha).
- `process_command`: se o modelo ainda está carregando, Jarvis diz "Ainda estou carregando, só um instante" e espera (até 4 min) em vez de parecer travado.
- `semantic_memory.prepare` espera o modelo carregar antes de mexer nos embeddings, e `backfill_vectors` gera os vetores que ficaram faltando (o `teste jarvis.txt` tinha sido indexado sem vetor).
- Caminho antigo de imagem (quando o roteador falha) também usa o FLUX.

### 2026-11-24 — Fase 6 concluída: registro, testes e documentação (itens 45 a 47)

- Validado por voz: imagem do lobo gerada pelo FLUX no ComfyUI.
- Novo `core/log.py`: tudo que aparece na janela também vai para `logs/jarvis.log` com data, hora e nível (o nível sai do conteúdo da linha: [DEBUG], erro/falhou, aviso/indisponível). Arquivo gira a cada 5 MB e guarda 5. `JARVIS_CONSOLE_LEVEL=INFO` esconde o [DEBUG] da janela; o arquivo guarda tudo. Erros inesperados vão com o traceback.
- Tempos: cada pedido de voz (`[TEMPO] pedido: Xs` na janela), cada ferramenta e cada imagem ficam em `logs/tempos.csv` (abre no Excel), para ver onde o Jarvis perde tempo.
- Testes: novo `tests/run_all.py` roda as 17 suítes de uma vez (155 testes aqui; o do Whisper precisa do venv do Windows). Novo `tests/test_ferramentas.py` confere os esquemas das 25 ferramentas. Desligamento, palavra de ativação e roteamento já tinham testes em `test_regressao.py` e `test_tool_router.py`.
- `README.md` reescrito com o estado atual (modelos, ferramentas, memória, imagens, API, logs, testes, estrutura).
- `build_jarvis.bat`: PyInstaller em pasta (`--onedir`) com faster-whisper, ctranslate2, kokoro e as DLLs da NVIDIA; tirou os arquivos do Whisper antigo e o `utils_datetime.py` que não existe mais. Ainda não testado.
- `Dockerfile` e `docker-compose.yml`: só a API de texto, com o Ollama no Windows (`host.docker.internal`). O Jarvis de voz roda no venv. Ainda não testado.
- `server.py` estava no `.gitignore` e nunca tinha ido para o git; agora vai (não guarda segredo, o token vem do .env).
- Próximo: Fase 7 (Jarvis vivo). Pendente do Pedro: item 16 (`ollama rm` dos modelos antigos).

### 2026-11-24 — Fase 7, parte 1: personalidade, perfil do Pedro, diário e limites (itens 52, 53, 54, 60)

- `brain/persona/persona.json`: traços fixos, princípios e os humores possíveis. Editável à mão.
- `brain/persona/core.py`: monta o bloco que entra no começo de toda conversa (roteador e caminho antigo): traços, humor do dia, até 15 fatos sobre o Pedro, o diário de ontem e as opiniões formadas. Fica 5 min em cache e não usa embeddings, então não atrasa a resposta. Humor do dia: sorteado uma vez por dia, com o diário de ontem puxando (estudou → curioso; projeto → focado; brincadeira → brincalhão).
- `brain/persona/perfil.py`: cada troca da conversa por voz vai para a tabela `turnos`. Quando o Jarvis volta ao modo passivo (2 min sem fala) e na abertura, o gemma4 lê os turnos novos e devolve em JSON até 5 fatos duradouros sobre o Pedro (preferência, projeto, pessoa, rotina, fato). Viram lembranças tipo `perfil`; um fato quase igual (semelhança ≥ 0,88) substitui o antigo. Se o Ollama falhar, os turnos ficam para a próxima.
- `brain/persona/diario.py`: na abertura e no modo passivo, escreve o diário (3 a 5 frases, primeira pessoa) de cada dia passado que teve conversa e ainda não tem diário (até 3 dias).
- `brain/persona/limites.py`: o que o Jarvis fizer sozinho só pode ler: lista fechada de ferramentas de leitura (busca, notícias, clima, memória, documentos) e bloqueio de endereços locais, rede de casa e bancos. Será usado pelo estudo autônomo e pela iniciativa.
- `consultar_memoria` e `listar_memorias` também enxergam os fatos do perfil.
- Testes nunca mais escrevem no banco de verdade: `JARVIS_MEMORY_DB` aponta para um banco temporário em `tests/test_regressao.py`.
- Testes: `tests/test_persona.py` (10). Total no `run_all`: 165.

### 2026-11-24 — Fase 7, parte 2: curiosidade, estudo autônomo e reflexão (itens 55, 56, 57)

- `brain/persona/curiosidade.py`: fila de temas (tabela `curiosidades`), sem repetir. Entra tema por três caminhos: a leitura da conversa devolve até 3 temas junto com os fatos do Pedro; pedido do Pedro tem prioridade; com a fila vazia, o gemma4 sugere temas ligados aos fatos do perfil.
- `brain/persona/estudo.py`: pega o próximo tema, busca na internet só para leitura (sem rede local, bancos ou endereços que não sejam http/https, `limites.check_url`) e sem trocar as fontes do "abrir a fonte" do Pedro (`search_web(remember=False)`). O gemma4 resume usando só o texto das páginas, diz quais fontes concordam e onde divergem; confiança "alta" só com duas fontes diferentes concordando. Guarda como `aprendido` com as fontes e a confiança (atualiza se já houver nota igual) e anota em `logs/aprendizados_DATA.txt`.
- `brain/persona/reflexao.py`: uma vez por dia junta notas aprendidas quase iguais (semelhança ≥ 0,93), procura contradições entre notas parecidas (0,75 a 0,93; tabela `contradicoes`) e forma ou atualiza até 2 opiniões (tabela `opinioes`, que já entra na personalidade). Não opina sobre política nem pessoas.
- `brain/persona/rotina.py`: a cada minuto, se a autonomia está ligada, o Jarvis não atende há `JARVIS_IDLE_MINUTES` (10) e ninguém mexe em teclado e mouse há esse tempo (`GetLastInputInfo`, então não pesa na placa enquanto o Pedro joga), faz UM passo: ler conversa → diários → reflexão (uma vez por dia, depois de `JARVIS_REFLECT_HOUR`, 22h) → estudar um tema (até `JARVIS_STUDY_PER_DAY`, 8). Falha de Ollama ou internet: espera 10 min.
- O antigo `auto_learning` (temas aleatórios sem fonte, gravava até mensagens de erro) saiu do `jarvis.py`. "Comece a estudar" / "pare de estudar" agora ligam e desligam a rotina. `JARVIS_AUTONOMY=0` desliga de vez.
- Cada pedido marca atividade (`config.LAST_ACTIVITY`); a rotina espera o Pedro parar.
- Testes: `tests/test_autonomia.py` (10). Total: 175.

### 2026-11-24 — Fase 7, parte 3: iniciativa e painel (itens 58 e 59)

- `brain/persona/iniciativa.py` + ferramentas `lembrar_compromisso`, `listar_compromissos`, `cancelar_compromisso`: "me lembra amanhã às 15h de ligar para o banco" vira um compromisso (o roteador agora recebe a hora atual). A rotina confere a cada minuto, mesmo com a autonomia desligada, e avisa por voz na hora ("Pedro, lembrete: ..."), esperando terminar se estiver atendendo um pedido (`config.NOT_BUSY`). Atraso máximo de 12 h (PC desligado na hora); avisa uma vez só.
- Ao abrir: depois do bom-dia, fala os compromissos do dia e puxa UM assunto do que estudou sozinho e ainda não contou ("Enquanto você estava fora, estudei sobre X. Quer que eu conte?"). A frase entra no histórico, então "sim, conta" funciona.
- Painel em `http://127.0.0.1:11600/painel` (rodar `server.py`): abas Sobre você, Pediu para guardar, Aprendido, Opiniões, Quer estudar, Diário, Compromissos, Contradições e Documentos, com filtro, Corrigir e Apagar. Entra com o `SECRET_TOKEN_JARVIS` (fica só na aba do navegador). Só campos permitidos são editáveis (`brain/persona/painel.py`).
- Testes: `tests/test_iniciativa.py` (7). Total: 182.
- Fase 7 concluída, menos o item 61 (ajuste fino LoRA, opcional): fica para depois de algumas semanas de conversas guardadas.

### 2026-11-24 — Janela para escrever ao Jarvis (pedido do Pedro)

- "Jarvis, abre o chat" (também "abre a janela de texto", "quero te escrever", "prefiro digitar", "abre um lugar pra escrever") abre uma janela própria no Chrome em modo app (`brain/chat_window.py` + `interface/chat.html`, porta `JARVIS_CHAT_PORT`, 8766).
- O texto escrito passa pelo mesmo caminho da voz (`process_command`): ferramentas, memória, perfil, tudo igual. A janela mostra a conversa inteira, inclusive o que foi dito por voz. Enter envia, Shift+Enter pula linha.
- "Responder só por escrito": a resposta aparece na janela sem falar (`audio.text_only`, vale só para a thread do pedido escrito).
- Voz e texto não atendem ao mesmo tempo (`_command_lock` em `process_command`). Escrever desfaz um "pare" anterior.
- Segurança: só 127.0.0.1; cada abertura do Jarvis gera uma chave nova que vai no endereço da janela; pedido sem a chave (de outro site no navegador) recebe 403.
- Testes: `tests/test_chat_window.py` (6). Total: 188.

### 2026-11-24 — Correção: voz de live/vídeo virava comando (e um "tchau" da live desligou o Jarvis)

- Causa: depois de um comando, por 2 minutos qualquer fala ouvida era tratada como comando, sem precisar de "Jarvis". O microfone pegava a voz da live que o Pedro assistia ("Obrigado, Lexy, Adriano", "Tchau").
- Novo `brain/followup.py` (`accept_followup`): sem dizer "Jarvis", uma frase só vale até `JARVIS_FOLLOWUP_SECONDS` (20 s) depois do FIM da última resposta, e só se nenhum outro programa estiver tocando som. Fora disso é ignorada (aparece no log como `[DEBUG] Ignorado`).
- Novo `brain/system_audio.py`: mede o pico das sessões de áudio do Windows (pycaw), sem contar o próprio Jarvis. Com som tocando (Chrome com a live, música, jogo), toda frase precisa de "Jarvis". Precisa de `pip install pycaw` (adicionado ao requirements); sem ele, vale só a janela de 20 s.
- Despedida ("tchau", "desligar") sem "Jarvis" no modo conversa é ignorada; "tchau, Jarvis" desliga.
- Testes: `tests/test_followup.py` (5).

### 2026-11-24 — Stable Diffusion removido do código

- O gerador antigo saiu do Jarvis: `modules/stable_diffusion_controller.py`, abrir/fechar o webui em `core/initializer.py` e `commands/commands_systeme.py`, `JARVIS_SD_AUTOSTART` e `JARVIS_IMAGE_ENGINE`. Imagem agora é só ComfyUI + FLUX (o caminho antigo de comandos também chama `criar_imagem`).
