# Ayutthaya: the Elephant Duel and the Embassy to Versailles

Date: 2026-11-16. Mod: `ayutthaya/` (`lth-ayutthaya`). Extends the 2026-11-12 Ayutthaya design.

## Intent

The owner wants the player to feel Ayutthaya's **greatness and courage**. Each feeling gets one story:

- **Courage: Yutthahatthi (the elephant duel), 1592 (B.E. 2135).** King Naresuan, mounted on the war
  elephant Chao Phraya Chaiyanuphap, challenged the Burmese crown prince Mingyi Swa to single combat at
  Nong Sarai and won. (Thai tradition dates it 1592; some historians date it 1593. The text says
  "1592" for consistency with the B.E. 2135 date Thai readers know.)
- **Greatness: Kosa Pan's embassy to Versailles, 1686 (B.E. 2229).** King Narai sent an embassy led by
  Kosa Pan (Ok-phra Wisut Sunthon) to Louis XIV. It reached Brest in June 1686, and Louis XIV received
  it at Versailles on 1 September 1686. The French court was dazzled.

The audience is foreign players meeting Ayutthaya. History is the foundation; the mechanics should tell
the story without the player reading a footnote.

## Goals, non-goals, anti-goals

- Goals: two new Exploration Age stories in the same shape as stories 01 and 02 (a prompt and two
  choices). The courage story can grant a **royal war elephant**, a unique hero unit the player sees on
  the map.
- Non-goals: no new 3D models (owner decision: only use models already in the game or a DLC); no
  multi-step story chains; no story about the fall of Ayutthaya in 1767 (a defeat does not fit
  "greatness and courage"; it may come later as a story about recovery).
- Anti-goals: the elephant must not be trainable, and must not become a third unique unit the civ
  builds. It must not be so strong that it makes wars trivial. The text must not misstate history, and
  it must not portray Burma or France as villains.

## Approaches

| | Approach | Trade-off |
|---|---|---|
| A | Two stories with only yield rewards | Fast, but the greatness stays on paper |
| **B (picked)** | **A, plus a royal war elephant granted by the courage story** | **Courage becomes visible on the map; one extra unit definition** |
| C | Multi-step chains (Kosa Pan's journey in 3 stories) | About twice the work, and the game's story pacing may break the chain apart |

The owner picked B on 2026-11-16 ("ตามที่แนะนำครับ").

## Design

### Story 03: Yutthahatthi

- When it fires: the player is Ayutthaya, is at war (`REQUIREMENT_PLAYER_HAS_X_WARS`, 1), and has a
  commander with at least 2 levels (`REQUIREMENT_PLAYER_HAS_COMMANDERS_WITH_X_LEVELS`). Both
  requirement types are used by the base game.
- Prompt: an enemy prince challenges your general to single combat on elephant-back.
- Choice B, "Ride out and accept the duel": grants one royal war elephant in the capital
  (`EFFECT_CITY_GRANT_UNIT` by unit class, the pattern story 01B already uses).
- Choice C, "Raise a chedi for victory": a culture reward, `REWARD_TYPE_MEDIUM_EARLY`. Naresuan is
  traditionally linked with Wat Yai Chai Mongkhon's great chedi.

### Story 04: The embassy to Versailles

- When it fires: the player is Ayutthaya and has met at least 3 other civilisations
  (`REQUIREMENT_PLAYER_MET_NUM_CIVS`). This captures Ayutthaya as an open, cosmopolitan court.
- Prompt: a distant king sends gifts and asks for an embassy; Kosa Pan offers to lead it.
- Choice B, "Send the embassy with royal gifts": an influence (diplomacy) reward.
- Choice C, "Bring back the knowledge of the West": a science reward.

### The royal war elephant (`UNIT_LTH_CHANG_SONG`)

- Display name: "Royal War Elephant" / "ช้างทรง". The description names Chao Phraya Chaiyanuphap.
- Art: borrows the Khmer war elephant `UNIT_DANTINAS_TATHA` (base game, so every player has it)
  through `visual-remaps.xml`. The Bang Rachan unit already proves that unit remaps work, including a
  remap to an Antiquity unit inside the Exploration Age.
- Role: Exploration Age mounted melee. Proposed stats: combat 50, 2 moves, sight 2 (knight: 45 combat,
  3 moves). Slower but stronger, like an elephant.
- Not trainable: it is only granted by story 03, has no production cost row, and appears in no build
  list.
- Maintenance: proposed 0, because it is a gift of the court.

### Text

All new strings go in `text/strings.txt` in both English and Thai, then through the existing text
generator and quality gate.

## Part 2: show models for the Ubosot and the Prang (experiment)

The owner asked on 2026-11-16 for the missing building models to be fixed too. The constraint still
holds: use models already in the game, and make no new ones.

- What we know: unit remaps work, but building remaps in `visual-remaps.xml` do nothing. Which model a
  building uses lives on the art side, in the table `BIN_Hero_Building_Footprint` inside the game's
  packed `.blp` files. The base game ships `BIN_Vihara_Scaled <= [BUILDING:BUILDING_VIHARA]`, with Meru
  done the same way.
- Plan: build a small art package that adds two rows pointing our buildings at existing assets:
  `BUILDING_LTH_UBOSOT` → the Vihara asset and `BUILDING_LTH_PRANG` → the Meru asset. It needs a
  BinModifier, a `ROOT_ASSET_BIN_MODIFIERS_<group>` list, a `<group>.dep`, and `<UpdateArt>` in the
  modinfo, with the Mac files under `Platforms/Mac`.
- Our own tool: we write the `.blp` writer ourselves in Python from the format as we understand it.
  Smayo's Civ7 Art Studio has no licence, so we may learn from it but must not copy its code.
- Unknown, and the first thing to test: the tool's author says the game loads art only from its DLC
  folder. If that is true, the package cannot ship through the Workshop. The test is to place the
  package in the Mods folder, start a game, and read `ArtDef.log`. A "No Packages found" line, or no
  models, means stop and report back.
- Stop rule: if the first test shows the game ignores art from Mods, we drop Part 2 and keep the
  buildings as they are. We do not pursue a DLC-folder install, because players could not get it from
  the Workshop.

Order: Part 1 (the stories and the elephant) first, then Part 2. They are independent, so a failure in
Part 2 does not hold back Part 1.

## Left to the builder

- How to make the unit impossible to train in this game version (no cost row, or a column the game
  offers), verified in game.
- What the elephant does at the Age transition.
- The exact requirement arguments for the war, commander-level and met-civs checks, copied from base
  game uses.
- Whether an influence reward exists as a narrative yield (`YIELD_DIPLOMACY`); if not, gold.
- In-game test: both stories fire, both choices pay out, the elephant shows the elephant model and the
  portrait helper shows its portrait (add it to `LTH_AYU_PORTRAIT_MODEL`), and the logs are clean.
