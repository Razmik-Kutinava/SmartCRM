/** Порядок плиток хаба карточки лида: DnD + localStorage.
 * DEFAULT_HUB_TILE_ORDER должен совпадать с id в HUB_PANELS (leadHubPreview.js).
 */

export const HUB_TILE_ORDER_KEY = 'smartcrm-lead-hub-tile-order';
export const HUB_TILE_DRAG_MIME = 'application/x-smartcrm-hub-tile-id';

/** Канон порядка = HUB_PANELS в leadHubPreview.js */
export const DEFAULT_HUB_TILE_ORDER = [
	'stages',
	'products',
	'card',
	'activity',
	'passport',
	'tasks',
	'emails',
	'agents',
];

/** @param {string[] | null | undefined} saved @param {string[]} [defaults] */
export function normalizeHubTileOrder(saved, defaults = DEFAULT_HUB_TILE_ORDER) {
	const def = [...defaults];
	const seen = new Set();
	const out = [];
	if (Array.isArray(saved)) {
		for (const id of saved) {
			if (typeof id !== 'string') continue;
			if (def.includes(id) && !seen.has(id)) {
				out.push(id);
				seen.add(id);
			}
		}
	}
	for (const id of def) {
		if (!seen.has(id)) out.push(id);
	}
	return out;
}

/** Переставить fromId на место toId (вставка перед целью). */
export function moveHubTile(order, fromId, toId) {
	const base = Array.isArray(order) ? [...order] : [...DEFAULT_HUB_TILE_ORDER];
	if (fromId === toId) return base;
	const fromIdx = base.indexOf(fromId);
	if (fromIdx < 0) return base;
	const without = base.filter((id) => id !== fromId);
	const insertAt = without.indexOf(toId);
	if (insertAt < 0) return base;
	without.splice(insertAt, 0, fromId);
	return without;
}

/** @param {Array<{ id: string }>} tiles @param {string[]} order */
export function sortTilesByOrder(tiles, order) {
	const idx = Object.fromEntries(
		(Array.isArray(order) ? order : DEFAULT_HUB_TILE_ORDER).map((id, i) => [id, i])
	);
	return [...tiles].sort((a, b) => (idx[a.id] ?? 999) - (idx[b.id] ?? 999));
}

/** @param {{ getItem?: (k: string) => string | null } | null | undefined} storage */
export function readHubTileOrder(storage) {
	const store = storage ?? (typeof localStorage !== 'undefined' ? localStorage : null);
	if (!store?.getItem) return [...DEFAULT_HUB_TILE_ORDER];
	try {
		const raw = store.getItem(HUB_TILE_ORDER_KEY);
		if (!raw) return [...DEFAULT_HUB_TILE_ORDER];
		return normalizeHubTileOrder(JSON.parse(raw));
	} catch {
		return [...DEFAULT_HUB_TILE_ORDER];
	}
}

/** @param {string[]} order @param {{ setItem?: (k: string, v: string) => void } | null | undefined} storage */
export function writeHubTileOrder(order, storage) {
	const store = storage ?? (typeof localStorage !== 'undefined' ? localStorage : null);
	if (!store?.setItem) return;
	try {
		store.setItem(HUB_TILE_ORDER_KEY, JSON.stringify(normalizeHubTileOrder(order)));
	} catch {
		/* квота / private mode */
	}
}

/** @param {DragEvent} e @param {string} tileId */
export function setHubTileDragData(e, tileId) {
	if (!e.dataTransfer) return;
	e.dataTransfer.setData(HUB_TILE_DRAG_MIME, String(tileId));
	e.dataTransfer.setData('text/plain', String(tileId));
	e.dataTransfer.effectAllowed = 'move';
}

/** @param {DataTransfer | null | undefined} dt */
export function parseHubTileDragId(dt) {
	if (!dt) return null;
	const raw = dt.getData(HUB_TILE_DRAG_MIME) || dt.getData('text/plain');
	const id = String(raw || '').trim();
	return id || null;
}
