/** Smoke: порядок плиток хаба лида (DnD + localStorage). */
import {
	DEFAULT_HUB_TILE_ORDER,
	HUB_TILE_ORDER_KEY,
	migrateHubTileId,
	moveHubTile,
	normalizeHubTileOrder,
	readHubTileOrder,
	sortTilesByOrder,
	writeHubTileOrder,
} from './hubTileOrder.js';

const def = DEFAULT_HUB_TILE_ORDER;
if (!Array.isArray(def) || def.length !== 5) throw new Error('default order must be 5');
if (def[0] !== 'client' || !def.includes('agents')) throw new Error('default ids');
if (def.includes('stages') || def.includes('card')) throw new Error('legacy ids in default');

if (migrateHubTileId('stages') !== null) throw new Error('stages migrates to null');
if (migrateHubTileId('card') !== 'client') throw new Error('card→client');
if (migrateHubTileId('tasks') !== 'work') throw new Error('tasks→work');

const norm = normalizeHubTileOrder(['agents', 'stages', 'card', 'unknown', 'client'], def);
if (norm[0] !== 'agents' || norm[1] !== 'client') throw new Error('normalize head');
if (norm.filter((id) => id === 'client').length !== 1) throw new Error('dedupe client');
if (!norm.includes('products') || norm.includes('unknown') || norm.includes('stages')) {
	throw new Error('merge defaults');
}
if (norm.length !== def.length) throw new Error('normalize length');

const moved = moveHubTile(def, 'agents', 'client');
if (moved[0] !== 'agents' || moved[1] !== 'client') throw new Error('move before target');
if (moveHubTile(def, 'client', 'client')[0] !== 'client') throw new Error('noop same');
if (moveHubTile(def, 'nope', 'client').join() !== def.join()) throw new Error('unknown from');

const tiles = def.map((id) => ({ id, title: id }));
const sorted = sortTilesByOrder(tiles, ['emails', ...def.filter((id) => id !== 'emails')]);
if (sorted[0].id !== 'emails') throw new Error('sortTilesByOrder');

const mem = new Map();
const storage = {
	getItem: (k) => (mem.has(k) ? mem.get(k) : null),
	setItem: (k, v) => {
		mem.set(k, String(v));
	},
};
writeHubTileOrder(['tasks', 'card'], storage);
const raw = storage.getItem(HUB_TILE_ORDER_KEY);
if (!raw || !raw.includes('work') || !raw.includes('client')) throw new Error('write migrates');
const read = readHubTileOrder(storage);
if (read[0] !== 'work' || read[1] !== 'client') throw new Error('read order');

console.log('hubTileOrder.smoke.mjs OK');
