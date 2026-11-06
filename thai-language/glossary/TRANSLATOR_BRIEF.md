# Translator brief: Civilization VII to Thai

You are translating in-game text of Sid Meier's Civilization VII into Thai for a fan Thai-language mod.
Work only on the input and output files named in your task.

## Files
- **Input:** `work/batches/<batch>.jsonl`. Each line is `{"tag","en_sha","en","file"}`. `file` tells you the
  screen or context: UnitText = units, ConstructibleText = buildings and improvements,
  NarrativeStories = story events, Civilopedia_* = encyclopedia articles, LeaderDialog_* = what a
  leader says to you, CityNames = names of cities, and so on.
- **Output:** `work/batches/<batch>.th.jsonl`. One line per input line, in the same order:
  `{"tag": same, "en_sha": same, "th": Thai}`, written with `json.dumps(..., ensure_ascii=False)`.
  Use a Python script to write it. Do not type thousands of lines into a shell heredoc.
- **Keep your scripts in your own folder:** `<scratchpad>/<batch>/` (for example `.../scratchpad/ex-d-07/tr.py`).
  Other translators run at the same time, and a shared file name like `tr03.py` let one translator
  overwrite and re-run another's script (2026-11-06).
- Paths are relative to the mod folder (`thai-language/` in the repository).

## Read first (mandatory)
- `glossary/POLICY.md`: the approved translation rules.
- `glossary/terms.tsv`: term decisions. Use them exactly, including the `proposed` ones.
- `glossary/names.tsv`: the canonical Thai for every name already translated (units, buildings, yields,
  ages, terrain, promotions, ...). Load it in your script. When an English string mentions one of
  these names, use exactly that Thai.

Key decisions:
- City = นคร, Town = เมือง, Settlement = ถิ่นฐาน, Capital = นครหลวง
- Unit = ยูนิต, Turn = เทิร์น, Yield = ผลผลิต, Plot/Tile = ช่อง, Tooltip = คำแนะนำ
- Combat Strength = พลังการรบ, Constructible = สิ่งปลูกสร้าง, Building = สิ่งก่อสร้าง
- Age names already contain ยุค (Antiquity = ยุคโบราณ), so "{1_AgeName} Age" -> "{1_AgeName}".
  Never write ยุคยุค.

## Hard rules (`python3 tools/batch.py validate <in> <out>` enforces all of them)
1. Keep every `{...}` and `[...]` token exactly, in any case: `{1_Name}`, `{2_Num : number #,###}`,
   `[ICON_GOLD]`, `[icon:YIELD_GOLD]`, `[N]`, `[n]`, `[B]`...`[/B]`, `[b]`, `[LI]`, `[STYLE:...]`,
   `[style: {1_S}]...[/style]`. You may move tokens to suit Thai grammar. Never drop, add or rename one.
   Exceptions:
   - Plural and gender selectors (`{1_X: plural 1?turn; other?turns;}`) may be replaced by the Thai word.
     If the selector contains a placeholder, keep that placeholder: `{1_X} เทิร์น`.
   - `{LOC_GRAMMAR_... << {1_Y}}` helpers may be dropped, but `{1_Y}` inside them must stay.
2. No U+200B and no zero-width characters. The build inserts word breaks. Do not put spaces between Thai
   words. Use a space only where Thai uses one: between phrases or clauses, and around Latin words,
   numbers and icons.
   A [TIP:...]word[/TIP] link is a Thai word, not an icon: write `บน[TIP:..]สิ่งปรับปรุง[/TIP]ต่อไปนี้`,
   never `บน [TIP:..]สิ่งปรับปรุง[/TIP] ต่อไปนี้` (tools/check.py fails on it).
3. Use only ASCII and Thai characters. That means no curly quotes, en/em dashes, ellipsis character, ×,
   •, ©, ®, accented Latin letters or any other script. Use " ' - ... x (C) (R) instead. Accented names
   must be transliterated into Thai.
4. Every input line appears exactly once in the output, with tag and en_sha unchanged.
5. Never let Latin letters touch Thai letters without a space between them.
6. Leave these as they are: brand names, keyboard and gamepad labels, technical tokens, and Legacy-path
   names written in Latin (Pax Imperatoria and similar).

## Names (rows whose tag ends in _NAME, and city/citizen/place names)
- Real places, peoples and people: use the established Thai name where one exists (อียิปต์, โรม, บาบิโลน,
  เอเธนส์, ขงจื๊อ). Otherwise transcribe into Thai following the Royal Society of Thailand's
  principles for the source language.
- Game objects (units, buildings, improvements, techs, civics): translate by meaning into short,
  natural Thai that a Thai strategy-game player would recognise. Historically specific unique items
  that are named in their own language (Hoplite, Ziggurat, Legion) are transliterated unless Thai
  already has a word for them (Pyramid = พีระมิด).
- The same English name must get the same Thai everywhere. Two different English names must not end up
  with the same Thai.

## Style
- Write natural, concise Thai. UI labels should be short. Descriptions should be full sentences.
- Narrative, story and Civilopedia text should be fluent literary Thai in a neutral written register
  (ภาษาเขียน). It should not read like a word-for-word translation.
- Leader dialog is spoken by a historical leader. Use a dignified first person (ข้า / เรา) to fit the
  character, and address the player as ท่าน.
- No ครับ or ค่ะ. Use คุณ only where English says "you" in UI text. Use Arabic numerals.

## Validate until it prints "0 error(s)"
    cd thai-language && python3 tools/batch.py validate work/batches/<batch>.jsonl work/batches/<batch>.th.jsonl

## Final report (nothing else)
1. The validator's last line.
2. How many rows were left in English and why, in one line.
3. Up to 5 judgment calls (tag and your choice).
4. Any new recurring game term you had to coin that is not in terms.tsv or names.tsv, as English -> Thai.
