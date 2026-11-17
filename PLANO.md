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
- [ ] 28. Interrupção por voz enquanto o Jarvis fala
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

## Extras pedidos durante o projeto

- [x] 48. Avatar holográfico 3D que fala (`brain/avatar/`, `commands/commands_avatar.py`)

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
