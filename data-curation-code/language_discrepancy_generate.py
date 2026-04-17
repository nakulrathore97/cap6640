"""
language_discrepancy_generate.py
Introduce exactly ONE language-discrepancy error per prompt line.

Strategy:
  - Look for English words in the prompt that have a known Spanish or French
    translation.
  - Randomly pick one such word and replace it with its foreign-language
    equivalent (Spanish or French, chosen randomly).
  - Only ONE substitution is made per prompt, analogous to typo_generate.py
    and grammar_generate.py.

Example:
  Control:   "A man eating an orange."
  Perturbed: "A man eating an naranja."   (naranja = orange in Spanish)
  Perturbed: "A man eating an orange."    (or: "Un homme mangeant une orange.")
"""

import random
import re

# ---------------------------------------------------------------------------
# Translation dictionaries  (English → Spanish / French)
# Keys are lowercase English words.  Words were chosen because they are common
# in image-generation prompts (objects, colours, people, scenes, actions …).
# ---------------------------------------------------------------------------

EN_TO_ES: dict[str, str] = {
    # colours
    "red": "rojo", "blue": "azul", "green": "verde", "yellow": "amarillo",
    "black": "negro", "white": "blanco", "orange": "naranja", "purple": "púrpura",
    "pink": "rosa", "brown": "marrón", "gray": "gris", "grey": "gris",
    "gold": "oro", "silver": "plata",
    # people / animals
    "man": "hombre", "woman": "mujer", "boy": "niño", "girl": "niña",
    "child": "niño", "children": "niños", "person": "persona",
    "dog": "perro", "cat": "gato", "bird": "pájaro", "horse": "caballo",
    "fish": "pez", "lion": "león", "tiger": "tigre", "bear": "oso",
    "wolf": "lobo", "fox": "zorro", "rabbit": "conejo", "snake": "serpiente",
    # nature / scene
    "tree": "árbol", "flower": "flor", "sun": "sol", "moon": "luna",
    "star": "estrella", "sky": "cielo", "cloud": "nube", "rain": "lluvia",
    "snow": "nieve", "fire": "fuego", "water": "agua", "river": "río",
    "mountain": "montaña", "forest": "bosque", "beach": "playa",
    "ocean": "océano", "sea": "mar", "island": "isla", "desert": "desierto",
    "field": "campo", "garden": "jardín", "city": "ciudad", "town": "pueblo",
    "village": "aldea", "road": "camino", "bridge": "puente",
    # objects / things
    "house": "casa", "door": "puerta", "window": "ventana", "table": "mesa",
    "chair": "silla", "book": "libro", "car": "coche", "train": "tren",
    "boat": "barco", "plane": "avión", "sword": "espada", "shield": "escudo",
    "crown": "corona", "castle": "castillo", "tower": "torre",
    "key": "llave", "bottle": "botella", "cup": "taza", "hat": "sombrero",
    "dress": "vestido", "shirt": "camisa", "coat": "abrigo", "shoes": "zapatos",
    "ring": "anillo", "light": "luz", "shadow": "sombra", "smoke": "humo",
    # food
    "apple": "manzana", "bread": "pan", "cake": "pastel", "wine": "vino",
    "fruit": "fruta", "meat": "carne", "egg": "huevo", "cheese": "queso",
    # actions (present participle → Spanish gerund)
    "eating": "comiendo", "running": "corriendo", "walking": "caminando",
    "sitting": "sentado", "standing": "de pie", "flying": "volando",
    "holding": "sosteniendo", "looking": "mirando", "sleeping": "durmiendo",
    "fighting": "luchando", "playing": "jugando", "dancing": "bailando",
    "riding": "montando", "painting": "pintando", "reading": "leyendo",
    # adjectives / descriptors
    "beautiful": "hermoso", "dark": "oscuro", "bright": "brillante",
    "ancient": "antiguo", "old": "viejo", "young": "joven", "small": "pequeño",
    "big": "grande", "tall": "alto", "short": "corto", "long": "largo",
    "fast": "rápido", "slow": "lento", "happy": "feliz", "sad": "triste",
    "angry": "enojado", "calm": "tranquilo", "lonely": "solitario",
    "magical": "mágico", "digital": "digital", "realistic": "realista",
    "fantasy": "fantasía", "epic": "épico", "dramatic": "dramático",
    "elegant": "elegante", "mysterious": "misterioso", "detailed": "detallado",
    # misc
    "portrait": "retrato", "landscape": "paisaje", "background": "fondo",
    "painting": "pintura", "night": "noche", "day": "día", "morning": "mañana",
    "evening": "tarde", "winter": "invierno", "summer": "verano",
    "spring": "primavera", "autumn": "otoño",
}

