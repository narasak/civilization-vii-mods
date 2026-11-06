/**
 * @file lth-thai-fonts.js
 * @description Make Thai renderable, at no ongoing cost to the UI thread.
 *
 * What the Phase 0 runs established (2026-11-06, build 1.5.0 / 1311346):
 *  - The game ships no font with Thai glyphs; we bundle Sarabun (body) and Kanit (title), OFL 1.1,
 *    rebuilt by tools/build-fonts.py with a zero-width U+200B glyph.
 *  - Gameface does not parse `unicode-range`, so a face must never be added to the native
 *    "BodyFont"/"TitleFont" families (it would replace the game's Latin font).
 *  - Gameface does fall back glyph by glyph along a font-family list, and scripts cannot read or edit
 *    the game's stylesheets (147/147 rules "unreadable"). So we out-rank the game's font rules with our
 *    own stylesheet: the same selectors, prefixed with `html`, with our family inserted in each stack.
 *    tools/check.py fails when a game update adds a font rule this list does not cover.
 *
 * Removed 2026-11-06 because the player saw buttons needing several clicks: a MutationObserver on
 * <body> (subtree + characterData) that ran getComputedStyle on every UI change. In the game it had
 * examined 2,111 elements and fixed 0 - pure cost. What remains is one <style> injection, plus a
 * single read-only audit in the front end that logs to UI.log ("LTH: audit") if a gap ever appears.
 */

const BUILD = 'v10';
const FAMILY_BODY = 'LTH-Sarabun';
const FAMILY_TITLE = 'LTH-Kanit';
const MOD_ID = 'lth-thai-language';

function src(file) {
    return `url("fs://game/${MOD_ID}/fonts/${file}"), url("fs://game/fonts/${file}")`;
}

const SIZES = ['2xs', 'xs', 'sm', 'base', 'lg', 'xl', '2xl']; // global-scaling.js fontSizes
const STATIC_BODY = [ // every static `font-family: "BodyFont", ...` rule in the game's .css files
    '.turn-icon .turn-display',
    '.unit-flag__army-stats',
    'panel-age-scores .age-scores__first-thermo-value',
    'panel-age-scores .age-scores__remainder-score',
    'panel-age-scores .age-scores__second-thermo-value',
    'panel-age-scores .age-scores__third-thermo-value',
    'panel-age-scores .age-scores__vict-req-number-value',
];
const STATIC_TITLE = [ // every static `font-family: "TitleFont", ...` rule
    'panel-age-scores .age-scores__card-title-text',
    'panel-age-scores .age-scores__first-place-label',
    'panel-age-scores .age-scores__remainder-profile-label',
    'panel-age-scores .age-scores__second-place-label',
    'panel-age-scores .age-scores__third-place-label',
];
// Thai stacks marks above and below the line; `leading-none` (line-height 1) makes wrapped Thai lines
// collide. Seen in the loading-screen tip box (load-screen.js _tmpl$4, screenshot 2026-11-06 15:19).
// Scoped to that box: a global .leading-none override would move icons and badges everywhere.
const THAI_LEADING = 'html .load-screen-tips-and-hints-inner-rect .leading-none { line-height: 1.45; }';
const STACK_BODY = `BodyFont, "${FAMILY_BODY}", "BodyFont-SC", "BodyFont-TC", "BodyFont-JP", "BodyFont-KR"`;
const STACK_TITLE = `TitleFont, "${FAMILY_TITLE}", "TitleFont-SC", "TitleFont-TC", "TitleFont-JP", "TitleFont-KR"`;

/** One face per CSS weight 100-900 (400/700 alone left font-medium = 500 unmatched). */
function faces(family, regular, bold) {
    const out = [];
    for (let w = 100; w <= 900; w += 100) {
        out.push(`@font-face { font-family: "${family}"; src: ${src(w <= 500 ? regular : bold)}; font-weight: ${w}; }`);
    }
    return out;
}

function css() {
    const sel = (list) => list.map(x => `html ${x}`).join(',\n');
    const title = ['.font-title', ...SIZES.map(z => `.font-title-${z}`), ...STATIC_TITLE];
    const body = ['.font-body', ...SIZES.map(z => `.font-body-${z}`), ...STATIC_BODY];
    return [
        ...faces(FAMILY_BODY, 'lth-Sarabun-Regular.ttf', 'lth-Sarabun-SemiBold.ttf'),
        ...faces(FAMILY_TITLE, 'lth-Kanit-Medium.ttf', 'lth-Kanit-SemiBold.ttf'),
        `${sel(title)} { font-family: ${STACK_TITLE}; }`,
        `${sel(body)} { font-family: ${STACK_BODY}; }`,
        `html, body { font-family: ${STACK_BODY}; }`,
        THAI_LEADING,
    ].join('\n');
}

