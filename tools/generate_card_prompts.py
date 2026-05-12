#!/usr/bin/env python3
"""
T-037: Generate image-generation prompts for all AWARA cards.

Reads agents.json, matrices.json, agent_matrix_map.json + lorebook texts.
Extracts cultural domain names, artifacts, esoteric descriptions from lorebooks.
Outputs data/card_prompts.json with enriched prompts for each card.

Usage:
    python tools/generate_card_prompts.py
"""

import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
LORE = os.path.join(BASE, "lore", "text")

ELEMENT_VISUALS = {
    "Огонь": "flames, embers, molten gold, solar corona, radiant heat haze",
    "Вода": "flowing water, moonlit waves, deep ocean currents, mist, rain drops",
    "Земля": "ancient stone, roots, crystals, mountain peaks, terracotta, fertile soil",
    "Воздух": "swirling winds, feathers, clouds, translucent veils, breath of light",
    "Эфир": "starfield, cosmic nebula, fractal geometry, iridescent void, quantum light",
}

GUNA_STYLE = {
    "саттва": "serene, luminous, harmonious, balanced light, ethereal glow",
    "раджас": "dynamic, passionate, energetic, vivid contrasts, motion blur",
    "тамас": "mysterious, deep, shadowy, ancient, cosmic darkness with pinpoints of light",
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


def parse_lorebook(filepath, agent_name):
    """Extract domain name, artifact, and esoteric essence for a given agent."""
    if not os.path.exists(filepath):
        return {}

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    result = {}

    agent_patterns = [
        agent_name,
        agent_name.replace("Свет Ра", "Свет Ра"),
    ]

    for pattern in agent_patterns:
        idx = text.find(pattern)
        if idx == -1:
            continue

        block = text[max(0, idx - 200):idx + 2000]

        domain_match = re.search(
            r"(?:Название Домена|Domain|Домен)[:\s]*([^\n]+)", block
        )
        if domain_match:
            result["domain_cultural"] = domain_match.group(1).strip()

        artifact_match = re.search(
            r"(?:Артефакт|Artifact|Ключ)[:\s]*([^\n]+)", block
        )
        if artifact_match:
            result["artifact"] = artifact_match.group(1).strip()

        essence_match = re.search(
            r"(?:Эзотерическая суть|Esoteric)[:\s]*([^\n.]+\.(?:[^\n.]+\.)?)",
            block,
        )
        if essence_match:
            result["essence"] = essence_match.group(1).strip()[:200]

        if result:
            break

    return result


def build_prompts():
    agents = load_json("agents.json")
    matrices = load_json("matrices.json")
    agent_map = load_json("agent_matrix_map.json")

    agents_by_id = {a["id"]: a for a in agents}
    matrices_by_id = {m["id"]: m for m in matrices}

    lore_cache = {}

    prompts = []

    for entry in agent_map:
        agent = agents_by_id.get(entry["agent_id"])
        matrix = matrices_by_id.get(entry["matrix_id"])
        if not agent or not matrix:
            continue

        element = agent.get("element", "Эфир")
        guna = agent.get("guna", "саттва")
        cultural_name = entry.get("cultural_name", agent["name"])
        visual_code = matrix.get("visual_code", "")
        matrix_slug = matrix["slug"]

        element_vis = ELEMENT_VISUALS.get(element, ELEMENT_VISUALS["Эфир"])
        guna_vis = GUNA_STYLE.get(guna, GUNA_STYLE["саттва"])
        culture_vis = MATRIX_CULTURAL_STYLE.get(matrix_slug, "")

        source_file = matrix.get("source_file", "")
        lore_key = f"{source_file}__{agent['name']}"
        if lore_key not in lore_cache:
            if source_file:
                lore_path = os.path.join(LORE, source_file)
                lore_cache[lore_key] = parse_lorebook(lore_path, agent["name"])
            else:
                lore_cache[lore_key] = {}
        lore = lore_cache[lore_key]

        domain_str = ""
        if lore.get("domain_cultural"):
            domain_str = f" Sacred domain: {lore['domain_cultural']}."

        artifact_str = ""
        if lore.get("artifact"):
            artifact_str = f" Key artifact: {lore['artifact']}."

        essence_str = ""
        if lore.get("essence"):
            essence_str = f" {lore['essence']}"

        prompt = (
            f"A mystical card depicting {cultural_name}, "
            f"manifestation of {agent['name']} in the {matrix['name']} tradition. "
            f"Domain: {agent['domain']}.{domain_str}{artifact_str}{essence_str} "
            f"Element: {element} — {element_vis}. "
            f"Cultural setting: {culture_vis}. "
            f"Visual motifs: {visual_code}. "
            f"Mood: {guna_vis}. "
            f"{STYLE_BASE}"
        )

        negative = (
            "text, watermark, signature, blurry, low quality, "
            "modern clothing, photography, realistic face, "
            "deformed, ugly, nsfw"
        )

        card_id = f"{agent['slug']}__{matrix['slug']}"

        prompts.append({
            "card_id": card_id,
            "agent_slug": agent["slug"],
            "agent_name": agent["name"],
            "matrix_slug": matrix["slug"],
            "matrix_name": matrix["name"],
            "cultural_name": cultural_name,
            "element": element,
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
