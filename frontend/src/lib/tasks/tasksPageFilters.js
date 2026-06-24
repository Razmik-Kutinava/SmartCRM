/** Фильтры страницы /leads/tasks — зеркало в backend/tests/lib/test_tasks_page_filters.py */

export const TASK_PAGE_FILTERS = [
	['all', 'Все'],
	['today', 'Сегодня'],
	['overdue', 'Просрочено'],
	['open', 'Открытые'],
	['escalated', 'Эскалация'],
];

const ALLOWED = new Set(TASK_PAGE_FILTERS.map(([id]) => id));

/** query ?filter= из URL */
export function parseTasksPageFilter(raw) {
	return ALLOWED.has(raw) ? raw : 'all';
}

/** Параметры для fetchTasks */
export function tasksFetchParams(filter) {
	return filter === 'all' ? {} : { status: filter };
}
