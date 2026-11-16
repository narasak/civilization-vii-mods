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
            console.error(`LTH-AYU: panel art set (${lthAyuFixed})`);
        }
    }
}

/*
 * Civilization details screen (2026-11-16). civ-details.js passes model.selectedCiv().bgImage, i.e.
 * "bg-panel-lth_ayutthaya", to the create-game stage, which hands it to WorldUI.addBackgroundLayer
 * (components/scene-3d.js). That 3D layer takes only textures packed in the game's files, so ours drew
 * black. For that one texture name we pass Siam's packed panel instead, the same borrowing the loading
 * screen already does (data/icons/icons.xml). Learned from reading the "Civilization Background Framework"
 * description (no licence: idea only, no code copied). Every other texture goes through untouched.
 */
const LTH_AYU_STAGE_FROM = 'bg-panel-lth_ayutthaya';
const LTH_AYU_STAGE_TO = 'bg-panel-siam';

function lthAyuHookStage() {
    if (typeof WorldUI === 'undefined' || !WorldUI.addBackgroundLayer || WorldUI.__lthAyuStageHooked) {
        return;
    }
    const original = WorldUI.addBackgroundLayer.bind(WorldUI);
    WorldUI.addBackgroundLayer = function (texture, params, pass) {
        if (typeof texture === 'string' && texture.toLowerCase().startsWith(LTH_AYU_STAGE_FROM)) {
            return original(LTH_AYU_STAGE_TO, params, pass);
        }
        return original(texture, params, pass);
    };
    WorldUI.__lthAyuStageHooked = true;
    console.error('LTH-AYU: details background hook installed');
}

lthAyuHookStage();
setInterval(lthAyuFix, 1000);
console.error('LTH-AYU: panel art helper loaded');
