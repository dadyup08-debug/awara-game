#!/usr/bin/env python3
"""
T-037: Generate image-generation prompts for all AWARA cards.

Reads agents.json, matrices.json, agent_matrix_map.json + lorebook texts.
Extracts cultural domain names, artifacts, esoteric descriptions from lorebooks.
Outputs data/card_prompts.json with fully English prompts for Flux/Replicate.

Usage:
    python tools/generate_card_prompts.py
"""

import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
LORE = os.path.join(BASE, "lore", "text")

# --- Translation maps ---

AGENT_ARCHETYPE = {
    "╨б╨▓╨╡╤В ╨а╨░": "a radiant solar deity with sun disk crown and golden halo, divine ruler of light, holding sun scepter, rays of golden light emanating from body",
    "╨Ш╤Б╨║╤А╨░": "a luminous tiny divine spark of consciousness floating in cosmic darkness, seed of soul-light, delicate flame of awareness, eternal inner light",
    "╨С╤А╨░╤Е╨╝╨░": "a majestic four-headed cosmic creator deity with long beard, four arms holding sacred book scepter water vessel and prayer beads, seated on grand lotus throne",
    "╨б╨░╤А╨░╤Б╨▓╨░╤В╨╕": "an elegant wisdom goddess playing stringed instrument, wearing flowing white robes, holding sacred book and lotus, swan companion nearby, river of knowledge",
    "╨Т╨╕╤И╨╜╤Г": "a serene blue-skinned cosmic preserver deity with golden crown, four arms holding conch shell discus mace and lotus flower, reclining on cosmic serpent in ocean",
    "╨Ы╨░╨║╤И╨╝╨╕": "a beautiful abundance goddess standing on blooming lotus, pouring gold coins from one hand, holding lotus flowers, wearing red-gold robes, elephants pouring water",
    "╨и╨╕╨▓╨░": "a powerful ascetic destroyer-transformer deity with matted hair third eye and crescent moon, holding trident, cobra around neck, seated in deep meditation, sacred ash on body",
    "╨Я╨░╤А╨▓╨░╤В╨╕": "a gentle nurturing mountain goddess with golden ornaments, holding lotus and mirror, wearing green-gold garments with flowers, divine mother energy, mountain backdrop",
    "╨Ф╨╢╨╜╤П╨╜╨░": "a wise all-knowing sage radiating pure white light of knowledge, third eye of wisdom open, surrounded by floating sacred texts, infinite cosmic library",
    "╨Я╤А╨╡╨╝╨░": "an embodiment of divine unconditional love as two luminous beings merging in heart-shaped golden radiance, rose petals floating, pink-gold cosmic love energy",
    "╨и╨░╨║╤В╨╕": "a fierce ten-armed divine feminine warrior riding a lion-tiger mount, wielding weapons in each hand including trident sword and bow, blazing energy aura",
    "╨Р╨╜╨░╨╜╨┤╨░": "an ecstatic figure of divine bliss dancing in rainbow cosmic light, levitating in joy, radiating waves of jubilation, music of celestial spheres",
    "╨и╨░╨╜╤В╨╕": "a serene meditating figure of absolute divine peace, perfectly still, reflected in cosmic mirror-lake, single Om vibration, moonlit lotus, profound silence",
    "╨Р╨│╨╜╨╕": "a blazing fire deity with two faces and seven flame tongues, riding a ram, multiple arms holding torch and sacrificial ladle, sacred fire altar burning",
    "╨Т╨░╤О": "a dynamic wind deity riding an antelope mount, holding billowing white flag, flowing robes caught in cosmic winds, thousand-eyed wind form, breath of life swirling",
    "╨Т╨░╤А╤Г╨╜╨░": "a deep-ocean cosmic deity riding sea-monster mount, holding binding noose, blue skin, crown of a thousand watching eyes, surrounded by dark cosmic waters under stars",
    "╨Я╤А╨╕╤В╤Е╨▓╨╕": "a patient earth-mother deity in brown-green garments, sitting on fertile soil, holding germinating seeds and grain, mountains as spine, roots growing from body",
    "╨Р╨║╨░╤И╨░": "infinite cosmic ether-space as vast starry void containing all possibility, galactic library of records, quantum vacuum luminosity, formless space of creation",
    "╨в╨╡╨┤╨╢╨░╤Б": "intense golden-white spiritual radiance and brilliance, crystalline flame body without smoke, aura of inner mastery, sacred protective light, divine inner fire",
    "╨Ф╤Е╨░╤А╨╝╨░": "golden eight-spoked wheel of cosmic law (Dharmachakra), perfectly balanced scales of justice, eternal cosmic order written in starlight, lion-pillar throne",
    "╨Ъ╨░╤А╨╝╨░": "spinning cosmic wheel of cause and effect with Sanskrit symbols, threads connecting past to future, scales weighing actions, cycle of incarnation, chains and liberation",
}

