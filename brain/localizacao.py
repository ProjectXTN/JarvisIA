import os
import requests
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def obter_localizacao():
    try:
        # Pega a localização baseada no IP
        ip_info = requests.get("https://ipinfo.io/json").json()
        loc = ip_info.get("loc")  # Vem no formato "lat,lon"

        if not loc:
            return "Não consegui obter suas coordenadas."

        lat, lon = loc.split(",")

        # Consulta na API do Google com a chave do .env
        geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GOOGLE_API_KEY}&language=pt-BR"
        resposta = requests.get(geo_url).json()

        if resposta["status"] == "OK":
            resultado = resposta["results"][0]
            endereco = resultado["formatted_address"]
            return f"📍 Você está em: {endereco}\n🌐 Coordenadas: {lat}, {lon}"
        else:
            return f"Erro ao obter localização via Google: {resposta['status']}"

    except Exception as e:
        return f"Erro ao obter localização via Google: {e}"