const log = (k, v) => console.error('LTH:', k, typeof v === 'string' ? v : JSON.stringify(v));

/** One pass, read-only: elements showing Thai whose font stack lacks our family. */
function auditOnce() {
    const THAI = /[\u0e00-\u0e7f]/;
    let thai = 0;
    const offenders = {};
    for (const el of document.body.querySelectorAll('*')) {
        let own = false;
        for (const c of el.childNodes) if (c.nodeType === 3 && THAI.test(c.nodeValue || '')) { own = true; break; }
        if (!own) continue;
        thai++;
        const ff = getComputedStyle(el).fontFamily || '';
        if (ff.indexOf(FAMILY_BODY) < 0 && ff.indexOf(FAMILY_TITLE) < 0) {
            offenders[`${el.tagName.toLowerCase()}.${String(el.className || '').trim().split(/\s+/).slice(0, 3).join('.')}`] = ff;
        }
    }
    log('audit', { thai, offenders });
}

/**
 * Thai text that WRAPS under a tight line-height: marks above and below collide between lines
 * (loading-screen tips, 2026-11-06). Single-line text is never reported, so the log lists only
 * places that need a scoped line-height fix in THAI_LEADING.
 *
 * Runs after user input, debounced and throttled. No MutationObserver: one firing on every DOM
 * change made buttons need several clicks (v6, 2026-11-06). Each scan logs its own cost ("ms").
 */
const LEADING_MIN = 1.3;   // line-height / font-size below this collides for wrapped Thai
const leadingSeen = new Set();
let leadingTimer = 0;
let leadingLast = 0;

function pathOf(el) {
    const part = (e) => e.tagName.toLowerCase() + String(e.className || '').trim().split(/\s+/)
        .filter(c => c && !/^(text-|font-|p[xytblr]?-|m[xytblr]?-|w-|h-|flex|items-|justify-)/.test(c))
        .slice(0, 3).map(c => '.' + c).join('');
    const out = [part(el)];
    for (let p = el.parentElement, i = 0; p && i < 2 && p !== document.body; p = p.parentElement, i++) out.unshift(part(p));
    return out.join(' > ');
}

function leadingScan() {
    leadingLast = Date.now();
    const t0 = Date.now();
    const THAI = /[฀-๿]/;
    let thai = 0;
    const found = [];
    for (const el of document.body.querySelectorAll('*')) {
        let own = false;
        for (const c of el.childNodes) if (c.nodeType === 3 && THAI.test(c.nodeValue || '')) { own = true; break; }
        if (!own) continue;
        thai++;
        const cs = getComputedStyle(el);
        const fs = parseFloat(cs.fontSize);
        const lh = parseFloat(cs.lineHeight);   // NaN for 'normal', which the font's own metrics space well
        if (!(fs > 0) || !(lh > 0) || lh / fs >= LEADING_MIN) continue;
        // Content height, not the box: padding made a one-line plot-tooltip row read as two lines
        // ("div.min-w-62 > div.relative > div", 2026-11-06 16:05; one line in the screenshot).
        const content = el.getBoundingClientRect().height - (parseFloat(cs.paddingTop) || 0) - (parseFloat(cs.paddingBottom) || 0)
            - (parseFloat(cs.borderTopWidth) || 0) - (parseFloat(cs.borderBottomWidth) || 0);
        if (content < lh * 1.8) continue;   // one line: nothing to collide with
        const key = pathOf(el);
        if (leadingSeen.has(key)) continue;
        leadingSeen.add(key);
        found.push({ el: key, ratio: Math.round(lh / fs * 100) / 100, text: (el.textContent || '').trim().slice(0, 24) });
    }
    log('leading', { ms: Date.now() - t0, thai, found });
}

function scheduleLeading() {
    clearTimeout(leadingTimer);
    const wait = Math.max(1200, 3000 - (Date.now() - leadingLast));
    leadingTimer = setTimeout(leadingScan, wait);
}

function start() {
    const style = document.createElement('style');
    style.id = 'lth-fonts';
    style.textContent = css();
    document.head.appendChild(style);
    log('build', BUILD);
    // Which build_css.py copy replaced the game's panel-animations.css (1 or 2), or none ('').
    let early = '';
    try { early = getComputedStyle(document.documentElement).getPropertyValue('--lth-early-css').trim(); } catch (_) {}
    log('early-css', early || 'none');
    if (typeof UI !== 'undefined' && typeof UI.isInShell === 'function' && UI.isInShell()) {
        setTimeout(auditOnce, 8000);
    }
    window.addEventListener('mouseup', scheduleLeading, true);
    window.addEventListener('keyup', scheduleLeading, true);
    setTimeout(leadingScan, 9000);
}

if (document.head && document.body) start();
else window.addEventListener('DOMContentLoaded', start, { once: true });