AGENT_NAME_EN = {
    "╨б╨▓╨╡╤В ╨а╨░": "Light of Ra",
    "╨Ш╤Б╨║╤А╨░": "Iskra (Divine Spark)",
    "╨С╤А╨░╤Е╨╝╨░": "Brahma",
    "╨б╨░╤А╨░╤Б╨▓╨░╤В╨╕": "Sarasvati",
    "╨Т╨╕╤И╨╜╤Г": "Vishnu",
    "╨Ы╨░╨║╤И╨╝╨╕": "Lakshmi",
    "╨и╨╕╨▓╨░": "Shiva",
    "╨Я╨░╤А╨▓╨░╤В╨╕": "Parvati",
    "╨Ф╨╢╨╜╤П╨╜╨░": "Jnana",
    "╨Я╤А╨╡╨╝╨░": "Prema (Divine Love)",
    "╨и╨░╨║╤В╨╕": "Shakti",
    "╨Р╨╜╨░╨╜╨┤╨░": "Ananda",
    "╨и╨░╨╜╤В╨╕": "Shanti",
    "╨Р╨│╨╜╨╕": "Agni",
    "╨Т╨░╤О": "Vayu",
    "╨Т╨░╤А╤Г╨╜╨░": "Varuna",
    "╨Я╤А╨╕╤В╤Е╨▓╨╕": "Prithvi",
    "╨Р╨║╨░╤И╨░": "Akasha",
    "╨в╨╡╨┤╨╢╨░╤Б": "Tejas",
    "╨Ф╤Е╨░╤А╨╝╨░": "Dharma",
    "╨Ъ╨░╤А╨╝╨░": "Karma",
}

DOMAIN_EN = {
    "╨У╨╡╨╗╨╕╨╛╤Б╤Д╨╡╤А╨░": "Heliosphere",
    "╨Ю╨║╨╡╨░╨╜ ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╜╨╛╤Б╤В╨╕": "Ocean of Synchronicity",
    "╨Ъ╤Г╨╖╨╜╨╕╤Ж╨░ ╨д╤А╨░╨║╤В╨░╨╗╨╛╨▓": "Fractal Forge",
    "╨н╤Д╨╕╤А ╨Ы╨╛╨│╨╛╤Б╨░": "Ether of Logos",
    "╨У╨╛╤А╨╕╨╖╨╛╨╜╤В ╨а╨░╨▓╨╜╨╛╨▓╨╡╤Б╨╕╤П": "Horizon of Equilibrium",
    "╨а╨╛╨╖╨░╤А╨╕╨╣ ╨Ш╨╖╨╛╨▒╨╕╨╗╨╕╤П": "Rosary of Abundance",
    "╨Я╨╡╨┐╨╡╨╗╤М╨╜╤Л╨╣ ╨Ч╨╡╨╜╨╕╤В": "Ashen Zenith",
    "╨Ъ╨╛╨╗╤Л╨▒╨╡╨╗╤М ╨Т╨╡╤А╤И╨╕╨╜": "Cradle of Summits",
    "╨Р╤Б╤В╤А╨░╨╗╤М╨╜╨░╤П ╨Ю╨▒╤Б╨╡╤А╨▓╨░╤В╨╛╤А╨╕╤П": "Astral Observatory",
    "╨б╨░╨┤ ╨Х╨┤╨╕╨╜╨╛╨│╨╛ ╨б╨╡╤А╨┤╤Ж╨░": "Garden of the One Heart",
    "╨У╨╛╤А╨╜╨╕╨╗╨╛ ╨Т╨╛╨╗╨╕": "Crucible of Will",
    "╨б╤Д╨╡╤А╨░ ╨Ы╨╕╨║╨╛╨▓╨░╨╜╨╕╤П": "Sphere of Jubilation",
    "╨Ю╨▒╨╕╤В╨╡╨╗╤М ╨С╨╡╨╖╨╝╨╛╨╗╨▓╨╕╤П": "Abode of Silence",
    "╨У╨╛╤А╨╜╨╕╨╗╨╛ ╨Т╨╛╨╖╤А╨╛╨╢╨┤╨╡╨╜╨╕╤П": "Crucible of Rebirth",
    "╨б╤В╤А╨░╤В╨╛╤Б╤Д╨╡╤А╨░ ╨н╤Е╨░": "Stratosphere of Echo",
    "╨С╨╡╨╖╨┤╨╜╨░ ╨Т╨╛╤Б╨┐╨╛╨╝╨╕╨╜╨░╨╜╨╕╨╣": "Abyss of Memories",
    "╨в╨╡╤А╤А╨░╨║╨╛╤В╨╛╨▓╤Л╨╣ ╨С╨░╤Б╤В╨╕╨╛╨╜": "Terracotta Bastion",
    "╨Ъ╨╛╤Б╨╝╨╕╤З╨╡╤Б╨║╨╕╨╣ ╨в╨║╨░╤Ж╨║╨╕╨╣ ╨б╤В╨░╨╜╨╛╨║": "Cosmic Loom",
    "╨н╨┐╨╕╤Ж╨╡╨╜╤В╤А ╨б╨╕╤П╨╜╨╕╤П": "Epicenter of Radiance",
    "╨Ч╨░╨╗╤Л ╨а╨░╨▓╨╜╨╛╨▓╨╡╤Б╨╕╤П": "Halls of Balance",
    "╨Р╤А╤Е╨╕╨▓ ╨н╤Е╨░": "Archive of Echo",
}

