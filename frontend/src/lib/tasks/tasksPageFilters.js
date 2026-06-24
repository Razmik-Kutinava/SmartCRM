/** Фильтры страницы /leads/tasks — зеркало backend/tests/lib/test_tasks_page_filters.py */

export const TASK_STATUS_FILTERS = [
	['all', 'Все'],
	['open', 'Открытые'],
	['done', 'Выполненные'],
];

export const TASK_DUE_FILTERS = [
	['all', 'Все сроки'],
	['today', 'Сегодня'],
	['tomorrow', 'Завтра'],
	['overdue', 'Просрочено'],
	['scheduled', 'Запланированные'],
];

const STATUS_ALLOWED = new Set(TASK_STATUS_FILTERS.map(([id]) => id));
const DUE_ALLOWED = new Set(TASK_DUE_FILTERS.map(([id]) => id));

/** Старый ?filter= для обратной совместимости */
const LEGACY_FILTER_MAP = {
	all: ['all', 'all', false],
	open: ['open', 'all', false],
	done: ['done', 'all', false],
	today: ['open', 'today', false],
	tomorrow: ['open', 'tomorrow', false],
	overdue: ['open', 'overdue', false],
	scheduled: ['open', 'scheduled', false],
	escalated: ['open', 'all', true],
};

export function parseTaskStatusFilter(raw) {
	return STATUS_ALLOWED.has(raw) ? raw : 'all';
}

export function parseTaskDueFilter(raw) {
	return DUE_ALLOWED.has(raw) ? raw : 'all';
}

export function parseLegacyTasksFilter(raw) {
	const row = LEGACY_FILTER_MAP[raw] || LEGACY_FILTER_MAP.all;
	return { taskStatus: row[0], dueFilter: row[1], escalatedOnly: row[2] };
}

/** Параметры для fetchTasks */
export function tasksFetchParams({ taskStatus = 'all', dueFilter = 'all', escalatedOnly = false } = {}) {
	const out = {};
	if (taskStatus && taskStatus !== 'all') out.taskStatus = taskStatus;
	if (dueFilter && dueFilter !== 'all') out.due = dueFilter;
	if (escalatedOnly) out.escalated = true;
	return out;
}
