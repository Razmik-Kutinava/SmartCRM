/** Smoke: порядок плиток хаба лида (DnD + localStorage). */
import {
	DEFAULT_HUB_TILE_ORDER,
	HUB_TILE_ORDER_KEY,
	moveHubTile,
	normalizeHubTileOrder,
	readHubTileOrder,
	sortTilesByOrder,
	writeHubTileOrder,
} from './hubTileOrder.js';

const def = DEFAULT_HUB_TILE_ORDER;
if (!Array.isArray(def) || def.length < 6) throw new Error('default order too short');
if (def[0] !== 'stages' || !def.includes('agents')) throw new Error('default ids');

const norm = normalizeHubTileOrder(['agents', 'stages', 'unknown', 'stages'], def);
if (norm[0] !== 'agents' || norm[1] !== 'stages') throw new Error('normalize head');
if (norm.filter((id) => id === 'stages').length !== 1) throw new Error('dedupe');
if (!norm.includes('products') || norm.includes('unknown')) throw new Error('merge defaults');
if (norm.length !== def.length) throw new Error('normalize length');

const moved = moveHubTile(def, 'agents', 'stages');
if (moved[0] !== 'agents' || moved[1] !== 'stages') throw new Error('move before target');
if (moveHubTile(def, 'stages', 'stages')[0] !== 'stages') throw new Error('noop same');
if (moveHubTile(def, 'nope', 'stages').join() !== def.join()) throw new Error('unknown from');

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
if (!raw || !raw.includes('tasks')) throw new Error('write');
const read = readHubTileOrder(storage);
if (read[0] !== 'tasks' || read[1] !== 'card' || !read.includes('stages')) throw new Error('read merge');

console.log('hubTileOrder smoke OK');