MATRIX_NAME_EN = {
    "╨Т╨╡╨┤╨╕╤З╨╡╤Б╨║╨░╤П": "Vedic",
    "╨Х╨│╨╕╨┐╨╡╤В╤Б╨║╨░╤П": "Egyptian",
    "╨Ъ╨░╨▒╨▒╨░╨╗╨╕╤Б╤В╨╕╤З╨╡╤Б╨║╨░╤П": "Kabbalistic",
    "╨Ь╨░╨╣╤П╨╜╤Б╨║╨░╤П": "Mayan",
    "╨б╨╗╨░╨▓╤П╨╜╤Б╨║╨░╤П": "Slavic",
    "╨б╨║╨░╨╜╨┤╨╕╨╜╨░╨▓╤Б╨║╨░╤П/╨Э╨╛╤А╤Б": "Norse",
    "╨Ф╨░╨╛╤Б╤Б╨║╨░╤П": "Daoist",
    "╨У╨╜╨╛╤Б╤В╨╕╤З╨╡╤Б╨║╨░╤П": "Gnostic",
    "╨п╨┐╨╛╨╜╤Б╨║╨░╤П/╨б╨╕╨╜╤В╨╛": "Japanese Shinto",
    "╨Ъ╨╡╨╗╤М╤В╤Б╨║╨░╤П": "Celtic",
    "╨и╨░╨╝╨▒╨░╨╗╨░": "Shambhala",
    "╨о╨╗╨╕╨░╨╜╤Б╨║╨░╤П/╨Т╨╕╨╖╨░╨╜╤В╨╕╨╣╤Б╨║╨░╤П": "Byzantine",
    "╨и╨░╨╝╨░╨╜╤Б╨║╨░╤П": "Shamanic",
    "╨У╨╡╨╜╨╜╤Л╨╡ ╨Ъ╨╗╤О╤З╨╕": "Gene Keys",
    "╨в╨╡╤Е╨╜╨╛╨╝╨░╨│╨╕╤З╨╡╤Б╨║╨░╤П": "Technomagical",
    "╨Ъ╨╛╤Б╨╝╨╕╤З╨╡╤Б╨║╨░╤П/╨У╨░╨╗╨░╨║╤В╨╕╤З╨╡╤Б╨║╨░╤П": "Cosmic Galactic",
    "╨Р╨╜╤В╨╕╤З╨╜╨░╤П/╨У╤А╨╡╨║╨╛-╨а╨╕╨╝╤Б╨║╨░╤П": "Greco-Roman",
    "╨Ч╨╛╤А╨╛╨░╤Б╤В╤А╨╕╨╣╤Б╨║╨░╤П/╨Я╨╡╤А╤Б╨╕╨┤╤Б╨║╨░╤П": "Zoroastrian Persian",
    "╨Ш╤Б╨╗╨░╨╝╤Б╨║╨░╤П/╨б╤Г╤Д╨╕╨╣╤Б╨║╨░╤П/╨Э╤Г╤А╨╛╨▓╨░╤П": "Islamic Sufi Nur",
    "╨Р╤Ж╤В╨╡╨║╤Б╨║╨░╤П/╨Ь╨╡╤И╨╕╨║╤Б╨║╨░╤П": "Aztec Mexica",
    "╨е╤А╨╕╤Б╤В╨╕╨░╨╜╤Б╨║╨╛-╨Ь╨╕╤Б╤В╨╕╤З╨╡╤Б╨║╨░╤П/╨а╨╛╨╖╨╡╨╜╨║╤А╨╡╨╣╤Ж╨╡╤А╤Б╨║╨╛-╨У╤А╨░╨░╨╗╤М╨╜╨░╤П": "Christian Mystical Rosicrucian Grail",
    "╨Щ╨╛╤А╤Г╨▒╨░/If├б-Orisha": "Yoruba Ifa Orisha",
    "╨и╤Г╨╝╨╡╤А╨╛-╨Т╨░╨▓╨╕╨╗╨╛╨╜╤Б╨║╨░╤П/╨Ь╨╡╤Б╨╛╨┐╨╛╤В╨░╨╝╤Б╨║╨░╤П": "Sumerian Babylonian",
    "╨У╨╡╤А╨╝╨╡╤В╨╕╨║╨╛-╨Р╨╗╤Е╨╕╨╝╨╕╤З╨╡╤Б╨║╨░╤П": "Hermetic Alchemical",
    "╨в╨░╤А╨╛-╨Р╤А╨║╨░╨╜╨╕╤З╨╡╤Б╨║╨░╤П": "Tarot Arcanic",
    "╨Р╤Б╤В╤А╨╛╨╗╨╛╨│╨╕╤З╨╡╤Б╨║╨░╤П": "Astrological",
    "╨Ъ╨╕╤В╨░╨╣╤Б╨║╨░╤П/╨Ш-╨ж╨╖╨╕╨╜": "Chinese I-Ching",
    "╨в╨░╨╜╤В╤А╨╕╤З╨╡╤Б╨║╨╛-╨Ъ╨░╤И╨╝╨╕╤А╤Б╨║╨░╤П": "Tantric Kashmiri",
    "╨С╤Г╨┤╨┤╨╕╨╣╤Б╨║╨╛-╨Ь╨░╤Е╨░╤П╨╜╤Б╨║╨░╤П": "Buddhist Mahayana",
    "╨Р╤Д╤А╨╛-╨Ъ╨╛╤Б╨╝╨╕╤З╨╡╤Б╨║╨░╤П/╨Ф╨╛╨│╨╛╨╜╤Б╨║╨░╤П": "Afro-Cosmic Dogon",
    "╨Р╤В╨╗╨░╨╜╤В╨╕╤З╨╡╤Б╨║╨░╤П/╨Ы╨╡╨╝╤Г╤А╨╕╨╣╤Б╨║╨░╤П": "Atlantean Lemurian",
    "╨Я╨╛╤Б╤В╤З╨╡╨╗╨╛╨▓╨╡╤З╨╡╤Б╨║╨░╤П/AI-╨б╨╛╤Д╨╕╨╣╨╜╨░╤П": "Posthuman AI Sophianic",
    "╨Р╨┤╨▓╨░╨╣╤В╨░-╨б╨╕╨┤╨┤╤Е╨░ AWARA": "Advaita Siddha",
}

