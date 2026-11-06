# Translation policy — Thai for Civilization VII

Approved by the project owner 2026-11-06. Approved rules become checks
in `tools/check.py` where they can be checked mechanically.

## 1. Names of real places, peoples and people
- **Countries and civilizations:** use the established Thai name where one exists (อียิปต์, โรม,
  สเปน, อังกฤษ, รัสเซีย, จีน → but Civ's "Ming" = ราชวงศ์หมิง only where the text means the dynasty).
- **Historical persons:** use the spelling in common Thai use (ขงจื๊อ, เจงกิสข่าน, นโปเลียน). Where none
  exists, transcribe by the Royal Society of Thailand's transcription principles for the source
  language. Record every name in `terms.tsv` so it is spelled once and reused.
- **Fictional or untranslatable names** (Legacy names such as "Pax Imperatoria",
  "Non Sufficit Orbis"): keep the original in Latin script, and add a Thai gloss only in descriptions.

## 2. Game mechanics
- Translate by **meaning**, not word for word: "Production" is การผลิต (the yield), not ผลผลิต.
- One English term → one Thai term, everywhere (`terms.tsv`). A term used differently in two places
  is a defect, not a style choice.
- Keep established gaming loanwords where Thai players actually use them: เทิร์น (Turn),
  ยูนิต (Unit), HUD.

## 3. Register and form
- Neutral, written register, polite but not formal-royal. No ครับ/ค่ะ in UI text.
- Address the player as คุณ only where the English says "you".
- Arabic numerals (1, 2, 3), not Thai numerals.
- Keep every placeholder and markup token exactly: `{1_Num}`, `[ICON_GOLD]`, `[N]`, `[B]…[/B]`.
  `tools/check.py` refuses a row that drops or adds one.

## 3a. English grammar helpers
`{LOC_GRAMMAR_A_AN << {1_X}}`, `LOC_GRAMMAR_HAS_HAVE`, `LOC_GRAMMAR_LEADER` etc. add English articles and
verbs. The helpers themselves are translated to output only the name (`{1}`, as the game's Japanese
text does), and a translator may drop a helper and keep the placeholder inside it:
`{LOC_GRAMMAR_A_AN << {1_Building}} was pillaged` -> `{1_Building} ถูกปล้นสะดม`. Dropping the name is an error.

## 4. Typography
- **Translators never type U+200B.** `tools/build_text.py` inserts zero-width spaces between words
  at build time (PyThaiNLP), because Gameface cannot segment Thai; stored translations must not
  contain any. Short labels (< 20 characters) get none: letter-spaced menus draw each one as a gap.
- Only characters the bundled fonts cover: ASCII, the Thai block, and the zero-width set.
  No “smart quotes”, em dashes or ellipsis characters — use ASCII equivalents.

## 5. What is never committed
`work/` holds the game's English text (Firaxis' content). It is git-ignored. Committed translation
files hold only tag, English hash and Thai.
