#!/bin/bash

echo "🔍 Detectando IP do Windows no WSL..."
WINDOWS_IP=$(ip route | grep default | awk '{print $3}')
OLLAMA_HOST_URL="http://$WINDOWS_IP:11434"

echo "🌐 Testando conexão com Ollama em $OLLAMA_HOST_URL ..."
RESPONSE=$(curl -s --max-time 3 "$OLLAMA_HOST_URL/api/tags")

if [[ "$RESPONSE" == *"models"* ]]; then
    echo "✅ Conexão com Ollama bem-sucedida!"
    echo "🔧 Definindo variável OLLAMA_HOST..."

    export OLLAMA_HOST=$OLLAMA_HOST_URL

    if grep -q "OLLAMA_HOST" ~/.bashrc; then
        echo "🧹 Limpando entrada antiga no .bashrc..."
        sed -i '/OLLAMA_HOST/d' ~/.bashrc
    fi

    echo "💾 Salvando no ~/.bashrc ..."
    echo "export OLLAMA_HOST=$OLLAMA_HOST_URL" >> ~/.bashrc

    echo "✅ Configuração finalizada com sucesso!"
    echo "💡 Use agora: source ~/.bashrc"
    echo "🚀 Pronto pra rodar: python jarvis.py"

else
    echo "❌ Falha na conexão com Ollama."
    echo "📛 Verifique se o Ollama está rodando no Windows com o portproxy ativo."
    echo "💬 Dica: execute no PowerShell como admin:"
    echo '  netsh interface portproxy add v4tov4 listenport=11434 listenaddress=0.0.0.0 connectport=11434 connectaddress=127.0.0.1'
    echo '  netsh advfirewall firewall add rule name="Allow Ollama WSL" dir=in action=allow protocol=TCP localport=11434'
fi
