import requests
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from brain.audio import say, listen

# Carrega as variáveis do .env
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def get_weather(city="Lexy", forecast=False, next_week=False):
    if not OPENWEATHER_API_KEY:
        return "API KEY do serviço de previsão do tempo não configurada."

    try:
        if forecast:
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&lang=pt_br&units=metric"
        else:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&lang=pt_br&units=metric"

        response = requests.get(url)
        data = response.json()

        if data.get("cod") not in (200, "200"):
            return "Não consegui obter a previsão do tempo agora."

        if forecast:
            # 📅 Modo de previsão para os próximos dias ou para a próxima semana
            forecast_texts = []
            for entry in data["list"]:
                date_str = entry["dt_txt"].split(" ")[0]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_of_week = date_obj.strftime("%A")
                day_of_week_ptbr = traduzir_dia_semana(day_of_week)

                formatted_date = date_obj.strftime("%d-%m")
                weather = entry["weather"][0]["description"]
                temp = entry["main"]["temp"]

                forecast_texts.append(
                    (
                        date_obj,
                        f"{day_of_week_ptbr} {formatted_date}: {weather}, {temp:.0f}°C",
                    )
                )

            # 🧠 Aqui filtramos o que interessa
            unique_days = []
            final_forecast = []

            for date_obj, line in forecast_texts:
                # Se for pedido "semana que vem", pula até segunda-feira da próxima semana
                if next_week:
                    today = datetime.now()
                    start_next_monday = today + timedelta(days=(7 - today.weekday()))
                    if date_obj.date() < start_next_monday.date():
                        continue

                day = line.split()[1]
                if day not in unique_days:
                    unique_days.append(day)
                    final_forecast.append(line)
                if len(final_forecast) >= 5:
                    break

            return f"Previsão do tempo para {city} nos próximos dias:\n" + "\n".join(
                final_forecast
            )

        else:
            # ☀️ Modo previsão normal (atual)
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            return (
                f"Em {city}, o clima está {weather} com temperatura de {temp:.0f}°C, "
                f"sensação térmica de {feels_like:.0f}°C, umidade de {humidity}% "
                f"e ventos a {wind_speed:.0f} km/h."
            )

    except Exception as e:
        print(f"[ERRO] Falha ao buscar previsão do tempo: {e}")
        return "Ocorreu um erro ao tentar buscar a previsão."


def traduzir_dia_semana(day_en):
    """Traduz dias da semana do inglês para português."""
    dias = {
        "Monday": "Segunda",
        "Tuesday": "Terça",
        "Wednesday": "Quarta",
        "Thursday": "Quinta",
        "Friday": "Sexta",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
    }
    return dias.get(day_en, day_en)


def is_weather_request(query):
    """Detecta se a consulta é sobre clima."""
    padroes = [
        r"\b(previsão|clima|meteorologia|meteo|meteor)\b",
        r"\b(como está o tempo|como está o clima|vai chover|temperatura|como esta o dia|qual a meteo de amanha|qual a meteor de amanha)\b",
    ]
    query = query.lower()
    for padrao in padroes:
        if re.search(padrao, query):
            return True
    return False


def clean_forecast_keywords(query):
    """Remove palavras que confundem extração da cidade."""
    query = query.lower()
    remove_terms = [
        "amanhã",
        "semana que vem",
        "próxima semana",
        "próximos dias",
        "hoje",
        "depois de amanhã",
    ]
    for term in remove_terms:
        query = query.replace(term, "")
    return query


def extract_city(query):
    """Extrai corretamente a cidade da frase de previsão do tempo."""
    query = clean_forecast_keywords(query)

    location_keywords = ["em", "de", "da", "do", "na", "no"]
    stop_keywords = [
        "para",
        "os",
        "as",
        "nos",
        "nas",
        "próximos",
        "próximas",
        "amanhã",
        "semana",
        "semana que vem",
        "dias",
        "hoje",
    ]

    start_pos = -1
    for keyword in location_keywords:
        pos = query.rfind(f" {keyword} ")
        if pos > start_pos:
            start_pos = pos + len(keyword) + 2

    if start_pos == -1:
        city = query
    else:
        city = query[start_pos:]

    # Corta se achar palavras de parada
    for stop_word in stop_keywords:
        stop_pos = city.lower().find(f" {stop_word} ")
        if stop_pos != -1:
            city = city[:stop_pos]
            break

    city = city.strip(",.?! ").title()


    invalid_cities = ["Tempo", "Clima", "Previsão", "Meteorologia", "Meteo", "Meteor"]
    if city in invalid_cities or not city:
        return None

    return city


def normalize_country(country):
    """Normaliza nomes de países para formato aceito pela API."""
    mapping = {
        "brasil": "Brazil",
        "frança": "France",
        "alemanha": "Germany",
        "espanha": "Spain",
        "portugal": "Portugal",
        "estados unidos": "USA",
        "eua": "USA",
        "inglaterra": "United Kingdom",
        "reino unido": "United Kingdom",
    }
    return mapping.get(country.lower(), country.title())


def detect_forecast_request(query):
    """Detecta se o usuário quer previsão para a próxima semana ou próximos dias."""
    query = query.lower()
    if "semana que vem" in query or "próxima semana" in query:
        return True, True
    elif "semana" in query or "próximos dias" in query or "amanhã" in query:
        return True, False
    else:
        return False, False


def handle_weather_query(query):
    """Lida com todo o fluxo de perguntas sobre o clima."""
    if not is_weather_request(query):
        return False

    city = extract_city(query)
    forecast, next_week = detect_forecast_request(query)

    if city:
        say(f"Você quer saber o clima de {city}. Pode me dizer o país?")
        country_response = listen().lower().strip()

        if country_response:
            normalized_country = normalize_country(country_response)
            location = f"{city},{normalized_country}"

            weather_report = get_weather(
                location, forecast=forecast, next_week=next_week
            )

            if "Não consegui obter a previsão" in weather_report:
                say(
                    "Desculpe, não entendi o nome da cidade. Pode repetir o nome da cidade, por favor?"
                )
                city_retry = listen().lower().strip().title()

                if city_retry:
                    say("E o país?")
                    country_retry = listen().lower().strip()
                    normalized_country = normalize_country(country_retry)
                    location = f"{city_retry},{normalized_country}"
                    weather_report = get_weather(
                        location, forecast=forecast, next_week=next_week
                    )
                else:
                    weather_report = "Não foi possível obter a previsão do tempo."
        else:
            weather_report = get_weather(city, forecast=forecast, next_week=next_week)
    else:
        weather_report = get_weather(forecast=forecast, next_week=next_week)

    say(weather_report)
    return True