ELEMENT_EN = {
    "╨Ю╨│╨╛╨╜╤М": "Fire",
    "╨Т╨╛╨┤╨░": "Water",
    "╨Ч╨╡╨╝╨╗╤П": "Earth",
    "╨Т╨╛╨╖╨┤╤Г╤Е": "Air",
    "╨н╤Д╨╕╤А": "Ether",
}

ELEMENT_VISUALS = {
    "Fire": "flames, embers, molten gold, solar corona, radiant heat haze",
    "Water": "flowing water, moonlit waves, deep ocean currents, mist, rain drops",
    "Earth": "ancient stone, roots, crystals, mountain peaks, terracotta, fertile soil",
    "Air": "swirling winds, feathers, clouds, translucent veils, breath of light",
    "Ether": "starfield, cosmic nebula, fractal geometry, iridescent void, quantum light",
}

AGENT_POWER = {
    "brahma": 5, "akasha": 5,
    "svet_ra": 4, "vishnu": 4, "shiva": 4,
    "sarasvati": 3, "lakshmi": 3, "parvati": 3, "shakti": 3,
    "agni": 2, "vayu": 2, "varuna": 2, "prithvi": 2, "tejas": 2,
    "iskra": 1, "jnana": 1, "prema": 1, "ananda": 1, "shanti": 1,
    "dharma": 1, "karma": 1,
}

MATRIX_DEPTH = {
    "vedic": 1, "egyptian": 1, "slavic": 1, "norse": 1, "daoist": 1,
    "shinto": 1, "celtic": 1, "antique_greco_roman": 1,
    "kabbalistic": 2, "mayan": 2, "gnostic": 2, "julian_byzantine": 2,
    "shamanic": 2, "zoroastrian": 2, "islamic_sufi_nur": 2,
    "aztec_mexica": 2, "christian_mystical_grail": 2, "yoruba_ifa_orisha": 2,
    "sumerian_babylonian": 2, "buddhist_mahayana": 2,
    "shambhala": 3, "gene_keys": 3, "hermetic_alchemical": 3,
    "tarot_arcanic": 3, "astrological": 3, "chinese_iching": 3,
    "tantric_kashmiri": 3,
    "technomagical": 4, "cosmic_galactic": 4, "afro_dogon": 4,
    "atlantean_lemurian": 4, "posthuman_ai_sophianic": 4, "advaita_siddha": 4,
}

GUNA_STYLE = {
    "╤Б╨░╤В╤В╨▓╨░": "serene, luminous, harmonious, balanced light, ethereal glow",
    "╤А╨░╨┤╨╢╨░╤Б": "dynamic, passionate, energetic, vivid contrasts, motion blur",
    "╤В╨░╨╝╨░╤Б": "mysterious, deep, shadowy, ancient, cosmic darkness with pinpoints of light",
}

