/** Задачи лида в блоке «Действия» — сроки, сортировка, заголовки. */
import { parseTaskDue } from '$lib/tasks/taskSla.js';
import { activityTypeLabel } from '$lib/leads/leadActivityTypes.js';

/** @param {Date} d */
export function formatRuDate(d) {
	const dd = String(d.getDate()).padStart(2, '0');
	const mm = String(d.getMonth() + 1).padStart(2, '0');
	const yyyy = d.getFullYear();
	return `${dd}.${mm}.${yyyy}`;
}

/** @param {string} isoDate YYYY-MM-DD */
export function isoDateToRuDue(isoDate) {
	if (!isoDate) return '—';
	const m = String(isoDate).match(/^(\d{4})-(\d{2})-(\d{2})/);
	if (!m) return '—';
	return `${m[3]}.${m[2]}.${m[1]}`;
}

/** @param {string} local datetime-local value */
export function datetimeLocalToRuDue(local) {
	if (!local) return '—';
	const datePart = local.split('T')[0];
	return isoDateToRuDue(datePart);
}

/** @param {{ useCustomTime?: boolean, customTime?: string }} opts */
export function defaultScheduleDateIso(opts = {}) {
	if (opts.useCustomTime && opts.customTime) {
		const part = opts.customTime.split('T')[0];
		if (part) return part;
	}
	const t = new Date();
	t.setDate(t.getDate() + 1);
	const y = t.getFullYear();
	const m = String(t.getMonth() + 1).padStart(2, '0');
	const d = String(t.getDate()).padStart(2, '0');
	return `${y}-${m}-${d}`;
}

/** @param {Record<string, unknown>} task */
export function taskDueKind(task) {
	if (task.status === 'done') return 'done';
	const due = parseTaskDue(task.due);
	if (!due) return 'none';
	const now = new Date();
	now.setHours(0, 0, 0, 0);
	due.setHours(0, 0, 0, 0);
	if (due < now) return 'overdue';
	if (due.getTime() === now.getTime()) return 'today';
	return 'upcoming';
}

/** @param {Record<string, unknown>} task */
export function taskDueBadge(task) {
	const kind = taskDueKind(task);
	if (kind === 'overdue') return { label: 'Просрочено', cls: 'text-red-400 bg-red-950/50 border-red-900/50' };
	if (kind === 'today') return { label: 'Сегодня', cls: 'text-amber-300 bg-amber-950/40 border-amber-900/40' };
	if (kind === 'upcoming') return { label: 'Запланировано', cls: 'text-emerald-400/90 bg-emerald-950/30 border-emerald-900/30' };
	if (kind === 'done') return { label: 'Готово', cls: 'text-gray-500 bg-gray-900/50 border-gray-800' };
	return { label: 'Без срока', cls: 'text-gray-600 bg-gray-900/40 border-gray-800' };
}

/** @param {Record<string, unknown>[]} tasks */
export function sortOpenTasksByDue(tasks) {
	const open = (tasks || []).filter((t) => t.status !== 'done');
	const rank = { overdue: 0, today: 1, upcoming: 2, none: 3, done: 4 };
	return [...open].sort((a, b) => {
		const ka = taskDueKind(a);
		const kb = taskDueKind(b);
		if (rank[ka] !== rank[kb]) return rank[ka] - rank[kb];
		const da = parseTaskDue(a.due);
		const db = parseTaskDue(b.due);
		if (da && db) return da - db;
		if (da) return -1;
		if (db) return 1;
		return String(a.title || '').localeCompare(String(b.title || ''), 'ru');
	});
}

/**
 * @param {Record<string, unknown>[]} tasks
 * @param {{ expanded?: boolean, previewLimit?: number }} opts
 */
export function tasksForActivityPanel(tasks, opts = {}) {
	const previewLimit = opts.previewLimit ?? 4;
	const sorted = sortOpenTasksByDue(tasks);
	const expanded = Boolean(opts.expanded);
	if (expanded || sorted.length <= previewLimit) {
		return { items: sorted, hiddenCount: 0, totalOpen: sorted.length };
	}
	return {
		items: sorted.slice(0, previewLimit),
		hiddenCount: sorted.length - previewLimit,
		totalOpen: sorted.length,
	};
}

/** @param {string} type @param {string} text @param {string} [company] */
export function taskTitleFromActivity(type, text, company = '') {
	const label = activityTypeLabel(type);
	const snippet = (text || '').trim().replace(/\s+/g, ' ').slice(0, 72);
	if (snippet) return `${label}: ${snippet}`;
	if (company) return `${label} — ${company}`;
	return label;
}
