// Upload a new build of the Workshop item through ISteamUGC, using the Steam client's existing login
// (no password, no steamcmd). Content and change note only: title, description, preview and
// visibility stay as they are. Run tools/package.sh first; it fills dist/lth-thai-language.
//
//   cd tools/steam && node update_item.mjs "change note"
//   node update_item.mjs "change note" --mod ../../../ayutthaya --content lth-ayutthaya --modinfo ayutthaya.modinfo --description
//
// --mod/--content/--modinfo point the same upload at another mod in this repo (default: the Thai pack).
// --description also sets the item description from <mod>/workshop/description.txt (measured 2026-11-12:
// ISteamUGC description updates work from the Mac; the official Uploader overwrites it on its own uploads).
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
const args = process.argv.slice(2);
const opt = (name, fallback) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : fallback; };
const HERE = dirname(fileURLToPath(import.meta.url));
const MOD = opt('--mod', null) ? join(process.cwd(), opt('--mod')) : join(HERE, '..', '..');
const CONTENT = opt('--content', 'lth-thai-language');
const MODINFO = opt('--modinfo', 'thai-language.modinfo');
const itemId = BigInt(readFileSync(join(MOD, 'workshop', 'published_id.txt'), 'utf8').trim());
const content = join(MOD, 'dist', CONTENT);
const note = args[0] && !args[0].startsWith('--') ? args[0] : null;

if (!note) { console.error('usage: node update_item.mjs "change note"'); process.exit(1); }
if (!existsSync(join(content, MODINFO))) {
    console.error(`COULD NOT LOOK: no build in ${content} (no ${MODINFO}) — build the mod's dist first`);
    process.exit(2);
}
const ver = /<Mod id="[^"]+" version="(\d+)"/.exec(readFileSync(join(content, MODINFO), 'utf8'))?.[1];
const update = { contentPath: content, changeNote: note };
if (args.includes('--description')) {
    update.description = readFileSync(join(MOD, 'workshop', 'description.txt'), 'utf8').trim();
}

let client;
try { client = steamworks.init(APP_ID); } catch (e) {
    console.error(`COULD NOT LOOK: Steam API did not initialise (Steam client running and online?): ${e.message}`);
    process.exit(2);
}
if (client.localplayer.getSteamId().accountId !== OWNER_ACCOUNT) {
    console.error(`Steam is not logged in as the item owner (${OWNER_ACCOUNT})`);
    process.exit(1);
}
console.log(`item ${itemId}: uploading version ${ver} from ${content}${update.description ? ' (with description)' : ''}`);
try {
    await client.workshop.updateItem(itemId, update, APP_ID);
    console.log(`done: version ${ver} uploaded`);
    process.exit(0);
} catch (e) {
    console.error(`FAILED: ${e.message || e}`);
    process.exit(1);
}
