import os
import requests
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_location():
    try:
        # Get location based on IP
        ip_info = requests.get("https://ipinfo.io/json").json()
        loc = ip_info.get("loc")  # Format comes as "lat,lon"

        if not loc:
            return "Não consegui obter suas coordenadas."

        lat, lon = loc.split(",")

        # Query Google API using the .env key
        geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GOOGLE_API_KEY}&language=pt-BR"
        response = requests.get(geo_url).json()

        if response["status"] == "OK":
            result = response["results"][0]
            address = result["formatted_address"]
            return f"📍 Você está em: {address}\n🌐 Coordenadas: {lat}, {lon}"
        else:
            return f"Erro ao obter localização via Google: {response['status']}"

    except Exception as e:
        return f"Erro ao obter localização via Google: {e}"
