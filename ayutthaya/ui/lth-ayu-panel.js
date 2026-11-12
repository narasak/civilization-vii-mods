/**
 * @file lth-ayu-panel.js
 * @description Show Ayutthaya's panel art on the game-setup screens.
 *
 * The civ card hard-codes `url('blp:bg-panel-<civ>')` (core/ui-next/screens/create-game/civ-card.js) and the
 * setup hub `url('blp:bg_panel_<civ>.png')` (create-game-hub.js). `blp:` resolves only textures packed by
 * Firaxis' Windows tools, so a Mac-built mod's PNG never loads there and the card stays black
 * (seen 2026-11-12). We point those two references at the PNG this mod imports instead.
 *
 * Cost, on purpose: no MutationObserver (the Thai Language Pack removed one on 2026-11-06 because it made
 * buttons need several clicks). One attribute query per second, front end only, touching only elements whose
 * inline style already names this civ.
 */
const LTH_AYU_ART = 'url("fs://game/lth-ayutthaya/art/bg-panel-lth_ayutthaya.png")';
const LTH_AYU_SELECTOR = '[style*="lth_ayutthaya"]';
let lthAyuFixed = 0;

function lthAyuFix() {
    let found;
    try {
        found = document.querySelectorAll(LTH_AYU_SELECTOR);
    } catch (e) {
        console.error(`LTH-AYU: panel query failed: ${e}`);
        return;
    }
    for (const el of found) {
        const bg = el.style.backgroundImage || '';
        if (bg.includes('blp:') && bg.includes('lth_ayutthaya')) {
            el.style.backgroundImage = LTH_AYU_ART;
            lthAyuFixed++;
            console.log(`LTH-AYU: panel art set (${lthAyuFixed})`);
        }
    }
}

setInterval(lthAyuFix, 1000);
console.log('LTH-AYU: panel art helper loaded');
