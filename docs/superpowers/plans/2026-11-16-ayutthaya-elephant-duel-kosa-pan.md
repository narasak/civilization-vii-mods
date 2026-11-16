# Ayutthaya: Elephant Duel, Kosa Pan, Building Models — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add stories 03 (Yutthahatthi) and 04 (embassy to Versailles), the royal war elephant they grant, and then try an art package that gives the Ubosot and the Prang existing game models.

**Architecture:** Data-only additions, following the existing story 01/02 and unit patterns in `ayutthaya/data/`. All text goes through `text/strings.txt` and `tools/build.py`. Part 2 is a separate experiment with a stop rule.

**Tech Stack:** Civ VII database XML and GameEffects XML; Python 3 (build gate, icon drawing, .blp writer); the UIScript JS portrait helper.

**Spec:** `docs/superpowers/specs/2026-11-16-ayutthaya-elephant-duel-kosa-pan-design.md`

## Global Constraints

- No new 3D models. Use only models in the base game or a DLC.
- Every string goes in English and Thai in `text/strings.txt`, and `tools/build.py` must report 0 findings.
- Never copy code from Smayo's Civ7 Art Studio (no licence), and never run `civart.exe`.
- The elephant is granted only by story 03: `CanTrain="false"`, `CanPurchase="false"`, no `Unit_Costs` row.
- Types are prefixed `LTH_`, and the build gate checks every LTH type has a `<Types>` row.

## Review Focus

- The elephant appears in a city's production or purchase list → it must not (checked in game, Task 3).
- Story 03 fires while the player is at peace → the requirement set includes `HAS_X_WARS` Amount 1.
- The elephant shows an empty portrait or a black flag → add it to the portrait map and give it its own flag icon.
- A non-Ayutthaya player gets the stories → both requirement sets include `REQ_STORY_CIVILIZATION_LTH_AYUTTHAYA`.
- The Thai text breaks the Thai pack's font rules → the build gate's check 2 covers this.

---

### Task 1: The royal war elephant `UNIT_LTH_CHANG_SONG`

**Files:** modify `ayutthaya/data/units.xml`, `ayutthaya/data/visual-remaps.xml`, `ayutthaya/data/icons/icons.xml`, `ayutthaya/ui/lth-ayu-portrait.js`, `ayutthaya/tools/make_icons.py`, `ayutthaya/text/strings.txt`, `ayutthaya/ayutthaya.modinfo`; create `ayutthaya/icons/unitflag_lth_chang_song.png`

**Produces:** unit class tag `UNIT_CLASS_LTH_CHANG_SONG`, used by Task 2's grant.

- [x] Add rows to `units.xml`:
  - `Units`: `Tier="2" Maintenance="0" BaseSightRange="2" BaseMoves="2"`, mounted, land combat, `CanTrain="false" CanPurchase="false"`, `TraitType="TRAIT_LTH_AYUTTHAYA"`.
  - `Unit_Stats`: Combat 50.
  - `TypeTags`: COMBAT, MELEE (or the cavalry class the knight uses), UNIQUE, `UNIT_CLASS_LTH_CHANG_SONG`.
  - `Unit_Advisories`: military.
- [x] Remap the unit to `UNIT_DANTINAS_TATHA` in `visual-remaps.xml`.
- [x] Draw an elephant silhouette flag with `make_icons.py` (`chang_song()`), add it to `icons.xml` and to the modinfo `ImportFiles`.
- [x] Add `UNIT_LTH_CHANG_SONG: 'UNIT_DANTINAS_TATHA'` to `LTH_AYU_PORTRAIT_MODEL`.
- [x] Add strings: `LOC_UNIT_LTH_CHANG_SONG_NAME` ("Royal War Elephant" / "ช้างทรง"), `_DESCRIPTION`, `LOC_REMAP_LTH_CHANG_SONG`.
- [x] Run `python3 tools/build.py --check`. Expected: 0 findings.

### Task 2: Stories 03 and 04

**Files:** modify `ayutthaya/data/narrative-stories.xml`, `ayutthaya/data/narrative-stories-gameeffects.xml`, `ayutthaya/text/strings.txt`

**Consumes:** `UNIT_CLASS_LTH_CHANG_SONG`.

- [x] Add 03A/B/C and 04A/B/C rows to every table that 01/02 use: Types, NarrativeStories, Rewards, Story_Rewards, RewardIcons (03B UNIT, 03C YIELD_CULTURE, 04B YIELD_DIPLOMACY, 04C YIELD_SCIENCE), TextReplacements and Links.
- [x] Requirement sets:
  - `REQSET_LTH_AYU_03A_NARRATIVE` = civ check + `REQUIREMENT_PLAYER_HAS_X_WARS` (Amount 1) + `REQUIREMENT_PLAYER_HAS_COMMANDERS_WITH_X_LEVELS` (LevelCount 2, CommanderCount 1).
  - `REQSET_LTH_AYU_04A_NARRATIVE` = civ check + `REQUIREMENT_PLAYER_MET_NUM_CIVS` (Amount 3).
- [x] Modifiers:
  - 03B: `EFFECT_CITY_GRANT_UNIT` on the capital, UnitTag `UNIT_CLASS_LTH_CHANG_SONG`, run-once.
  - 03C, 04B, 04C: `EFFECT_PLAYER_GRANT_YIELD_NARRATIVE` with `REWARD_TYPE_MEDIUM_EARLY`.
- [x] Add strings for STORYTITLE, NAME, DESCRIPTION and COMPLETION on 03A–04C, with history as in the spec.
- [x] Run `python3 tools/build.py --check`. Expected: 0 findings.
- [x] Commit Tasks 1 and 2 together.

### Task 3: Install and test in game (the owner plays)

- [x] Run `LTH_PYTHON=<venv python> tools/install.sh`. Expected: `installed -> …/Mods/lth-ayutthaya`.
- [ ] (story 04 not yet seen in game; story 03 and the elephant verified 2026-11-16) The owner plays. Story 04 should fire after meeting 3 civilizations. Story 03 should fire when at war with a level-2 commander. Check that choice 03B gives an elephant with the elephant model, a portrait and a flag, and that the elephant appears in no build or buy list.
- [x] Read `UI.log`, `Database.log` and `Modding.log`. Expected: no LTH errors.

### Task 4 (Part 2): Building-model art package experiment

- [x] (replaced by a cheaper first test: a renamed copy of a small DLC package inside the mod; no writer was built) Write `ayutthaya/tools/blp/` (our own `.blp` writer) and generate a package with two `BIN_Hero_Building_Footprint` rows: `BUILDING_LTH_UBOSOT` → the Vihara asset, `BUILDING_LTH_PRANG` → the Meru asset. Add `<UpdateArt>` to the modinfo.
- [x] Install it, have the owner start a game, and read `ArtDef.log`.
- [x] (FIRED 2026-11-16: `No Packages found`; Part 2 dropped, building remaps removed) Stop rule: "No Packages found", or no models, means drop Part 2 and report back.
