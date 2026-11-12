# Ayutthaya Civilization for Civilization VII (อาณาจักรอยุธยา)

Ayutthaya, the river capital of the Thai kingdom (1351-1767), as an Exploration Age civilization. It fills
the gap in the game's Thai line: Khmer (Antiquity) → **Ayutthaya** (Exploration) → Siam (Modern).

อาณาจักรอยุธยาเป็นอารยธรรมยุคแห่งการสำรวจ เชื่อมเส้นทาง ขอม → อยุธยา → สยาม ข้อความเป็นภาษาอังกฤษ
และจะเป็นภาษาไทยเมื่อเปิดม็อด Thai Language Pack ด้วย

## What it adds

| | |
|---|---|
| **Ability: Venice of the East** | +1 Food on Navigable River tiles (river prawns). +3 Gold on Bazaars in Settlements with a Navigable River (floating markets). Antiquity and Modern versions for "allow across time" games. |
| **Unique quarter: Wat** | Ubosot (+6 Happiness) and Prang (+6 Culture), each +1 next to a Navigable River or Wonder. Built together in one district: +4 Science, +2 Culture (the wat was the village school). |
| **Bang Rachan Villager** | Replaces the Swordsman line (35/40/45). +5 Combat Strength inside your own territory. |
| **Thammathut** | Replaces the Missionary. +25 Science per settlement converted. Honours the 1753 mission that founded the Siam Nikaya in Sri Lanka. |
| **Civic tree** | Khlong, Sangha, Krung Si: traditions River Prawns, Temple Schools, Phra Khlang Sinkha; +1 settlement cap. |
| **Narrative** | The Legend of Bang Rachan; The Floating Market at Wat Doem. |
| **Unlocks** | Play as Khmer, or found 3 settlements on Navigable Rivers in Antiquity. Ayutthaya unlocks Siam. |
| **Wonder** | Wat Xieng Thong is the associated wonder when the Asia wonders DLC is enabled. |

Numbers follow the official civilizations (unique buildings +6, unique units at base strength plus a
conditional bonus). Design and sources: [`docs/superpowers/specs/2026-11-12-ayutthaya-design.md`](../docs/superpowers/specs/2026-11-12-ayutthaya-design.md).

## Known limits (v1)

- The Ubosot and Prang have **no 3D model yet**: the game's visual remaps work for units but not for new
  building types, and new art packages can only be built with Firaxis' Windows-only Development Tools.
- The civilization-details screen background stays dark for the same reason (it is a packed 3D texture).
  The civ card and setup hub show the mod's own panel art.

## Build (macOS)

```sh
pip install -r ../thai-language/tools/requirements.txt pillow
python3 tools/make_panel.py                 # panel art (original, drawn by the script)
LTH_PYTHON=python3 tools/install.sh         # gate, generate text, copy into the Mods folder
```

`tools/build.py` is the gate: both languages present, markup identical, every LOC key and LTH type
defined, the modinfo lists exactly the files on disk.
