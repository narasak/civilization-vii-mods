# Thai Language for Civilization VII (ม็อดภาษาไทย)

แปลข้อความในเกม Civilization VII เป็นภาษาไทยทั้งหมด: เมนู คำแนะนำ ซีวิโลพีเดีย เหตุการณ์เรื่องราว
บทสนทนาผู้นำ ทั้งเกมหลัก 3 ยุค และ DLC ทุกตัว พร้อมฟอนต์ไทย (Sarabun, Kanit) ในตัว

Translates the whole game into Thai. Thai is not a selectable language in Civ VII, so the mod replaces the
English text: keep the game language on English.

## Status

- 46,593 of 46,622 game strings translated (99.94%); the rest are empty strings and English grammar helpers.
- Published on the Steam Workshop (public since 2026-11-06). Machine-assisted, checked by tooling and tested in game. Reports welcome.
- Tested on Civilization VII 1.5.0, macOS.

## Install

- **Steam Workshop:** [subscribe to Thai Language Pack - ภาษาไทย](https://steamcommunity.com/sharedfiles/filedetails/?id=3834574849).
- **Manual:** download `thai-language-pack-v<N>.zip` from [Releases](https://github.com/narasak/civilization-vii-mods/releases) and unzip it into your Mods folder
  (macOS `~/Library/Application Support/Civilization VII/Mods/`, Windows `%LOCALAPPDATA%\Firaxis Games\Sid Meier's Civilization VII\Mods\`).

Then enable "Thai Language Pack" under Add-Ons.

### Build from source (macOS)


```sh
pip install -r tools/requirements.txt          # fonttools, pythainlp, defusedxml
python3 tools/extract.py                       # read the game's English text into work/catalog.jsonl
LTH_PYTHON=python3 tools/install.sh            # build text, run every check, copy into the Mods folder
```

`install.sh` reads the game's own text from your installation to place each translation; it refuses to
install if any check fails. `tools/package.sh` builds the release zip from the same gated build.

## How it works

- `translations/<module>.jsonl`: one row per game string: tag, a hash of the English it translates, Thai.
  A changed English string no longer matches its hash, so a game update cannot silently show stale Thai.
- `tools/build_text.py` writes `text/gen/*.xml`, putting each row under the same load condition (Age,
  shell or game) as the English it replaces, and inserting word-break points for Thai line wrapping.
- `ui/lth-thai-fonts.js` and an early stylesheet give every game font stack a Thai fallback, from the
  loading screen on.
- `tools/check.py` is the gate: placeholders and markup preserved, characters the fonts can draw, no
  stray spaces around links, every game font rule covered.
- `glossary/`: translation policy, approved terms, and the brief every translator follows.

## Not in this repository

The game's English text and anything generated from it (`work/`, `glossary/names.tsv`, `text/gen/`).
They are rebuilt locally from your installed game.
