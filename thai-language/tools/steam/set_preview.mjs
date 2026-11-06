// Set the Workshop item's main preview image through ISteamUGC::SetItemPreview.
//
// Why not steamcmd: workshop_build_item uploads the preview through legacy Steam Cloud, which Civ VII
// refuses ("Access Denied" after the content uploaded, 2026-11-06). ISteamUGC uses UGC storage.
//
//   cd tools/steam && npm install --ignore-scripts && node set_preview.mjs
//
// Needs the Steam client running, ONLINE, and logged in as the item's owner. Changes only the preview:
// title, description, content and visibility are left as they are.
//
// MEASURED 2026-11-06 on macOS, item 3834574849 — this does NOT work from a Mac:
//   as app 1295660 (the game):   preview -> 'access denied'; a title-only update -> OK
//   as app 3688890 (Dev Tools):  preview -> 'a generic failure' (Windows-only tool, not installed)
//   a NEW item made with ISteamUGC::CreateItem (item 3834585868): preview -> 'access denied' too, so it
//   is not the legacy-cloud storage of a steamcmd-created item; Civ VII refuses previews from any client
//   but its own uploader.
// The main preview has to be set once with the uploader in Civilization VII Development Tools on
// Windows. Later steamcmd updates run with --no-preview and leave it in place.
import { createRequire } from 'node:module';
import { readFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const steamworks = require('steamworks.js');

const APP_ID = 1295660;          // Sid Meier's Civilization VII: the Workshop the item lives in
// Run AS the game's Development Tools (Windows-only app, but the API needs only the licence). As the
// game itself, SetItemPreview is refused (access denied) while title updates pass (probe 2026-11-06).
const TOOLS_APP_ID = Number(process.env.LTH_STEAM_APP || 3688890);
const OWNER_ACCOUNT = 346951011; // [U:1:346951011], the account steamcmd created the item with
const MOD = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const itemId = BigInt(readFileSync(join(MOD, 'workshop', 'published_id.txt'), 'utf8').trim());
const preview = join(MOD, 'workshop', 'preview.png');

const size = statSync(preview).size;
if (size > 1024 * 1024) { console.error(`preview is ${size} bytes; Steam's limit is 1 MB`); process.exit(1); }

let client;
try {
    client = steamworks.init(TOOLS_APP_ID);
} catch (e) {
    console.error(`COULD NOT LOOK: Steam API did not initialise (is the Steam client running and online?): ${e.message}`);
    process.exit(2);
}
const me = client.localplayer.getSteamId();
if (me.accountId !== OWNER_ACCOUNT) {
    console.error(`Steam is logged in as account ${me.accountId}, not the item owner ${OWNER_ACCOUNT}`);
    process.exit(1);
}
console.log(`as app ${TOOLS_APP_ID}, item ${itemId}: uploading preview ${preview} (${size} bytes) as ${client.localplayer.getName()}`);
try {
    const r = await client.workshop.updateItem(itemId, { previewPath: preview, changeNote: 'Preview image' }, APP_ID);
    console.log(`done: item ${r.itemId}${r.needsToAcceptAgreement ? ' (account must accept the Workshop agreement)' : ''}`);
    process.exit(0);
} catch (e) {
    console.error(`FAILED: ${e.message || e}`);
    process.exit(1);
}
