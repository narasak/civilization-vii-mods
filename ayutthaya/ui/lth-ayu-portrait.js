/**
 * @file lth-ayu-portrait.js
 * @description Give Ayutthaya's unique units a portrait in the selected-unit panel.
 *
 * The panel draws a live 3D render: unit-actions.js calls WorldUI.requestPortrait(unitType, unitType, bg)
 * and shows url("live:/<unitType>"). Visual remaps do not reach that render, so our units showed an empty
 * black square (seen 2026-11-12). We re-request the same live texture name, rendered from the unit whose
 * model the remap borrows. One element lookup per second, game only; no MutationObserver.
 */
const LTH_AYU_PORTRAIT_MODEL = {
    UNIT_LTH_BANG_RACHAN: 'UNIT_SWORDSMAN',
    UNIT_LTH_BANG_RACHAN_2: 'UNIT_MAN_AT_ARMS',
    UNIT_LTH_BANG_RACHAN_3: 'UNIT_PIKEMAN',
    UNIT_LTH_THAMMATHUT: 'UNIT_MISSIONARY',
};
let lthAyuLastPortrait = '';

function lthAyuPortrait() {
    if (typeof WorldUI === 'undefined' || !WorldUI.requestPortrait) {
        return;
    }
    const img = document.querySelector('.unit-actions__unit-portrait-image');
    const bg = img?.style.backgroundImage || '';
    const m = /live:\/(UNIT_LTH_[A-Z0-9_]+)/.exec(bg);
    if (!m) {
        lthAyuLastPortrait = '';
        return;
    }
    const type = m[1];
    const model = LTH_AYU_PORTRAIT_MODEL[type];
    if (!model || lthAyuLastPortrait === type) {
        return;
    }
    try {
        WorldUI.requestPortrait(type, model, 'UnitPortraitsBG_UNIQUE');
        lthAyuLastPortrait = type;
        console.log(`LTH-AYU: portrait ${type} rendered from ${model}`);
    } catch (e) {
        console.error(`LTH-AYU: portrait request failed for ${type}: ${e}`);
    }
}

setInterval(lthAyuPortrait, 1000);
console.log('LTH-AYU: portrait helper loaded');
