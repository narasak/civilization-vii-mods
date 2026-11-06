"""Shared text rules for every tool that reads or writes translations — one copy, not three.

Before this module, batch.py, check.py and build_text.py each had their own placeholder regex, and
they drifted: one missed lowercase markup (13,871 tokens), and none could see a selector whose
choices contain placeholders, e.g. {1_Amount: plural 1?{1_Amount} turn; other?{1_Amount} turns;}.
"""
import re
from collections import Counter


def tokens(text):
    """Markup tokens in order: every balanced {...} (nested braces kept whole) and every [...]."""
    out = []
    s = text or ''
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == '{':
            depth, j = 0, i
            while j < n:
                if s[j] == '{':
                    depth += 1
                elif s[j] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth != 0:          # unbalanced: take the rest so a comparison can still fail loudly
                out.append(s[i:])
                break
            out.append(s[i:j + 1])
            i = j + 1
        elif c == '[':
            j = s.find(']', i + 1)
            if j == -1:
                out.append(s[i:])
                break
            out.append(s[i:j + 1])
            i = j + 1
        else:
            i += 1
    return out


def strip_tokens(text, repl=' '):
    """Text with every token replaced — for counting visible characters or checking prose."""
    s = text or ''
    for t in sorted(set(tokens(s)), key=len, reverse=True):
        s = s.replace(t, repl)
    return s


# Droppable tokens: plural/gender selectors, and {LOC_GRAMMAR_X << {1_Y}} helpers, which add English
# articles and verbs ("a ", "has ") that Thai does not use. A translation may keep them, drop them,
# or use the placeholders inside them on their own (the game's Japanese text does the same).
SELECTOR = re.compile(r'^\{(?:[^:{}]+:\s*(?:plural|gender)\b|LOC_GRAMMAR_)')


# A number format can carry words: {1_value: number Take # Damage; Heal # Health} (LOC_REWARD_ADJUST_DAMAGE,
# the only one in the game on 2026-11-06). Its words are prose the player reads, so they may be translated;
# what must survive is the placeholder, the `number` keyword and the format skeleton (# and ; counts).
NUMBER_WORDS = re.compile(r'^\{([^:{}]+):\s*number\s+(.*)\}$', re.S)


def _key(t):
    m = NUMBER_WORDS.match(t)
    if m and re.search(r'[A-Za-z฀-๿]{2,}', m.group(2)):
        body = m.group(2)
        return f'{{{m.group(1).strip()}: number <words> #{body.count("#")} ;{body.count(";")}}}'
    return t


def strict_tokens(text):
    """Tokens that must survive translation exactly. Plural/gender selectors choose an English word
    by count or gender; Thai inflects neither, so a translation may replace them with the Thai word."""
    return Counter(_key(t) for t in tokens(text) if not SELECTOR.match(t))


# Latin letters touching Thai with no space ("การแofficial") — corruption, not style.
GLUED = re.compile(r'[\u0e00-\u0e7f][A-Za-z]+|[A-Za-z]+[\u0e00-\u0e7f]')
ALLOWED_EXTRA = '\u200b\u200c\u200d\u2060\ufeff'


def bad_chars(th):
    return sorted({c for c in (th or '') if not (c.isascii() or '\u0e00' <= c <= '\u0e7f' or c in ALLOWED_EXTRA)})


def glued(th):
    return GLUED.findall(strip_tokens((th or '').replace('\u200b', '')))


def compare(en, th):
    """(missing, extra) token lists for a translation, empty when it is acceptable.

    Non-selector tokens must match as a multiset. A plural/gender selector may be dropped, kept, or
    replaced by the placeholders it contains: {1_Amount: plural 1?{1_Amount} turn;...} -> "{1_Amount} ครั้ง".
    """
    want, got = strict_tokens(en), strict_tokens(th)
    # A grammar helper wraps a name: dropping the helper is fine, dropping the name is not.
    th_tokens = set(tokens(th))
    for t in tokens(en):
        if t.startswith('{LOC_GRAMMAR_') and t not in th_tokens:
            for inner in set(tokens(t[1:-1])):
                want[inner] += 1
    allowance = Counter()
    for t in tokens(en):
        if SELECTOR.match(t):
            for inner in set(tokens(t[1:-1])):
                allowance[inner] += 1
    extra = got - want
    for t in list(extra):
        extra[t] -= min(extra[t], allowance[t])
    extra = +extra
    return list((want - got).elements()), list(extra.elements())


def split_keep(text):
    """Text split into alternating prose and whole tokens (nested braces kept intact)."""
    s = text or ''
    parts, pos = [], 0
    for t in tokens(s):
        i = s.find(t, pos)
        if i > pos:
            parts.append(s[pos:i])
        parts.append(t)
        pos = i + len(t)
    if pos < len(s):
        parts.append(s[pos:])
    return parts


def is_token(piece):
    return bool(piece) and ((piece[0] == '{' and piece[-1] == '}') or (piece[0] == '[' and piece[-1] == ']'))
