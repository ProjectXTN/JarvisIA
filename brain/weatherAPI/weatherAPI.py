import requests
import os
import re
import difflib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from brain.audio import say, listen, ask
from brain.utils.utils import normalize_text
from core import config
from core.settings import HOME_CITY, HOME_COUNTRY

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
HOME_LOCATION = f"{HOME_CITY},{HOME_COUNTRY}"


def get_weather(city=HOME_LOCATION, forecast=False, next_week=False, lang="pt"):
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

        response = requests.get(url, timeout=10)
        # Na fala, só o nome da cidade ("Lexy"), sem o código do país
        city = city.split(",")[0]
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


def _sounds_like_home(city):
    """True se o nome ouvido parece a cidade de casa (o Whisper erra a grafia)."""
    heard = normalize_text(city)
    home = normalize_text(HOME_CITY)
    return difflib.SequenceMatcher(None, heard, home).ratio() >= 0.65


def resolve_location(city):
    """Transforma o nome ouvido em 'Cidade,PAÍS' para a OpenWeather.

    Usa a cidade de casa se o nome soar parecido; senão pergunta ao serviço
    de geocodificação da OpenWeather. Devolve None se a cidade não existe.
    """
    if _sounds_like_home(city):
        return HOME_LOCATION

    try:
        results = requests.get(
            "https://api.openweathermap.org/geo/1.0/direct",
            params={"q": city, "limit": 1, "appid": OPENWEATHER_API_KEY},
            timeout=10,
        ).json()
    except Exception as e:
        print(f"[CLIMA] Geocodificação falhou, usando o nome como ouvido: {e}")
        return city

    if isinstance(results, list):
        if not results:
            return None
        return f"{results[0]['name']},{results[0]['country']}"

    # Resposta de erro da API (chave sem acesso, por exemplo)
    print(f"[CLIMA] Geocodificação indisponível: {results}")
    return city


def handle_weather_query(query, lang="pt"):
    if not is_weather_request(query):
        return False

    city = extract_city(query)
    forecast, next_week = detect_forecast_request(query)

    # Sem cidade na frase: usa a cidade de casa. Não pergunta mais o país;
    # a geocodificação descobre sozinha.
    location = resolve_location(city) if city else HOME_LOCATION

    if location is None and not config.IS_API_REQUEST:
        city_retry = ask(f"Não encontrei a cidade {city}. Pode repetir só o nome da cidade?").strip(" .,!?").title()
        location = resolve_location(city_retry) if city_retry else None

    if location is None:
        weather_report = {
            "pt": "Não encontrei essa cidade.",
            "en": "I could not find that city.",
            "fr": "Je n'ai pas trouvé cette ville.",
        }.get(lang, "Não encontrei essa cidade.")
    else:
        print(f"[CLIMA] Consultando: {location}")
        weather_report = get_weather(
            location, forecast=forecast, next_week=next_week, lang=lang
        )

    if not weather_report:
        weather_report = "Desculpe, não consegui obter a previsão do tempo."

    if not config.IS_API_REQUEST:
        say(weather_report)

    return weather_report
