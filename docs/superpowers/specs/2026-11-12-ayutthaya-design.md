# Ayutthaya civilization (Exploration Age) — design

Approved in chat by the owner, 2026-11-12 ("ทำได้เลยครับ ขอให้สนุกและโดดเด่น และเป็นอยุธยา").

## Intent

Let foreign players meet Ayutthaya through play, and make it fun. History is the foundation, not the
headline. Mechanics should tell the story on their own: a city on the water, the wat at the centre of
community life, and Bang Rachan as the moment players remember.

- Centrepiece (owner's choice): **the wat**.
- Supporting pillars: river prawns (river abundance), floating markets (river trade), Bang Rachan.
- Fills the gap in the game's Thai line: Khmer (Antiquity) → **Ayutthaya** (Exploration) → Siam (Modern).

## Goals / non-goals / anti-goals

- Goal: an Exploration civ built exactly like Firaxis' own (Đại Việt / Majapahit layout), numbers in
  line with official civs, English as the primary text, Thai when the Thai Language Pack is active.
- Non-goals (v1): a leader, a new wonder, new 3D art. Art is borrowed through the game's own systems.
- Anti-goals: anything a Thai player would find disrespectful (Buddha images as icons or as things to
  destroy or trade; royal caricature; a monk who fights); "evil Burmese" framing (enemies stay generic);
  presenting legend or Rattanakosin-era things as Ayutthaya-era fact.

## Prior art (research 2026-11-12)

Hellpanda's Ayutthaya (CivFanatics, unmaintained) and Sukritact's Civ VI Siam both used Floating Market
improvement + Chang Suek elephant. We do neither: the market is part of the ability, and our uniques are
the wat, the Thammathut monk and the Bang Rachan villagers, which nobody has done.

## Mechanics (as built; numbers follow official civs)

| Piece | Official pattern | Ayutthaya |
|---|---|---|
| Ability "Venice of the East" | Majapahit, Đại Việt | +1 Food on Navigable River tiles (river prawns). Bazaars in settlements on a Navigable River +3 Gold (floating markets). |
| Unique quarter: **Wat** | Majapahit Pura (2 × 290-cost buildings, +6 base yield) | **Ubosot** +6 Happiness, +1 Happiness per adjacent Navigable River. **Prang** +6 Culture, +1 Culture per adjacent Navigable River. Quarter: +4 Science, +2 Culture in that settlement (the wat as village school). |
| Unique unit: **Bang Rachan Villagers** | Leiomano (replaces Swordsman line, 35/40/45) | Replaces Swordsman / Man-at-Arms / Pikeman, 35/40/45, standard cost. +5 Combat Strength inside your own territory. |
| Unique civilian: **Thammathut** (Dhamma envoy) | Majapahit Pedanda (replaces Missionary) | Replaces Missionary. +25 Science each time it converts a settlement. Monk, never a combatant. |
| Civic tree (3 nodes: 800 / 800 / 1200) | Majapahit | Khlong (canals) → Ubosot + tradition *River Prawns* (+1 Gold on Navigable River tiles). Sangha → Prang + tradition *Temple Schools* (Temples +2 Science). Krung Si (needs both) → tradition *Phra Khlang Sinkha* (+2 Gold and +1 Influence per trade route) and +1 settlement cap. |
| Favored wonder | every civ has one | Wat Xieng Thong, only when the Asia wonders DLC is in use. |
| Unlocks | config + unlocks + syncretism | Unlocked by Khmer, or by 3 settlements on Navigable Rivers in Antiquity. Ayutthaya unlocks Siam. |
| Narrative | Đại Việt stories | "The Legend of Bang Rachan" story with two choices. |
| Names | | Capital Krung Si Ayutthaya + ~30 Ayutthaya-era towns (RTGS spelling). |

Attributes: Cultural, Economic. Start bias: Navigable River.

## Constraints

- Built and packaged on macOS. No Windows tools, so no new art packages; VisualRemaps + IconAliases only.
- Every type carries the `LTH_` prefix so it cannot collide with another Ayutthaya mod.
- Text lives once, in `text/strings.txt` (EN and TH side by side); the build writes the game XML and
  refuses to build if a tag lacks either language or the two disagree on markup.
- Mod Name/Description in the modinfo stay ASCII (Thai there renders as boxes on the Add-Ons screen).

## Left to the builder (my calls)

- Second unique unit is the Thammathut monk rather than the river warship floated in chat: it serves
  the wat pillar the owner chose.
- Ubosot borrows the Maurya Vihara's art, the Prang borrows Majapahit's Meru; to be checked in game.
- Loading screen and narrative panel borrow Siam's images; no narration audio.
