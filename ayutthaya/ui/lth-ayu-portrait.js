/**
 * @file lth-ayu-portrait.js
 * @description Give Ayutthaya's unique units a portrait in the selected-unit panel.
 *
 * base-standard unit-actions.js (line ~710) calls WorldUI.requestPortrait(unitType, unitType, bg) and
 * shows url("live:/<unitType>"). Visual remaps do not reach that render, so our units showed an empty
 * black square (2026-11-12, again 2026-11-15).
 *
 * v1 re-requested live:/UNIT_LTH_* with the model unit as 2nd argument: still black, so the render
 * follows the FIRST argument. v2 used our own texture name: "Failed loading resource:
 * live:/LTH_PORTRAIT_..." (UI.log 2026-11-15), so the name must be a real unit type. v3 shows the
 * borrowed unit's own portrait, live:/<model>, exactly as the panel does for that unit. The panel
 * puts live:/UNIT_LTH_* back on every refresh; the next tick swaps it again.
 * v4 (2026-11-16): swaps every element carrying live:/UNIT_LTH_* (the army panel slots too), via one
 * attribute-selector query every 500 ms, game only; no MutationObserver.
 *
 * Logging uses console.error: this build writes only console.error to UI.log (the Thai pack's
 * lth-thai-fonts.js logs the same way); console.log lines never appeared, which hid v1's state.
 */
const LTH_AYU_PORTRAIT_MODEL = {
    UNIT_LTH_BANG_RACHAN: 'UNIT_SWORDSMAN',
    UNIT_LTH_BANG_RACHAN_2: 'UNIT_MAN_AT_ARMS',
    UNIT_LTH_BANG_RACHAN_3: 'UNIT_PIKEMAN',
    UNIT_LTH_THAMMATHUT: 'UNIT_MISSIONARY',
    UNIT_LTH_CHANG_SONG: 'UNIT_DANTINAS_TATHA',
};
const lthAyuRendered = new Set();
const lthAyuLog = (msg) => console.error(`LTH-AYU: ${msg}`);

function lthAyuSwap(el) {
    const m = /live:\/(UNIT_LTH_[A-Z0-9_]+)/.exec(el.style.backgroundImage || '');
    if (!m) {
        return;
    }
    const type = m[1];
    const model = LTH_AYU_PORTRAIT_MODEL[type];
    if (!model) {
        return;
    }
    try {
        // Requested on every swap (swaps happen only when a panel resets it), in case the renderer
        // released the texture; logged once per model.
        WorldUI.requestPortrait(model, model, 'UnitPortraitsBG_UNIQUE');
        if (!lthAyuRendered.has(model)) {
            lthAyuRendered.add(model);
            lthAyuLog(`portrait ${type} shown as ${model}`);
        }
        el.style.backgroundImage = `url("live:/${model}")`;
    } catch (e) {
        lthAyuLog(`portrait request failed for ${type}: ${e}`);
    }
}

function lthAyuPortrait() {
    if (typeof WorldUI === 'undefined' || !WorldUI.requestPortrait) {
        return;
    }
    // Every element showing one of our live portraits: the selected-unit panel AND the slots of a
    // commander's army panel (black squares there on 2026-11-16). Matches inline style only.
    let els;
    try {
        els = document.querySelectorAll('[style*="live:/UNIT_LTH_"]');
    } catch (e) {
        // If the UI engine rejects the attribute selector, keep v3's behaviour (selected-unit panel only).
        if (!lthAyuRendered.has('#fallback')) {
            lthAyuRendered.add('#fallback');
            lthAyuLog(`attribute selector unsupported (${e}); selected-unit panel only`);
        }
        els = document.querySelectorAll('.unit-actions__unit-portrait-image');
    }
    els.forEach(lthAyuSwap);
}

setInterval(lthAyuPortrait, 500);
lthAyuLog('portrait helper v4 loaded');
