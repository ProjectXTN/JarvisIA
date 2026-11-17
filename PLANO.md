# Plano de refatoração do Jarvis (2026)

Acompanhamento do trabalho no branch `refactor-2026`.
`[x]` = feito · `[ ]` = pendente. A coluna "Onde" indica os arquivos alterados.

Última atualização: 2026-11-17

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

- [ ] 15. Baixar `qwen3.8:27b` e `gemma4:26b`, comparar em português e escolher
- [ ] 16. Remover `llama3.2`, `llama3.3`, `codestral`, `llava`, `llama3.2-vision:90b`
- [ ] 17. Reescrever `llama_query` para `/api/chat` (system, histórico, `options`, `keep_alive`, `think: false`)
- [ ] 18. Unificar os prompts de sistema num "Jarvis de voz"
- [ ] 19. Ligar o histórico de conversa no fluxo de voz
- [x] 20. Trocar `start_llava()` por um aquecimento HTTP do modelo escolhido (feito para o modelo atual; trocar o nome quando o novo for escolhido)
- [ ] 21. Visão: enviar imagem em base64 pelo `/api/chat`
- [ ] 22. Modelo reserva de código quando o principal recusar

## Fase 3 — Velocidade e naturalidade da voz

- [ ] 23. Whisper `large-v3-turbo`, `beam_size=1`, áudio em memória
- [ ] 24. Manter o microfone aberto entre escutas
- [ ] 25. TTS local com Kokoro (`brain/tts.py`), Google TTS como reserva
- [ ] 26. Streaming LLM → TTS frase a frase
- [ ] 27. Tocar áudio com `sounddevice`, sem `ffplay`
- [x] 28. Interrupção por voz enquanto o Jarvis fala (só com ordem de parar; perguntas não interrompem)
- [ ] 29. Bip local no lugar de "Jarvis Ativado..." e remover `sleep(0.5)`
- [ ] 30. Hotword dedicada com `openWakeWord`

## Fase 4 — Inteligência: ferramentas no lugar de regex

- [ ] 31. Transformar cada comando em ferramenta com descrição
- [ ] 32. Roteamento por tool calling em `process_command`
- [ ] 33. Atalhos sem LLM para música, volume e desligar
- [ ] 34. Comandos encadeados via múltiplas ferramentas; apagar `commands_multiples.py`
- [ ] 35. Busca web: `params=`, `User-Agent`, 3 páginas, resumos do Brave
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