EN_TO_FR: dict[str, str] = {
    # colours
    "red": "rouge", "blue": "bleu", "green": "vert", "yellow": "jaune",
    "black": "noir", "white": "blanc", "orange": "orange", "purple": "violet",
    "pink": "rose", "brown": "brun", "gray": "gris", "grey": "gris",
    "gold": "or", "silver": "argent",
    # people / animals
    "man": "homme", "woman": "femme", "boy": "garçon", "girl": "fille",
    "child": "enfant", "children": "enfants", "person": "personne",
    "dog": "chien", "cat": "chat", "bird": "oiseau", "horse": "cheval",
    "fish": "poisson", "lion": "lion", "tiger": "tigre", "bear": "ours",
    "wolf": "loup", "fox": "renard", "rabbit": "lapin", "snake": "serpent",
    # nature / scene
    "tree": "arbre", "flower": "fleur", "sun": "soleil", "moon": "lune",
    "star": "étoile", "sky": "ciel", "cloud": "nuage", "rain": "pluie",
    "snow": "neige", "fire": "feu", "water": "eau", "river": "rivière",
    "mountain": "montagne", "forest": "forêt", "beach": "plage",
    "ocean": "océan", "sea": "mer", "island": "île", "desert": "désert",
    "field": "champ", "garden": "jardin", "city": "ville", "town": "ville",
    "village": "village", "road": "route", "bridge": "pont",
    # objects / things
    "house": "maison", "door": "porte", "window": "fenêtre", "table": "table",
    "chair": "chaise", "book": "livre", "car": "voiture", "train": "train",
    "boat": "bateau", "plane": "avion", "sword": "épée", "shield": "bouclier",
    "crown": "couronne", "castle": "château", "tower": "tour",
    "key": "clé", "bottle": "bouteille", "cup": "tasse", "hat": "chapeau",
    "dress": "robe", "shirt": "chemise", "coat": "manteau", "shoes": "chaussures",
    "ring": "anneau", "light": "lumière", "shadow": "ombre", "smoke": "fumée",
    # food
    "apple": "pomme", "bread": "pain", "cake": "gâteau", "wine": "vin",
    "fruit": "fruit", "meat": "viande", "egg": "œuf", "cheese": "fromage",
    # actions (present participle → French)
    "eating": "mangeant", "running": "courant", "walking": "marchant",
    "sitting": "assis", "standing": "debout", "flying": "volant",
    "holding": "tenant", "looking": "regardant", "sleeping": "dormant",
    "fighting": "combattant", "playing": "jouant", "dancing": "dansant",
    "riding": "montant", "painting": "peignant", "reading": "lisant",
    # adjectives / descriptors
    "beautiful": "beau", "dark": "sombre", "bright": "brillant",
    "ancient": "ancien", "old": "vieux", "young": "jeune", "small": "petit",
    "big": "grand", "tall": "grand", "short": "court", "long": "long",
    "fast": "rapide", "slow": "lent", "happy": "heureux", "sad": "triste",
    "angry": "en colère", "calm": "calme", "lonely": "solitaire",
    "magical": "magique", "digital": "numérique", "realistic": "réaliste",
    "fantasy": "fantaisie", "epic": "épique", "dramatic": "dramatique",
    "elegant": "élégant", "mysterious": "mystérieux", "detailed": "détaillé",
    # misc
    "portrait": "portrait", "landscape": "paysage", "background": "arrière-plan",
    "painting": "peinture", "night": "nuit", "day": "jour", "morning": "matin",
    "evening": "soir", "winter": "hiver", "summer": "été",
    "spring": "printemps", "autumn": "automne",
}

LANG_DICTS = {
    "spanish": EN_TO_ES,
    "french":  EN_TO_FR,
}


# ---------------------------------------------------------------------------
# Core perturbation logic
# ---------------------------------------------------------------------------

def _find_candidates(text: str, translation_dict: dict[str, str]) -> list[re.Match]:
    """Return all regex Match objects for translatable words in `text`."""
    candidates = []
    for en_word in translation_dict:
        pattern = r'\b' + re.escape(en_word) + r'\b'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            candidates.append(m)
    return candidates


def perturb_language(text: str, lang: str | None = None) -> tuple[str, str | None]:
    """Replace ONE English word with its Spanish or French translation.

    Parameters
    ----------
    text : str
        The original English prompt.
    lang : str | None
        'spanish', 'french', or None (chosen randomly).

    Returns
    -------
    (perturbed_text, language_used)
        language_used is None if no substitution was possible.
    """
    if lang is None:
        lang = random.choice(list(LANG_DICTS.keys()))

    translation_dict = LANG_DICTS[lang]
    candidates = _find_candidates(text, translation_dict)

    if not candidates:
        return text, None  # no known word found — return unchanged

    m = random.choice(candidates)
    en_word  = m.group(0)
    foreign  = translation_dict[en_word.lower()]

    # Preserve leading-capital if the original word was capitalised
    if en_word[0].isupper() and len(foreign) > 0:
        foreign = foreign[0].upper() + foreign[1:]

    perturbed = text[: m.start()] + foreign + text[m.end():]
    return perturbed, lang


# ---------------------------------------------------------------------------
# Main — batch processing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    input_path  = os.path.join(os.path.dirname(__file__), "diffusiondb_prompts_small.txt")
    output_path = os.path.join(os.path.dirname(__file__), "diffusiondb_prompts_small_langdiscrepancy.txt")

    changed = 0
    total   = 0

    with open(input_path, "r", encoding="utf-8") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            prompt    = line.rstrip("\n")
            perturbed, lang = perturb_language(prompt)
            fout.write(perturbed + "\n")
            total += 1
            if perturbed != prompt:
                changed += 1

    print(f"Done. {changed}/{total} prompts perturbed → {output_path}")
