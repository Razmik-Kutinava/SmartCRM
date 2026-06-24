/** Вкладка «Дела» — фильтры как в B24 (зеркало core/lead_activities_query.py). */

export const ACTIVITY_DUE_FILTERS = [
	['scheduled', 'Запланированные'],
	['today', 'Сегодня'],
	['tomorrow', 'Завтра'],
	['overdue', 'Просрочено'],
	['incoming', 'Входящие'],
	['all', 'Все дела'],
];

const ALLOWED = new Set(ACTIVITY_DUE_FILTERS.map(([id]) => id));

export function parseActivityDueFilter(raw) {
	return ALLOWED.has(raw) ? raw : 'scheduled';
}

/** @param {{ due?: string, manager?: string | null }} opts */
export function activitiesQueryParams({ due = 'scheduled', manager = null } = {}) {
	const out = new URLSearchParams();
	if (due && due !== 'scheduled') out.set('due', due);
	const mgr = manager && manager !== 'all' ? String(manager).trim() : '';
	if (mgr) out.set('manager', mgr);
	return out.toString();
}