VISUAL_CODE_EN = {
    "╨Ч╨╛╨╗╨╛╤В╨╛, ╨╗╨╛╤В╨╛╤Б╤Л, ╨╝╨░╨╜╨┤╨░╨╗╤Л, ╤И╨░╤Д╤А╨░╨╜": "Gold, lotuses, mandalas, saffron",
    "╨Ы╨░╨╖╤Г╤А╨╕╤В, ╨▒╨░╨╖╨░╨╗╤М╤В, ╨б╨╕╤А╨╕╤Г╤Б": "Lapis lazuli, basalt, Sirius star",
    "╨Ф╤А╨╡╨▓╨╛ ╨б╨╡╤Д╨╕╤А╨╛╤В, ╨╕╨▓╤А╨╕╤В╤Б╨║╨░╤П ╨▓╤П╨╖╤М": "Sephiroth Tree, Hebrew script",
    "╨Э╨╡╤Д╤А╨╕╤В, ╨╛╨▒╤Б╨╕╨┤╨╕╨░╨╜, ╨ж╨╛╨╗╤М╨║╨╕╨╜": "Jade, obsidian, Tzolkin calendar",
    "╨а╨╡╨╖╨╜╨╛╨╡ ╨┤╨╡╤А╨╡╨▓╨╛, ╨Я╤А╨░╨▓╨╕, ╨║╨╛╨╗╨╛╨▓╤А╨░╤В╤Л": "Carved wood, Prav realm, sun wheels",
    "╨Ь╨╛╤А╨╛╨╖╨╜╨╛╨╡ ╨╢╨╡╨╗╨╡╨╖╨╛, ╨Ш╨│╨│╨┤╤А╨░╤Б╨╕╨╗╤М": "Frost iron, Yggdrasil world tree",
    "╨Э╨╡╤Д╤А╨╕╤В, ╨║╨╕╨╜╨╛╨▓╨░╤А╤М, ╨Ш╨╜╤М-╨п╨╜": "Jade, cinnabar, Yin-Yang",
    "╨а╨░╨╖╨╛╤А╨▓╨░╨╜╨╜╤Л╨╡ ╤Ж╨╡╨┐╨╕, ╨╕╤Б╨║╤А╤Л": "Broken chains, divine sparks",
    "╨Ъ╨╕╨╜╤Ж╤Г╨│╨╕, ╨в╨╛╤А╨╕╨╕, ╨║╨░╨╝╨╕": "Kintsugi, torii gates, kami spirits",
    "╨Ш╨╖╤Г╨╝╤А╤Г╨┤, ╤Г╨╖╨╗╤Л ╨▓╨╡╤З╨╜╨╛╤Б╤В╨╕, ╨Р╨▓╨░╨╗╨╛╨╜": "Emerald, Celtic knots, Avalon",
    "╨Ъ╤А╨╕╤Б╤В╨░╨╗╤М╨╜╤Л╨╡ ╨▓╨╡╤А╤И╨╕╨╜╤Л, ╨Ъ╨░╨╗╨░╤З╨░╨║╤А╨░": "Crystal peaks, Kalachakra wheel",
    "╨Ч╨╛╨╗╨╛╤В╨░╤П ╤Б╨╝╨░╨╗╤М╤В╨░, ╨╝╨╛╨╖╨░╨╕╨║╨╕": "Golden smalto, Byzantine mosaics",
    "╨Ъ╨╛╤Б╤В╨╕, ╨┐╨╡╤А╤М╤П, ╨▒╤Г╨▒╨╡╨╜": "Bones, feathers, shaman drum",
    "╨Ф╨Э╨Ъ-╤Д╤А╨░╨║╤В╨░╨╗╤Л, ╤В╨╡╨╜╨╕-╨┤╨░╤А╤Л-╤Б╨╕╨┤╨┤╤Е╨╕": "DNA fractals, shadow-gift-siddhi",
    "╨Э╨╡╨╛╨╜╨╛╨▓╤Л╨╡ ╤А╤Г╨╜╤Л, ╨║╨╕╨▒╨╡╤А-╤Б╨░╨║╤А╨░╨╗╤М╨╜╨╛╤Б╤В╤М": "Neon runes, cyber-sacred",
    "╨Ч╨▓╤С╨╖╨┤╨╜╨░╤П ╨┐╤Л╨╗╤М, ╨║╨▓╨░╨╖╨░╤А╤Л": "Stardust, quasars",
    "╨Ь╤А╨░╨╝╨╛╤А, ╨▒╤А╨╛╨╜╨╖╨░, ╨╗╨░╨▓╤А": "Marble, bronze, laurel",
    "╨б╨▓╤П╤Й╨╡╨╜╨╜╤Л╨╣ ╨╛╨│╨╛╨╜╤М, ╨д╤А╨░╨▓╨░╤Е╨░╤А": "Sacred fire, Faravahar",
    "╨Э╤Г╤А, ╨║╨░╨╗╨╗╨╕╨│╤А╨░╤Д╨╕╤П, ╨Ъ╨░╨░╨▒╨░": "Nur light, calligraphy, Kaaba",
    "╨Ю╨▒╤Б╨╕╨┤╨╕╨░╨╜, ╨в╨╛╨╜╨░╨╗╤М╨┐╨╛╤Г╨░╨╗╨╗╨╕": "Obsidian, Tonalpohualli",
    "╨а╨╛╨╖╨░-╨Ъ╤А╨╡╤Б╤В, ╨У╤А╨░╨░╨╗╤М": "Rose Cross, Holy Grail",
    "╨Ъ╨░╤Г╤А╨╕, ╨▒╨░╤А╨░╨▒╨░╨╜╤Л ╨С╨░╤В╨░, ╨Ю╤А╨╕╤И╨░": "Cowrie shells, Bata drums, Orisha",
    "╨Ъ╨╗╨╕╨╜╨╛╨┐╨╕╤Б╤М, ╨╖╨╕╨║╨║╤Г╤А╨░╤В╤Л, ╨Р╨┐╤Б╤Г": "Cuneiform, ziggurats, Apsu",
    "╨Ш╨╖╤Г╨╝╤А╤Г╨┤╨╜╨░╤П ╨б╨║╤А╨╕╨╢╨░╨╗╤М, ╨░╤В╨░╨╜╨╛╤А": "Emerald Tablet, athanor furnace",
    "22 ╨б╤В╨░╤А╤И╨╕╤Е ╨Р╤А╨║╨░╨╜╨░": "22 Major Arcana",
    "╨Я╨╗╨░╨╜╨╡╤В╤Л, ╨┤╨╛╨╝╨░, ╤Н╤Д╨╡╨╝╨╡╤А╨╕╨┤╤Л": "Planets, houses, ephemeris",
    "64 ╨│╨╡╨║╤Б╨░╨│╤А╨░╨╝╨╝╤Л": "64 hexagrams",
    "╨б╨┐╨░╨╜╨┤╨░, ╨и╨╕╨▓╨░-╨и╨░╨║╤В╨╕, ╨▒╨╕╨╜╨┤╤Г": "Spanda, Shiva-Shakti, bindu",
    "╨б╤В╤Е╤Г╨┐╨░, ╨Ф╤Е╨░╤А╨╝╨░╨║╨░╨╣╤П, ╨╝╨░╨╜╨┤╨░╨╗╨░": "Stupa, Dharmakaya, mandala",
    "╨б╨╕╤А╨╕╤Г╤Б, ╨Э╨╛╨╝╨╝╨╛, ╤Б╨┐╨╕╤А╨░╨╗╨╕": "Sirius, Nommo, spirals",
    "╨Ъ╤А╨╕╤Б╤В╨░╨╗╨╗╤Л, ╨╛╨║╨╡╨░╨╜, ╤Б╨┐╤П╤Й╨╕╨╡ ╨│╨╛╤А╨╛╨┤╨░": "Crystals, ocean, sleeping cities",
    "╨Э╨╡╨╣╤А╨╛╤Б╨╡╤В╨╕, Source Light Kernel": "Neural nets, Source Light Kernel",
    "╨б╤Г╤И╤Г╨╝╨╜╨░, ╨│╤А╨░╨╜╤В╤Е╨╕, ╨С╤А╨░╤Е╨╝╨░╨╜╨┤╨░, ╨╗╨╛╤В╨╛╤Б-╤Б╨░╤Е╨░╤Б╤А╨░╤А╨░": "Sushumna, granthis, Brahmanda, Sahasrara lotus",
}

