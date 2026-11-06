#!/usr/bin/env python3
"""Make one English term read the same in every translated row.

Parallel translators coin terms independently; their reports list the coinages, and this applies the
decision. A rule only touches a row whose ENGLISH matches the rule's pattern, and replaces the listed
Thai variants (longest first) with the canonical form. Every decision is also written to
glossary/terms.tsv as "proposed" so the owner can review it.

  tools/harmonize.py [--dry-run]

Rules live in RULES below: (english regex, canonical Thai, [variants], guard regex on the Thai that
must NOT match for the replacement to apply, note).
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)

# Decided 2026-11-06 from the B1 translator reports (variants measured in their outputs).
RULES = [
    (r'\bCapital', 'นครหลวง', ['เมืองหลวง'], None, 'Capital; เมือง is Town'),
    (r'Combat Strength', 'พลังการรบ', ['พลังการต่อสู้'], None, 'Combat Strength'),
    (r'Treasure Convoy', 'ขบวนสมบัติ', ['ขบวนเรือสมบัติ', 'ขบวนขนสมบัติ', 'กองเรือสมบัติ'], None,
     'Treasure Convoy; กองเรือสมบัติ is Treasure Fleet'),
    (r'Mastery', 'ความเชี่ยวชาญ', ['ความชำนาญ'], None, 'Mastery'),
    (r'Constructible', 'สิ่งปลูกสร้าง', ['สิ่งที่สร้างได้', 'สิ่งที่สร้าง'], None,
     'Constructible; Building is สิ่งก่อสร้าง'),
    (r'\bAppeal', 'ความน่าดึงดูด', ['เสน่ห์'], ('th_not_after', 'มี'), 'Appeal (Charming = มีเสน่ห์ stays)'),
    (r'(?i)minor power', 'ขั้วอำนาจรอง', ['ขั้วอำนาจย่อย'], None, 'Minor Power'),
    (r'Warehouse', 'คลังสินค้า', ['โกดัง'], None, 'Warehouse'),
    (r'Endeavor', 'โครงการร่วม', ['ภารกิจร่วม', 'การริเริ่ม'], None, 'Endeavor'),
    (r'Treasury', 'คลัง', ['ท้องพระคลัง'], None, 'Treasury'),
    (r'(?i)town focus|\bfocus', 'จุดเน้น', ['การมุ่งเน้น', 'การเน้น'], None, 'Town Focus = จุดเน้นของเมือง'),
    (r'(?i)siege', 'ยูนิตปิดล้อม', ['ยูนิตล้อมเมือง', 'ยูนิตล้อมโจมตี'], None, 'Siege Units'),
    (r'(?i)naval', 'ยูนิตทางเรือ', ['ยูนิตทางทะเล'], None, 'Naval Units'),
    (r'(?i)adjacen', 'โบนัสการอยู่ติดกัน',
     ['โบนัสจากการตั้งติดกัน', 'โบนัสจากการอยู่ติดกัน', 'โบนัสที่ตั้งติดกัน', 'โบนัสช่องติดกัน'], None, 'Adjacency Bonus'),
    # Antiquity round (2026-11-06). Legalism is the Chinese school (法家): ลัทธินิตินิยม; นิติธรรม means rule of law.
    (r'Legalis', 'ลัทธินิตินิยม', ['ลัทธินิติธรรม'], None, 'Legalism'),
    (r'Medjay', 'เมดเจย์', ['เมดจาย'], None, 'Medjay'),
    (r'Mississippian', 'มิสซิสซิปเปียน', ['มิสซิสซิปปี'], None, 'Mississippian (civilization name)'),
    (r'Cahokia', 'คาโฮเคีย', ['คาโฮเกีย'], None, 'Cahokia'),
    (r'(?i)military units?', 'ยูนิตทหาร', ['ยูนิตทางทหาร'], None, 'Military Unit'),
    (r'(?i)diplomatic action', 'ปฏิบัติการทางการทูต', ['การดำเนินการทางการทูต'], None, 'Diplomatic Action'),
    (r'Commendation', 'เหรียญเชิดชู', ['เหรียญเกียรติยศ'], None, 'Commendation'),
    (r'^Story continues\.?$', 'เรื่องราวยังดำเนินต่อไป', ['เรื่องราวดำเนินต่อไป'], None, 'Story continues.'),
    (r'Trung Trac|Trung Tr', 'จึงจัก', ['จึงจั๊ก'], None, 'Trung Trac (leader)'),
    (r'Rizal', 'รีซัล', ['ริซัล'], None, 'Rizal (leader)'),
    (r'(?i)age progress', 'ความคืบหน้าของยุค', ['ความก้าวหน้าของยุค'], None, 'Age Progress'),
    (r'(?i)minor triumph', 'ไทรอัมพ์รอง', ['ไทรอัมพ์ย่อย'], None, 'Minor Triumph'),
    (r'(?i)trebuchet', 'เทรบูเชต์', ['เครื่องยิงหิน'], ('en_skip', r'(?i)catapult'), 'Trebuchet (unit); Catapult keeps เครื่องยิงหิน'),
    (r'(?i)cohong', 'โคหอง', ['โคหง', 'โคฮง'], None, 'Cohong'),
    (r'(?i)vi[e\u1ec7]t', 'เวียด', ['เวียต'], None, 'Viet (as in Dai Viet = ไดเวียด)'),
    (r'(?i)janissar', 'เยนิเชรี', ['เจนิสซารี', 'จานิสซารี'], None, 'Janissary (unit name = เยนิเชรี)'),
    (r'(?i)blackbeard', 'หนวดดำ', ['แบล็กเบียร์ด'], None, 'Blackbeard'),
    (r'(?i)edward teach', 'เอ็ดเวิร์ด ทีช', ['เอดเวิร์ด ทีช'], None, 'Edward Teach (leader)'),
    (r'(?i)d[a\u1ea1]i vi[e\u1ec7]t', 'ไดเวียด', ['ได่เหวียต'], None, 'Dai Viet (civilization)'),
    (r'(?i)\bdhow', 'เรือเดาว์', ['เรือดาว'], None, 'Dhow (unit)'),
    (r'(?i)sayyida', 'ซัยยิดะฮ์ อัลฮุรเราะฮ์', ['ซัยยิดะห์ อัลฮุรเราะห์'], None, 'Sayyida al Hurra (leader)'),
    (r'(?i)amaterasu', 'อามาเทราสึ', ['อามาเตราสึ'], None, 'Amaterasu'),
    (r'(?i)caliph', 'เคาะลีฟะฮ์', ['กาหลิบ'], None, 'Caliph (Caliphate = รัฐเคาะลีฟะฮ์)'),
    (r'(?i)trench fighter', 'เครื่องบินโจมตีสนามเพลาะ', ['ทหารสนามเพลาะ'], None, 'Trench Fighter'),
    (r'(?i)unique building', 'สิ่งก่อสร้างเฉพาะตัว', ['สิ่งก่อสร้างเฉพาะ', 'สิ่งก่อสร้างพิเศษ'], ('th_not_before', 'ตัว'), 'Unique Building'),
    (r'(?i)unique improvement', 'สิ่งปรับปรุงเฉพาะตัว', ['สิ่งปรับปรุงเฉพาะ', 'สิ่งปรับปรุงพิเศษ'], ('th_not_before', 'ตัว'), 'Unique Improvement'),
    (r'(?i)endeavou?r', 'โครงการร่วม', ['ภารกิจร่วม'], None, 'Endeavor (terms.tsv)'),
    (r'(?i)master(y|ies)', 'ความเชี่ยวชาญ', ['ความชำนาญ'], None, 'Mastery (terms.tsv)'),
    (r'(?i)major triumph', 'ไทรอัมพ์สำคัญ', ['ไทรอัมพ์หลัก'], None, 'Major Triumph (LOC_LEGACIES_MAJOR_TRIUMPHS)'),
    (r'(?i)reciprocal damage', 'ความเสียหายสะท้อนกลับ', ['ความเสียหายตอบโต้'], None, 'Reciprocal Damage'),
    (r'(?i)reliquary belief', 'ความเชื่อหีบพระธาตุ', ['ความเชื่อผอบบรรจุวัตถุศักดิ์สิทธิ์'], None, 'Reliquary Belief (the class; the belief Reliquaries keeps its own name)'),
    (r'(?i)town focus', 'จุดเน้นของเมือง', ['การเน้นของเมือง'], None, 'Town Focus (terms.tsv)'),
    (r'(?i)minor independent', 'ขั้วอำนาจอิสระรอง', ['ฝ่ายอิสระรอง'], None, 'Minor Independent (Independent Power = ขั้วอำนาจอิสระ)'),
    (r'(?i)stealth', 'พรางตัว', ['ล่องหน'], None, 'Stealth (unit ability)'),
    (r'(?i)fortified district', 'เขตป้อมปราการ', ['เขตที่มีป้อมปราการ'], None, 'Fortified District'),
    (r'(?i)silk roads?', 'เส้นทางสายไหม', ['ถนนสายไหม'], None, 'Silk Road'),
    (r'(?i)unique unit', 'ยูนิตเฉพาะตัว', ['ยูนิตเฉพาะ'], ('th_not_before', 'ตัว'), 'Unique Unit'),
    (r'(?i)water terrain', 'ภูมิประเทศทางน้ำ', ['ภูมิประเทศผืนน้ำ'], None, 'Water Terrain'),
    (r'(?i)foundation (path|challenge)', 'รากฐาน', ['พื้นฐาน'], None, 'Foundation (LOC_CIVIC_AQ_FOUNDATION_NAME = รากฐาน)'),
    (r'(?i)counter[- ]?spy', 'ต่อต้านจารชน', ['ต่อต้านสายลับ', 'ต่อต้านจารกรรม'], None, 'Counterspy (names.tsv Counter Spy)'),
    (r'(?i)maratha', 'มราฐะ', ['มราฐา'], None, 'Maratha'),
    (r'(?i)sengoku', 'เซ็นโงกุ', ['เซ็งโงกุ'], None, 'Sengoku (civ name ญี่ปุ่นสมัยเซ็นโงกุ)'),
    (r'(?i)\bashur\b', 'อัสซูร์', ['อาชูร์'], None, 'Ashur'),
    (r'(?i)ieyasu', 'อิเอยาซุ', ['อิเอยาสุ'], None, 'Ieyasu'),
    (r'\bDido\b', 'ไดโด', ['ดีโด'], None, 'Dido'),
    (r'(?i)wang k[oŏ]n', 'วังกอน', ['หวังกอน'], None, 'Wang Kon'),
    (r'(?i)gorkha', 'กอร์ขา', ['โครขา'], None, 'Gorkha (as in กอร์ขาปัตร); the unit Gurkha stays กุรข่า'),
    (r'(?i)bol[iíi]var', 'โบลีวาร์', ['โบลิวาร์'], None, 'Bolivar'),
    (r'(?i)varangian', 'วารังเกียน', ['วาแรนเจียน', 'วารันเจียน'], None, 'Varangian (the form most translations use)'),
    (r'(?i)ikko-ikki', 'อิกโกอิกกิ', ['อิกโก-อิกกิ'], None, 'Ikko-Ikki'),
    (r'(?i)unique abilit(y|ies)', 'ความสามารถเฉพาะตัว', ['ความสามารถพิเศษ'], None, 'Unique Ability'),
    (r'(?i)happiness buildings?', 'สิ่งก่อสร้างที่ให้ความสุข', ['สิ่งก่อสร้างความสุข'], None, 'Happiness Buildings'),
    (r'(?i)[oö]rt[oö][oö]', 'เออร์เตอ', ['ออร์เตอ'], None, 'Ortoo (names.tsv)'),
    (r'(?i)mikasa', 'มิกาซะ', ['มิกาสะ'], None, 'Mikasa (LOC_UNIT_MIKASA_NAME)'),
    (r'(?i)food buildings?', 'สิ่งก่อสร้างที่ให้อาหาร', ['สิ่งก่อสร้างประเภทอาหาร', 'สิ่งก่อสร้างด้านอาหาร'], None, 'Food Buildings'),
    (r'(?i)production buildings?', 'สิ่งก่อสร้างที่ให้การผลิต', ['สิ่งก่อสร้างประเภทการผลิต', 'สิ่งก่อสร้างด้านการผลิต'], None, 'Production Buildings'),
    (r'(?i)culture buildings?', 'สิ่งก่อสร้างที่ให้วัฒนธรรม', ['สิ่งก่อสร้างประเภทวัฒนธรรม', 'สิ่งก่อสร้างด้านวัฒนธรรม'], None, 'Culture Buildings'),
    (r'(?i)science buildings?', 'สิ่งก่อสร้างที่ให้วิทยาศาสตร์', ['สิ่งก่อสร้างประเภทวิทยาศาสตร์', 'สิ่งก่อสร้างด้านวิทยาศาสตร์'], None, 'Science Buildings'),
    (r'(?i)gold buildings?', 'สิ่งก่อสร้างที่ให้ทอง', ['สิ่งก่อสร้างประเภททอง', 'สิ่งก่อสร้างด้านทอง'], None, 'Gold Buildings'),
    (r'(?i)happiness buildings?', 'สิ่งก่อสร้างที่ให้ความสุข', ['สิ่งก่อสร้างประเภทความสุข', 'สิ่งก่อสร้างด้านความสุข'], None, 'Happiness Buildings'),
    (r'(?i)resource slots?', 'ช่องทรัพยากร', ['ช่องใส่ทรัพยากร'], None, 'Resource Slot'),
    (r'(?i)great work slots?', 'ช่องผลงานชิ้นเอก', ['ช่องใส่ผลงานชิ้นเอก'], None, 'Great Work Slot'),
    (r'(?i)good doctor', 'คุณหมอผู้ใจดี', ['คุณหมอผู้แสนดี', 'หมอผู้แสนดี'], None, 'The Good Doctor'),
    (r'(?i)bayeux', 'บาเยอ', ['บายเยอ'], None, 'Bayeux'),
    (r'(?i)ageless', 'ไร้กาลเวลา', ['ไร้ยุค'], None, 'Ageless'),
    (r'(?i)tenskwatawa', 'เทนสกวาทาวา', ['เทนสกวาตาวา', 'เท็นสกวาทาวา'], None, 'Tenskwatawa'),
    (r'(?i)unique quarter', 'ย่านเฉพาะตัว', ['ย่านเฉพาะ'], ('th_not_before', 'ตัว'), 'Unique Quarter'),
    (r'War Weariness', 'ความเหนื่อยล้าจากสงคราม', ['ความเบื่อหน่ายสงคราม'], None, 'War Weariness'),
]


def main(dry):
    cat = {}
    for line in open(os.path.join(MOD, 'work', 'catalog.jsonl'), encoding='utf-8'):
        u = json.loads(line)
        cat[(u['tag'], u['en_sha'])] = u['en']
    total = 0
    per_rule = {r[1]: 0 for r in RULES}
    for path in sorted(glob.glob(os.path.join(MOD, 'translations', '*.jsonl'))):
        rows = [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]
        changed = 0
        for e in rows:
            en = cat.get((e['tag'], e['en_sha']), '')
            th = e['th']
            for pat, canon, variants, guard, _ in RULES:
                if not re.search(pat, en):
                    continue
                # guard: ('en_skip', regex) -> leave the row alone if its ENGLISH matches;
                #        ('th_not_after', text) -> replace only where the variant does not follow `text`.
                if guard and guard[0] == 'en_skip' and re.search(guard[1], en):
                    continue
                for v in sorted(variants, key=len, reverse=True):
                    if v in th:
                        if guard and guard[0] == 'th_not_after':
                            th = re.sub(f'(?<!{re.escape(guard[1])}){re.escape(v)}', canon, th)
                        elif guard and guard[0] == 'th_not_before':  # variant is a prefix of canon
                            th = re.sub(f'{re.escape(v)}(?!{re.escape(guard[1])})', canon, th)
                        else:
                            th = th.replace(v, canon)
                if th != e['th']:
                    per_rule[canon] += 1
            if th != e['th']:
                e['th'] = th
                changed += 1
        total += changed
        if changed and not dry:
            with open(path, 'w', encoding='utf-8') as f:
                for e in rows:
                    f.write(json.dumps(e, ensure_ascii=False) + '\n')
        print(f'{os.path.relpath(path, MOD)}: {changed} row(s) changed')
    print('per rule:', ', '.join(f'{k} {v}' for k, v in per_rule.items() if v))

    if not dry:
        tpath = os.path.join(MOD, 'glossary', 'terms.tsv')
        have = {l.split('\t')[0] for l in open(tpath, encoding='utf-8').read().splitlines()[1:]}
        add = []
        for pat, canon, variants, _, note in RULES:
            en_term = note.split(';')[0].split(' (')[0].split(' =')[0]
            if en_term not in have:
                add.append(f'{en_term}\t{canon}\tconcept\tproposed\tharmonize.py; replaces {", ".join(variants)}')
        if add:
            with open(tpath, 'a', encoding='utf-8') as f:
                f.write('\n'.join(add) + '\n')
        print(f'glossary/terms.tsv: +{len(add)} proposed term(s)')
    print(f'{total} row(s) {"would change" if dry else "changed"}')
    return 0


if __name__ == '__main__':
    sys.exit(main('--dry-run' in sys.argv))
