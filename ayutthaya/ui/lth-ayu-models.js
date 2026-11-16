/**
 * @file lth-ayu-models.js
 * @description Show 3D models on the Ubosot and Prang plots, which the game leaves empty.
 *
 * A mod cannot ship building art: the game loads art packages only from its own DLC folders
 * (ArtDef.log "No Packages found", 2026-11-16). But the UI layer can place any model the game
 * already has on a plot: WorldUI.createModelGroup() + modelGroup.addModelAtPlot(asset, plot, offset,
 * params). The base game does this itself (unit-flags/unit-info.js, tuner-input.js, world-vfx.js).
 * Learned from reading Sloth's "Custom Civ Art Fixes" (no licence: idea only, no code copied).
 *
 * TRIAL (2026-11-16): asset names, offsets and scale are first guesses to be judged in game.
 * Only completed buildings on plots the local player has revealed get a model.
 * Logging uses console.error, the only level this build writes to UI.log.
 */
const LTH_AYU_MODELS = {
    BUILDING_LTH_UBOSOT: { asset: 'BIN_Vihara_Scaled', offset: { x: -14, y: 6, z: 0 } },
    BUILDING_LTH_PRANG: { asset: 'BIN_Meru_Scaled', offset: { x: 14, y: -6, z: 0 } },
};
const lthAyuModelLog = (msg) => console.error(`LTH-AYU: ${msg}`);
const lthAyuPlots = new Map();          // "x,y" -> [{ asset, offset }]
let lthAyuGroup = null;
let lthAyuRebuildQueued = false;
const lthAyuRejected = new Set();

function lthAyuScanPlot(x, y) {
    const key = `${x},${y}`;
    const found = [];
    const observer = GameContext.localObserverID ?? GameContext.localPlayerID;
    if (GameplayMap.getRevealedState(observer, x, y) != RevealedStates.HIDDEN) {
        for (const id of MapConstructibles.getHiddenFilteredConstructibles(x, y) ?? []) {
            const c = Constructibles.getByComponentID(id);
            if (!c || !c.complete) {
                continue;
            }
            const type = GameInfo.Constructibles.lookup(c.type)?.ConstructibleType;
            const model = type && LTH_AYU_MODELS[type];
            if (model) {
                found.push(model);
            }
        }
    }
    const before = lthAyuPlots.has(key);
    if (found.length) {
        lthAyuPlots.set(key, found);
    } else {
        lthAyuPlots.delete(key);
    }
    return found.length > 0 || before;
}

function lthAyuRebuild() {
    lthAyuRebuildQueued = false;
    if (!lthAyuGroup) {
        return;
    }
    lthAyuGroup.clear();
    let placed = 0;
    for (const [key, models] of lthAyuPlots) {
        const [x, y] = key.split(',').map(Number);
        for (const m of models) {
            try {
                const params = { placement: PlacementMode.TERRAIN, angle: 0, scale: 1, needsShadows: true, initialState: 'IDLE' };
                const model = lthAyuGroup.addModelAtPlot(m.asset, { i: x, j: y }, m.offset, params);
                if (model === undefined || model === null) {
                    if (!lthAyuRejected.has(m.asset)) {
                        lthAyuRejected.add(m.asset);
                        lthAyuModelLog(`model ${m.asset} rejected by the engine`);
                    }
                } else {
                    placed++;
                }
            } catch (e) {
                lthAyuModelLog(`model ${m.asset} failed at ${key}: ${e}`);
            }
        }
    }
    lthAyuModelLog(`models placed: ${placed} on ${lthAyuPlots.size} plot(s)`);
}

function lthAyuQueueRebuild() {
    if (!lthAyuRebuildQueued) {
        lthAyuRebuildQueued = true;
        setTimeout(lthAyuRebuild, 250);
    }
}

function lthAyuOnPlotEvent(data) {
    const loc = data?.location;
    if (loc && lthAyuScanPlot(loc.x, loc.y)) {
        lthAyuQueueRebuild();
    }
}

function lthAyuFullScan() {
    lthAyuPlots.clear();
    const w = GameplayMap.getGridWidth();
    const h = GameplayMap.getGridHeight();
    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            lthAyuScanPlot(x, y);
        }
    }
    lthAyuQueueRebuild();
}

function lthAyuModelsInit() {
    if (typeof WorldUI === 'undefined' || !WorldUI.createModelGroup || typeof MapConstructibles === 'undefined') {
        lthAyuModelLog('models: game APIs not ready, not starting');
        return;
    }
    lthAyuGroup = WorldUI.createModelGroup('LTH_AYU_WatModels');
    for (const ev of ['ConstructibleAddedToMap', 'ConstructibleBuildCompleted', 'ConstructibleRemovedFromMap',
        'ConstructibleChanged', 'ConstructibleVisibilityChanged', 'PlotVisibilityChanged']) {
        engine.on(ev, lthAyuOnPlotEvent);
    }
    engine.on('LocalPlayerChanged', lthAyuFullScan);
    lthAyuFullScan();
    lthAyuModelLog('models helper (trial) loaded');
}

// The map and gameplay APIs are ready once the game has loaded; wait for that before scanning.
if (typeof engine !== 'undefined' && engine.whenReady) {
    engine.whenReady.then(() => setTimeout(lthAyuModelsInit, 1000));
} else {
    setTimeout(lthAyuModelsInit, 3000);
}