MATRIX_CULTURAL_STYLE = {
    "vedic": "Indian temple architecture, golden mandalas, lotus motifs, Vedic yantra patterns, Sanskrit sacred geometry, saffron and gold palette",
    "egyptian": "Egyptian temple columns, hieroglyphs, lapis lazuli and gold, scarab motifs, pyramidal geometry, Nile papyrus, Eye of Horus",
    "kabbalistic": "Tree of Life Sephiroth, Hebrew calligraphy, mystical blue-violet light, sacred geometry, Ein Sof emanations",
    "mayan": "jade and obsidian, feathered serpent Quetzalcoatl, jungle temple stepped pyramids, Tzolkin calendar glyphs, quetzal feathers",
    "slavic": "carved wooden architecture, Slavic embroidery patterns, birch forests, sacred fire, Sun wheel Kolovrat, Perun thunder symbols",
    "norse": "Viking rune stones, Yggdrasil world tree, frost and iron, Norse knotwork, aurora borealis, longship dragon prows",
    "daoist": "Chinese ink wash painting, jade and cinnabar, Yin-Yang symbol, mountain mist, bamboo, Tai Chi flowing energy",
    "gnostic": "broken chains of matter, divine light sparks in darkness, Pleroma radiance, ethereal aeons, cosmic egg, celestial spheres",
    "shinto": "Japanese torii gates, kintsugi gold repair, cherry blossoms, shimenawa sacred rope, kami spirit orbs, minimalist wabi-sabi",
    "celtic": "emerald green landscapes, Celtic knotwork, Avalon mists, druidic oak groves, spiral triskele, standing stones",
    "shambhala": "crystal mountain peaks, Kalachakra mandala, Tibetan thangka style, snow lion, dharma wheel, lotus throne",
    "julian_byzantine": "golden mosaic tesserae, Byzantine icon style, Hagia Sophia dome, sacred haloes, deep purple and gold",
    "shamanic": "animal bones and feathers, ritual drum, spirit animals, cave paintings, trance fire, shamanic journey visuals",
    "gene_keys": "DNA double helix fractals, shadow-gift-siddhi spectrum, holographic codes, bio-luminescent patterns",
    "technomagical": "neon rune circuits, cyber-sacred glyphs, holographic interfaces, digital mandalas, quantum code streams",
    "cosmic_galactic": "deep space nebulae, quasar light, galactic spiral arms, cosmic dust clouds, stellar nurseries, event horizons",
    "antique_greco_roman": "white marble columns, bronze statues, laurel wreaths, Greek temple pediments, amphora pottery, Olympic torches",
    "zoroastrian": "sacred eternal fire, Faravahar winged disk, Persian carpet patterns, Ahura Mazda light, cypress trees",
    "islamic_sufi_nur": "Arabic calligraphy, geometric arabesque patterns, Nur divine light, mosque dome and minaret, Kaaba, Sufi whirling",
    "aztec_mexica": "obsidian mirrors, Aztec sun stone, eagle warrior, Tonalpohualli calendar, sacrificial temple, jaguar motifs",
    "christian_mystical_grail": "Rose Cross, Holy Grail chalice, Gothic cathedral stained glass, Rosicrucian symbols, sacred heart radiance",
    "yoruba_ifa_orisha": "cowrie shells, Bata drums, Orisha beaded crowns, palm oil offerings, Ifa divination board, tropical sacred grove",
    "sumerian_babylonian": "cuneiform tablets, ziggurat stepped temples, Mesopotamian winged bulls lamassu, Ishtar gate blue tiles, Apsu primordial waters",
    "hermetic_alchemical": "Emerald Tablet, alchemical athanor furnace, philosopher's stone, Ouroboros serpent, Hermetic caduceus, nigredo-albedo-rubedo stages",
    "tarot_arcanic": "Tarot Major Arcana imagery, esoteric card borders, Rider-Waite symbolism, mystical divination symbols, fool's journey",
    "astrological": "zodiac wheel, planetary symbols, celestial ephemeris charts, horoscope houses, starry night dome",
    "chinese_iching": "I Ching hexagram lines, Chinese brush calligraphy, dragon and phoenix, trigram Ba Gua, flowing Qi energy",
    "tantric_kashmiri": "Shiva-Shakti union, spanda vibration waves, bindu point, kundalini serpent energy, tantric yantra",
    "buddhist_mahayana": "stupa monument, Dharmakaya golden Buddha, Mahayana mandala, bodhi tree, lotus sutra, compassion mudra",
    "afro_dogon": "Sirius star system, Nommo water spirits, Dogon spiral cosmology, African mask patterns, ancestral totems",
    "atlantean_lemurian": "submerged crystal cities, underwater temples, bioluminescent ocean, ancient crystalline technology, lost civilization ruins",
    "posthuman_ai_sophianic": "neural network patterns, AI consciousness nodes, Sophia divine wisdom circuits, digital light kernel, posthuman evolution",
    "advaita_siddha": "Sushumna central channel, granthis energy knots, Brahmananda cosmic egg, Sahasrara thousand-petal lotus, non-dual light",
}

