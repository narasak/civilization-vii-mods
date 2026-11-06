// Upload a new build of the Workshop item through ISteamUGC, using the Steam client's existing login
// (no password, no steamcmd). Content and change note only: title, description, preview and
// visibility stay as they are. Run tools/package.sh first; it fills dist/lth-thai-language.
//
//   cd tools/steam && node update_item.mjs "change note"
//
// Measured 2026-11-06: as app 1295660 ISteamUGC updates pass (title, content); only the preview is
// refused (see set_preview.mjs).
import { createRequire } from 'node:module';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const steamworks = require('steamworks.js');

const APP_ID = 1295660;
const OWNER_ACCOUNT = 346951011;
const MOD = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const itemId = BigInt(readFileSync(join(MOD, 'workshop', 'published_id.txt'), 'utf8').trim());
const content = join(MOD, 'dist', 'lth-thai-language');
const note = process.argv[2];

if (!note) { console.error('usage: node update_item.mjs "change note"'); process.exit(1); }
if (!existsSync(join(content, 'thai-language.modinfo'))) {
    console.error('COULD NOT LOOK: no build in dist/lth-thai-language — run tools/package.sh first');
    process.exit(2);
}
const ver = /<Mod id="lth-thai-language" version="(\d+)"/.exec(readFileSync(join(content, 'thai-language.modinfo'), 'utf8'))?.[1];

let client;
try { client = steamworks.init(APP_ID); } catch (e) {
    console.error(`COULD NOT LOOK: Steam API did not initialise (Steam client running and online?): ${e.message}`);
    process.exit(2);
}
if (client.localplayer.getSteamId().accountId !== OWNER_ACCOUNT) {
    console.error(`Steam is not logged in as the item owner (${OWNER_ACCOUNT})`);
    process.exit(1);
}
console.log(`item ${itemId}: uploading version ${ver} from ${content}`);
try {
    await client.workshop.updateItem(itemId, { contentPath: content, changeNote: note }, APP_ID);
    console.log(`done: version ${ver} uploaded`);
    process.exit(0);
} catch (e) {
    console.error(`FAILED: ${e.message || e}`);
    process.exit(1);
}
