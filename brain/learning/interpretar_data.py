from datetime import datetime, timedelta
import calendar

def interpretar_intervalo_data(texto):
    hoje = datetime.now().date()

    texto = texto.lower()

    if "hoje" in texto:
        return hoje.isoformat(), hoje.isoformat()
    elif "ontem" in texto:
        ontem = hoje - timedelta(days=1)
        return ontem.isoformat(), ontem.isoformat()
    elif "esta semana" in texto or "nesta semana" in texto:
        inicio = hoje - timedelta(days=hoje.weekday())  # segunda
        return inicio.isoformat(), hoje.isoformat()
    elif "este mês" in texto or "neste mês" in texto:
        inicio = hoje.replace(day=1)
        return inicio.isoformat(), hoje.isoformat()
    else:
        # Verifica mês específico por nome
        meses = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
            "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
            "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
        }
        for nome_mes, numero in meses.items():
            if nome_mes in texto:
                ano = hoje.year
                inicio = datetime(ano, numero, 1).date()
                fim = datetime(ano, numero, calendar.monthrange(ano, numero)[1]).date()
                return inicio.isoformat(), fim.isoformat()

    return None, None  # não reconhecido
