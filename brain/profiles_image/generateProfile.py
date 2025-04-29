class GenerationProfile:
    def __init__(self, name, model, sampler, cfg_scale, steps, negative_prompt, width=1024, height=1024):
        self.name = name
        self.model = model
        self.sampler = sampler
        self.cfg_scale = cfg_scale
        self.steps = steps
        self.negative_prompt = negative_prompt
        self.width = width
        self.height = height
        
def detect_profile_from_prompt(prompt):
    prompt = prompt.lower()

    if any(word in prompt for word in ["planeta", "alienígena", "espaço", "ficção científica", "estação espacial", "mundo alienígena", "sci-fi", "space", "extraterrestre"]):
        return "sci_fi_planet"

    if any(word in prompt for word in ["cidade futurista", "neon", "cyberpunk", "metrópole futurista", "rua iluminada", "tokyo futurista", "cidade do futuro"]):
        return "cyberpunk"

    if any(word in prompt for word in ["castelo", "reino mágico", "dragão", "cavaleiro", "floresta encantada", "reino de fantasia", "épico medieval", "magia", "fadas"]):
        return "fantasy_kingdom"

    if any(word in prompt for word in ["batalha medieval", "guerra de cavaleiros", "exército medieval", "batalha épica", "cavaleiros em guerra", "soldados de armadura"]):
        return "medieval_battle"

    if any(word in prompt for word in ["horror", "terror", "mansão assombrada", "cemitério", "castelo sombrio", "vampiro", "gótico", "noite sombria", "escuro e sombrio"]):
        return "dark_gothic"

    if any(word in prompt for word in ["retrato realista", "foto realista", "fotografia de pessoa", "retrato de mulher", "retrato de homem", "selfie ultra realista", "foto de rosto"]):
        return "realism"

    if any(word in prompt for word in ["pintura artística", "fantasia artística", "arte épica", "pintura de fantasia", "imagem estilizada", "obra de arte"]):
        return "artistic"

    return "realism"

        
PROFILES = {
    "realism": GenerationProfile(
        name="Realistic Portrait",
        model="RealisticVision.safetensors",
        sampler="DPM++ 2M Karras",
        cfg_scale=8,
        steps=40,
        negative_prompt=(
            "blurry, lowres, bad anatomy, bad hands, missing fingers, "
            "extra limbs, poorly drawn face, deformed face, bad lighting, "
            "watermark, text, logo, multiple people, crowd, group of people"
        ),
        width=768,
        height=1152,
    ),
    "artistic": GenerationProfile(
        name="Artistic Fantasy",
        model="DreamShaper_8.safetensors",
        sampler="DPM++ 2M Karras",
        cfg_scale=10,
        steps=50,
        negative_prompt=(
            "blurry, lowres, bad anatomy, weird colors, bad hands, missing fingers, "
            "poorly drawn face, bad composition, extra limbs, watermark, text"
        ),
        width=1024,
        height=1024,
    ),
    "cyberpunk": GenerationProfile(
        name="Futuristic City",
        model="RealisticVision.safetensors",
        sampler="DPM++ 2M Karras",
        cfg_scale=9,
        steps=45,
        negative_prompt=(
            "blurry, lowres, bad anatomy, multiple people, crowd, dull colors, "
            "bad reflections, poorly drawn city, broken buildings, watermark, text"
        ),
        width=1536,
        height=864,
    ),
    "fantasy_kingdom": GenerationProfile(
        name="Fantasy Magic Kingdom",
        model="DreamShaper_8.safetensors",
        sampler="DPM++ 2M SDE Karras",
        cfg_scale=11,
        steps=50,
        negative_prompt=(
            "blurry, bad anatomy, low quality, dark colors, extra limbs, weird background, "
            "poorly drawn castle, poorly drawn dragon, watermark, text"
        ),
        width=1024,
        height=1536,
    ),
    "dark_gothic": GenerationProfile(
        name="Dark Gothic Horror",
        model="RealisticVision.safetensors",
        sampler="DPM++ 2M Karras",
        cfg_scale=10,
        steps=45,
        negative_prompt=(
            "bright lighting, cartoonish, blurry, lowres, bad anatomy, missing limbs, "
            "watermark, text, poorly drawn horror, broken scene"
        ),
        width=960,
        height=1280,
    ),
    "sci_fi_planet": GenerationProfile(
        name="Sci-Fi Alien Planet",
        model="DreamShaper_8.safetensors",
        sampler="DPM++ 2M SDE Karras",
        cfg_scale=10,
        steps=60,
        negative_prompt=(
            "blurry, dull colors, bad planets, broken stars, low quality, poorly drawn spaceship, "
            "bad anatomy, watermark, text"
        ),
        width=1536,
        height=864,
    ),
    "medieval_battle": GenerationProfile(
        name="Medieval Epic Battle",
        model="RealisticVision.safetensors",
        sampler="DPM++ 2M Karras",
        cfg_scale=10,
        steps=50,
        negative_prompt=(
            "blurry, cartoonish, lowres, poorly drawn soldiers, broken armor, bad faces, "
            "watermark, text, deformed horses"
        ),
        width=1536,
        height=864,
    ),
}