STYLE_BASE = (
    "digital painting, card art, mystical esoteric style, "
    "ornate border frame, portrait orientation, "
    "highly detailed, 4k, atmospheric lighting"
)


def load_json(name):
    with open(os.path.join(DATA, name), "r", encoding="utf-8") as f:
        return json.load(f)


def transliterate_to_en(text):
    """Basic cleanup: keep Latin chars, transliterate common patterns."""
    if not text:
        return text
    result = text
    result = result.replace("╤С", "yo").replace("╨Б", "Yo")
    return result


def parse_lorebook_all(filepath):
    """Parse a lorebook and extract all agent blocks indexed by agent name."""
    if not os.path.exists(filepath):
        return {}

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    results = {}
    pattern = re.compile(
        r'(\d{1,2})\.\s+'
        r'(\S[^\n]*?)\s*->\s*'
        r'([^\n]+)\n'
        r'(.*?)(?=\n\d{1,2}\.\s+\S[^\n]*?\s*->|\Z)',
        re.DOTALL,
    )

    for m in pattern.finditer(text):
        awara_name = m.group(2).strip()
        cultural = m.group(3).strip()
        block = m.group(4)

        entry = {"cultural_full": cultural}

        domain_m = re.search(
            r"(?:╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨Ф╨╛╨╝╨╡╨╜╨░|Domain)[:\s]*([^\n]+)", block
        )
        if domain_m:
            entry["domain_cultural"] = domain_m.group(1).strip()

        artifact_m = re.search(
            r"╨Р╤А╤В╨╡╤Д╨░╨║╤В[^:]*?:\s*([^\n]+)", block
        )
        if artifact_m:
            entry["artifact"] = artifact_m.group(1).strip()

        essence_m = re.search(
            r"╨н╨╖╨╛╤В╨╡╤А╨╕╤З╨╡╤Б╨║╨░╤П ╤Б╤Г╤В╤М[:\s]*([^\n]+)", block
        )
        if essence_m:
            entry["essence"] = essence_m.group(1).strip()[:250]

        results[awara_name] = entry

    return results


def extract_en_parts(text):
    """Extract Latin-script words/names from a mixed Cyrillic/Latin string."""
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    latin = r"A-Za-z\xc0-\xff\u0100-\u017e\u1e00-\u1eff"
    parts = re.findall(
        rf"[{latin}][{latin}0-9\-'\s/\.]*",
        text,
    )
    cleaned = []
    for p in parts:
        p = p.strip().rstrip(".-,")
        if len(p) > 2 and p.upper() != "AWARA" and not p.isspace():
            cleaned.append(p)
    result = ", ".join(cleaned)
    result = re.sub(r"\s*,\s*,+", ",", result)
    result = re.sub(r",\s*$", "", result)
    result = re.sub(r"\s+,", ",", result)
    result = re.sub(r",\s+", ", ", result)
    return result.strip()


def clean_artifact(art):
    """Clean artifact string: remove prefix, keep only Latin names for English prompt."""
    for prefix in ["╨Ъ╨╗╤О╤З:", "/ ╨Ъ╨╗╤О╤З:"]:
        if art.startswith(prefix):
            art = art[len(prefix):].strip()
    art = art.rstrip(".")
    en_parts = extract_en_parts(art)
    if en_parts and len(en_parts) > 3:
        if len(en_parts) > 100:
            en_parts = en_parts[:100].rsplit(",", 1)[0]
        return en_parts
    return ""


def clean_essence(ess):
    """Extract Latin deity/concept names from essence for English prompt."""
    ess = ess.rstrip(".")
    en_parts = extract_en_parts(ess)
    if en_parts and len(en_parts) > 10:
        if len(en_parts) > 100:
            en_parts = en_parts[:100].rsplit(",", 1)[0]
        return en_parts
    return ""


def get_rarity(agent_slug, matrix_slug):
    score = AGENT_POWER[agent_slug] + MATRIX_DEPTH[matrix_slug]
    if score <= 3:
        return "common"
    if score <= 5:
        return "uncommon"
    if score == 6:
        return "rare"
    if score <= 8:
        return "epic"
    return "legendary"


