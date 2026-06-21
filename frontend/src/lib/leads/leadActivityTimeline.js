/** Слияние касаний и комментариев в единую ленту. */
import { activityTypeLabel } from '$lib/leads/leadActivityTypes.js';

/** @param {string | null | undefined} iso */
export function activityEffectiveAt(iso) {
	if (!iso) return 0;
	const t = Date.parse(iso);
	return Number.isNaN(t) ? 0 : t;
}

/** @param {Record<string, unknown>} row */
function commRow(row) {
	const at = row.occurredAt || row.createdAt;
	return {
		id: `comm-${row.id}`,
		kind: 'communication',
		type: String(row.communicationType || 'other'),
		label: activityTypeLabel(String(row.communicationType || 'other')),
		text: String(row.content || ''),
		actor: String(row.actor || 'Менеджер'),
		at,
		atMs: activityEffectiveAt(at),
	};
}

/** @param {Record<string, unknown>} row */
function commentRow(row) {
	const at = row.createdAt;
	return {
		id: `comment-${row.id}`,
		kind: 'comment',
		type: 'comment',
		label: 'Комментарий',
		text: String(row.body || ''),
		actor: String(row.author || 'Менеджер'),
		at,
		atMs: activityEffectiveAt(at),
	};
}

/**
 * @param {{ communications?: unknown[], comments?: unknown[] }} data
 * @returns {Array<ReturnType<typeof commRow>>}
 */
export function buildActivityTimeline(data) {
	const comms = (data.communications || []).map((r) => commRow(/** @type {Record<string, unknown>} */ (r)));
	const comments = (data.comments || []).map((r) => commentRow(/** @type {Record<string, unknown>} */ (r)));
	const seenCommentText = new Set(
		comms.filter((c) => c.type === 'comment').map((c) => `${c.text}|${c.atMs}`)
	);
	const legacyComments = comments.filter((c) => !seenCommentText.has(`${c.text}|${c.atMs}`));
	return [...comms, ...legacyComments].sort((a, b) => b.atMs - a.atMs);
}

/** @param {string | null | undefined} iso */
export function formatActivityWhen(iso) {
	if (!iso) return '—';
	try {
		return new Date(iso).toLocaleString('ru-RU', {
			day: '2-digit',
			month: '2-digit',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
		});
	} catch {
		return String(iso);
	}
}

/** Локальное значение для input datetime-local (сейчас). */
export function nowDatetimeLocalValue() {
	const d = new Date();
	d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
	return d.toISOString().slice(0, 16);
}

/** @param {string} localValue */
export function datetimeLocalToIso(localValue) {
	const s = String(localValue || '').trim();
	if (!s) return null;
	const d = new Date(s);
	if (Number.isNaN(d.getTime())) return null;
	return d.toISOString();
}
