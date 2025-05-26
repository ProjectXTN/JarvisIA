import requests
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from brain.audio import say, listen
from brain.utils.utils import normalize_text
from core import config

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def get_weather(city="Lexy", forecast=False, next_week=False, lang="pt"):
    if not OPENWEATHER_API_KEY:
        return {
            "pt": "API KEY do serviço de previsão do tempo não configurada.",
            "en": "Weather service API KEY not configured.",
            "fr": "Clé API du service météo non configurée.",
        }.get(lang, "API KEY do serviço de previsão do tempo não configurada.")

    # Mapear lang para código reconhecido pela OpenWeather
    lang_map = {"pt": "pt_br", "en": "en", "fr": "fr"}
    api_lang = lang_map.get(lang, "en")

    try:
        if forecast:
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&lang={api_lang}&units=metric"
        else:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&lang={api_lang}&units=metric"

        response = requests.get(url)
        data = response.json()

        if data.get("cod") not in (200, "200"):
            return {
                "pt": "Não consegui obter a previsão do tempo agora.",
                "en": "Could not get the weather forecast right now.",
                "fr": "Je n'ai pas pu obtenir la météo pour le moment.",
            }.get(lang, "Não consegui obter a previsão do tempo agora.")

        # Nomes dos dias da semana nos três idiomas
        dias_semana = {
            "pt": [
                "Segunda",
                "Terça",
                "Quarta",
                "Quinta",
                "Sexta",
                "Sábado",
                "Domingo",
            ],
            "en": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
            "fr": [
                "Lundi",
                "Mardi",
                "Mercredi",
                "Jeudi",
                "Vendredi",
                "Samedi",
                "Dimanche",
            ],
        }

        if forecast:
            forecast_texts = []
            for entry in data["list"]:
                date_str = entry["dt_txt"].split(" ")[0]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_of_week = (
                    dias_semana[lang][date_obj.weekday()]
                    if lang in dias_semana
                    else date_obj.strftime("%A")
                )
                formatted_date = date_obj.strftime("%d-%m")
                weather = entry["weather"][0]["description"].capitalize()
                temp = entry["main"]["temp"]

                forecast_texts.append(
                    (
                        date_obj,
                        f"{day_of_week} {formatted_date}: {weather}, {temp:.0f}°C",
                    )
                )

            unique_days = []
            final_forecast = []

            for date_obj, line in forecast_texts:
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

            # Mensagem multilíngue
            intro = {
                "pt": f"Previsão do tempo para {city} nos próximos dias:",
                "en": f"Weather forecast for {city} for the next days:",
                "fr": f"Prévisions météo pour {city} pour les prochains jours:",
            }.get(lang, f"Weather forecast for {city}:")

            return intro + "\n" + "\n".join(final_forecast)

        else:
            weather = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            report = {
                "pt": (
                    f"Em {city}, o clima está {weather} com temperatura de {temp:.0f}°C, "
                    f"sensação térmica de {feels_like:.0f}°C, umidade de {humidity}% "
                    f"e ventos a {wind_speed:.0f} km/h."
                ),
                "en": (
                    f"In {city}, the weather is {weather} with a temperature of {temp:.0f}°C, "
                    f"feels like {feels_like:.0f}°C, humidity of {humidity}%, "
                    f"and wind speeds of {wind_speed:.0f} km/h."
                ),
                "fr": (
                    f"À {city}, le temps est {weather} avec une température de {temp:.0f}°C, "
                    f"ressenti de {feels_like:.0f}°C, humidité de {humidity}%, "
                    f"et vents à {wind_speed:.0f} km/h."
                ),
            }.get(
                lang,
                f"In {city}, the weather is {weather} with a temperature of {temp:.0f}°C.",
            )

            return report

    except Exception as e:
        print(f"[ERRO] Falha ao buscar previsão do tempo: {e}")
        return {
            "pt": "Ocorreu um erro ao tentar buscar a previsão.",
            "en": "An error occurred while fetching the weather forecast.",
            "fr": "Une erreur est survenue lors de la récupération de la météo.",
        }.get(lang, "Ocorreu um erro ao tentar buscar a previsão.")


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
        r"\b(previs[aã]o|previsando|clima|clime|meteorologia|meteo|meteor|tempo)\b",
        r"\b(como est[aá] o tempo|como est[aá] o clima|vai chover|temperatura|como esta o dia|qual a meteo( de| para)? amanh[aã]|qual a meteor( de| para)? amanh[aã])\b",
        # Frances
        r"\b(m[ée]t[ée]o|meteo|pr[ée]vision|pr[ée]visions|temps|temp[ée]rature|il va pleuvoir|va-t-il pleuvoir|pleuvra-t-il|quelle m[ée]t[ée]o|quelle temp[ée]rature|quel temps|m[ée]t[ée]o (du jour|demain|aujourd'hui))\b",
        # INGLÊS
        r"\b(weather|forecast|temperature|climate|is it going to rain|will it rain|is it raining|what'?s the weather|how'?s the weather|weather (today|tomorrow|now)|current weather|weather forecast|rain forecast)\b",
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
    """Extrai corretamente a cidade da frase de previsão do tempo (pt, en, fr)."""
    query = clean_forecast_keywords(query)
    query_norm = normalize_text(query)

    # Keywords de localização
    location_keywords = [
        "para",
        "em",
        "de",
        "da",
        "do",
        "na",
        "no",  # pt
        "in",
        "at",
        "for",
        "from",  # en
        "a",
        "au",
        "en",
        "pour",
        "dans",
        "du",
        "à",  # fr/pt
    ]
    stop_keywords = [
        # PT
        "para",
        "os",
        "as",
        "nos",
        "nas",
        "proximos",
        "proximas",
        "amanha",
        "semana",
        "semana que vem",
        "dias",
        "hoje",
        # EN
        "for",
        "in",
        "at",
        "of",
        "tomorrow",
        "next week",
        "days",
        "today",
        "week",
        "after tomorrow",
        # FR
        "pour",
        "a",
        "au",
        "aux",
        "demain",
        "semaine",
        "prochains",
        "prochaines",
        "aujourdhui",
        "jours",
        "apres-demain",
    ]

    regex = r"(?:{})(?:\s+|['’])([a-zA-Zà-ÿ\-']+)".format("|".join(location_keywords))
    matches = re.findall(regex, query_norm)
    city = None
    if matches:
        city = matches[-1]
    else:
        tokens = re.findall(r"[a-zA-Zà-ÿ\-']+", query_norm)
        for word in reversed(tokens):
            if word not in stop_keywords:
                city = word
                break

    if not city:
        return None

    city = city.strip(",.?! ").title()
    invalid_cities = [
        "Tempo",
        "Clima",
        "Previsao",
        "Meteorologia",
        "Meteo",
        "Meteor",
        "Weather",
        "Forecast",
        "Temperature",
        "Climate",
        "Prevision",
        "Temps",
        "Aujourd",
        "Hui",
        "Demain",
        "Semaine",
        "Jours",
        "Tomorrow",
        "Week",
        "Days",
    ]
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
    """Detecta se o usuário quer previsão para a próxima semana ou próximos dias (PT, EN, FR)."""
    query = query.lower()

    next_week_keywords = [
        "semana que vem",
        "próxima semana",  # pt
        "next week",  # en
        "semaine prochaine",
        "la semaine prochaine",  # fr
    ]

    forecast_keywords = [
        "semana",
        "próximos dias",
        "amanhã",
        "depois de amanhã",  # pt
        "week",
        "days",
        "tomorrow",
        "today",
        "after tomorrow",  # en
        "semaine",
        "jours",
        "demain",
        "après-demain",
        "aujourd'hui",  # fr
    ]

    # Next week?
    for k in next_week_keywords:
        if k in query:
            return True, True
    for k in forecast_keywords:
        if k in query:
            return True, False
    return False, False


def handle_weather_query(query, lang="pt"):
    if not is_weather_request(query):
        return False

    city = extract_city(query)
    forecast, next_week = detect_forecast_request(query)

    if city:
        if config.IS_API_REQUEST:
            location = city
        else:
            say(f"Você quer saber o clima de {city}. Pode me dizer o país?")
            country_response = listen().lower().strip()

            if country_response:
                normalized_country = normalize_country(country_response)
                location = f"{city},{normalized_country}"
            else:
                location = city
    else:
        location = None

    # Faz a busca pela previsão
    weather_report = get_weather(
        location if location else "Lexy",  # fallback
        forecast=forecast,
        next_week=next_week,
        lang=lang,
    )

    # Se não deu certo, tenta repetir no modo CLI
    if not weather_report or "Não consegui obter" in weather_report:
        if not config.IS_API_REQUEST:
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

    if not weather_report:
        weather_report = "Desculpe, não consegui obter a previsão do tempo."

    if not config.IS_API_REQUEST:
        say(weather_report)

    return weather_report
