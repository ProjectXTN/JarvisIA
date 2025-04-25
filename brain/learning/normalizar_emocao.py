def normalizar_emocao(emocao):
    mapa = {
        "muito": "feliz",
        "muito feliz": "feliz",
        "felizão": "feliz",
        "deixou feliz": "feliz",
        "fez feliz": "feliz",
        "tristeza": "triste",
        "triste": "triste",
        "nervoso": "estressado",
        "estressado": "estressado",
        "estressou": "estressado",
        "raiva": "irritado",
        "puto": "irritado",
        "irritou": "irritado",
        "me irritou": "irritado",
        "me marcou": "marcante",
    }
    return mapa.get(emocao.strip().lower(), emocao.strip().lower())
