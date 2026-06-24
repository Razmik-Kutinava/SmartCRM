/** Слияние касаний, комментариев и дел B24 в единую ленту. */
import { activityTypeLabel } from '$lib/leads/leadActivityTypes.js';
import { parseTaskDue } from '$lib/tasks/taskSla.js';

/** @param {string | null | undefined} iso */
export function activityEffectiveAt(iso) {
	if (!iso) return 0;
	const t = Date.parse(iso);
	return Number.isNaN(t) ? 0 : t;
}

/** @param {string} note */
function b24MarkerFromNote(note) {
	const m = String(note || '').match(/^\[b24:(\w+):(\d+)\]/);
	return m ? `${m[1]}:${m[2]}` : '';
}

/** @param {string} content */
function b24MarkerFromContent(content) {
	const m = String(content || '').match(/^\[b24:(\w+):(\d+)\]/);
	return m ? `${m[1]}:${m[2]}` : '';
}

/** @param {Record<string, unknown>} row */
function commRow(row) {
	const at = row.occurredAt || row.createdAt;
	const raw = String(row.content || '');
	const text = raw.replace(/^\[b24:[^\]]+\]\s*/, '').trim() || raw;
	return {
		id: `comm-${row.id}`,
		kind: 'communication',
		type: String(row.communicationType || 'other'),
		label: activityTypeLabel(String(row.communicationType || 'other')),
		text,
		actor: String(row.actor || 'Менеджер'),
		at,
		atMs: activityEffectiveAt(at),
		b24Marker: b24MarkerFromContent(raw),
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
		b24Marker: '',
	};
}

/** @param {Record<string, unknown>} task */
function taskRow(task) {
	const note = String(task.note || '');
	const marker = b24MarkerFromNote(note);
	if (marker.startsWith('act:')) return null;
	const title = String(task.title || '').trim();
	const body = note.replace(/^\[b24:[^\]]+\]\s*/, '').trim();
	const text = body || title;
	const due = parseTaskDue(task.due);
	const atMs = due ? due.getTime() : activityEffectiveAt(task.createdAt);
	const at = due ? due.toISOString() : task.createdAt;
	const isMeeting = title.startsWith('Встреча') || title.startsWith('Звонок') || title.startsWith('Дело');
	return {
		id: `task-${task.id}`,
		kind: 'task',
		type: isMeeting ? 'meeting' : 'task',
		label: title.split(':')[0] || 'Задача',
		text,
		actor: String(task.assignee || 'Менеджер'),
		at,
		atMs,
		b24Marker: marker,
	};
}

/**
 * @param {{ communications?: unknown[], comments?: unknown[], tasks?: unknown[] }} data
 */
export function buildActivityTimeline(data) {
	const comms = (data.communications || []).map((r) => commRow(/** @type {Record<string, unknown>} */ (r)));
	const actMarkers = new Set(comms.map((c) => c.b24Marker).filter(Boolean));
	const comments = (data.comments || []).map((r) => commentRow(/** @type {Record<string, unknown>} */ (r)));
	const seenCommentText = new Set(
		comms.filter((c) => c.type === 'comment').map((c) => `${c.text}|${c.atMs}`)
	);
	const legacyComments = comments.filter((c) => !seenCommentText.has(`${c.text}|${c.atMs}`));
	const taskRows = (data.tasks || [])
		.map((r) => taskRow(/** @type {Record<string, unknown>} */ (r)))
		.filter(Boolean)
		.filter((t) => !t.b24Marker || !actMarkers.has(t.b24Marker));
	return [...comms, ...legacyComments, ...taskRows].sort((a, b) => b.atMs - a.atMs);
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
