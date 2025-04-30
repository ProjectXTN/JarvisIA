def normalize_emotion(emotion):
    mapping = {
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
    return mapping.get(emotion.strip().lower(), emotion.strip().lower())
