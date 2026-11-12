// Force Steam to download the Workshop item and wait until the local copy is a given version, so the
// Workshop copy can be diffed against dist/lth-thai-language. Steam did not auto-download the item
// while it was Hidden (2026-11-06), and an installed older copy makes installInfo() look "done" early.
//
//   cd tools/steam && node download_item.mjs <version> [itemId]   (version = modinfo version, e.g. 12;
//   itemId defaults to workshop/published_id.txt)
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const steamworks = require('steamworks.js');
const MOD = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const want = process.argv[2];
const itemId = BigInt(process.argv[3] || readFileSync(join(MOD, 'workshop', 'published_id.txt'), 'utf8').trim());
if (!/^\d+$/.test(want || '')) { console.error('usage: node download_item.mjs <version>'); process.exit(1); }

let c;
try { c = steamworks.init(1295660); } catch (e) {
    console.error(`COULD NOT LOOK: Steam API did not initialise (Steam client running and online?): ${e.message}`);
    process.exit(2);
}
const version = () => {
    try {
        const info = c.workshop.installInfo(itemId);
        return /version="(\d+)"/.exec(readFileSync(join(info.folder, 'thai-language.modinfo'), 'utf8'))[1];
    } catch { return null; }
};
console.log(`local version ${version() ?? 'none'}; DownloadItem -> ${c.workshop.download(itemId, true)}`);
for (let s = 1; s <= 180; s++) {
    await new Promise(r => setTimeout(r, 1000));
    if (version() === want) {
        console.log(`local copy is version ${want} after ${s}s: ${c.workshop.installInfo(itemId).folder}`);
        process.exit(0);
    }
}
console.error(`timed out after 180s; local version ${version() ?? 'none'}`);
process.exit(1);