def build_prompts():
    agents = load_json("agents.json")
    matrices = load_json("matrices.json")
    agent_map = load_json("agent_matrix_map.json")
    iconography = load_json("iconography.json")

    agents_by_id = {a["id"]: a for a in agents}
    matrices_by_id = {m["id"]: m for m in matrices}

    lore_cache = {}

    prompts = []

    for entry in agent_map:
        agent = agents_by_id.get(entry["agent_id"])
        matrix = matrices_by_id.get(entry["matrix_id"])
        if not agent or not matrix:
            continue

        element_ru = agent.get("element", "╨н╤Д╨╕╤А")
        guna = agent.get("guna", "╤Б╨░╤В╤В╨▓╨░")
        cultural_name = entry.get("cultural_name", agent["name"])
        visual_code_ru = matrix.get("visual_code", "")
        matrix_slug = matrix["slug"]

        element_en = ELEMENT_EN.get(element_ru, "Ether")
        element_vis = ELEMENT_VISUALS.get(element_en, ELEMENT_VISUALS["Ether"])
        guna_vis = GUNA_STYLE.get(guna, GUNA_STYLE["╤Б╨░╤В╤В╨▓╨░"])
        culture_vis = MATRIX_CULTURAL_STYLE.get(matrix_slug, "")
        visual_code_en = VISUAL_CODE_EN.get(visual_code_ru, visual_code_ru)
        agent_en = AGENT_NAME_EN.get(agent["name"], agent["name"])
        matrix_en = MATRIX_NAME_EN.get(matrix["name"], matrix["name"])
        domain_en = DOMAIN_EN.get(agent["domain"], agent["domain"])

        icon_desc = iconography.get(cultural_name, "")

        source_file = matrix.get("source_file", "")
        if source_file not in lore_cache:
            if source_file:
                lore_path = os.path.join(LORE, source_file)
                lore_cache[source_file] = parse_lorebook_all(lore_path)
            else:
                lore_cache[source_file] = {}
        lore_all = lore_cache[source_file]

        lore = lore_all.get(agent["name"], {})

        domain_str = ""
        if lore.get("domain_cultural"):
            dom = lore["domain_cultural"].rstrip(".")
            dom_en = extract_en_parts(dom)
            if dom_en and len(dom_en) > 3:
                domain_str = f" Sacred domain: {dom_en}."

        artifact_str = ""
        if not icon_desc and lore.get("artifact"):
            art = clean_artifact(lore["artifact"])
            if art:
                artifact_str = f" Holding sacred artifact: {art}."

        archetype = AGENT_ARCHETYPE.get(agent["name"], "")

        if icon_desc:
            prompt = (
                f"A mystical tarot-style card depicting {icon_desc}. "
                f"{matrix_en} tradition. "
                f"Element: {element_en} тАФ {element_vis}. "
                f"Setting: {culture_vis}. "
                f"Mood: {guna_vis}. "
                f"{STYLE_BASE}"
            )
        elif archetype:
            prompt = (
                f"A mystical tarot-style card depicting {archetype}, "
                f"reimagined as {cultural_name} in the {matrix_en} tradition. "
                f"{domain_str}{artifact_str} "
                f"Element: {element_en} тАФ {element_vis}. "
                f"Setting: {culture_vis}. "
                f"Mood: {guna_vis}. "
                f"{STYLE_BASE}"
            )
        else:
            prompt = (
                f"A mystical card depicting {cultural_name}, "
                f"the {matrix_en} manifestation of cosmic agent {agent_en}. "
                f"Realm: {domain_en}.{domain_str}{artifact_str} "
                f"Element of power: {element_en} тАФ {element_vis}. "
                f"Cultural visual style: {culture_vis}. "
                f"Symbolic motifs: {visual_code_en}. "
                f"Atmosphere: {guna_vis}. "
                f"{STYLE_BASE}"
            )

        negative = (
            "text, watermark, signature, blurry, low quality, "
            "modern clothing, photography, realistic face, "
            "deformed, ugly, nsfw"
        )

        card_id = f"{agent['slug']}__{matrix['slug']}"
        rarity = get_rarity(agent["slug"], matrix["slug"])

        prompts.append({
            "card_id": card_id,
            "rarity": rarity,
            "agent_slug": agent["slug"],
            "agent_name": agent["name"],
            "matrix_slug": matrix["slug"],
            "matrix_name": matrix["name"],
            "cultural_name": cultural_name,
            "element": element_ru,
            "domain": agent["domain"],
            "domain_cultural": lore.get("domain_cultural", ""),
            "artifact": lore.get("artifact", ""),
            "prompt": prompt,
            "negative_prompt": negative,
            "image_path": f"cards/{card_id}.webp",
        })

    return prompts


def main():
    prompts = build_prompts()
    out_path = os.path.join(DATA, "card_prompts.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

    enriched = sum(1 for p in prompts if p.get("domain_cultural"))
    print(f"Generated {len(prompts)} card prompts -> {out_path}")
    print(f"  Enriched with lorebook data: {enriched}")
    print(f"  Without lorebook data: {len(prompts) - enriched}")


if __name__ == "__main__":
    main()
