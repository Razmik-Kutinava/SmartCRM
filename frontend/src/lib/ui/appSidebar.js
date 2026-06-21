/** Сайдбар приложения: сворачивание и автоскрытие на карточке лида. */

const STORAGE_KEY = 'smartcrm-sidebar-collapsed';

const LEADS_SUBROUTES = new Set([
	'list',
	'funnel',
	'calendar',
	'tasks',
	'analytics',
	'focus',
	'campaign',
]);

/** `/leads/{id}` — карточка лида, не подразделы списка. */
export function isLeadCardRoute(pathname = '') {
	const m = String(pathname).match(/^\/leads\/([^/]+)$/);
	if (!m) return false;
	return !LEADS_SUBROUTES.has(m[1]);
}

export function readSidebarCollapsed() {
	if (typeof localStorage === 'undefined') return false;
	return localStorage.getItem(STORAGE_KEY) === '1';
}

export function writeSidebarCollapsed(collapsed) {
	if (typeof localStorage === 'undefined') return;
	localStorage.setItem(STORAGE_KEY, collapsed ? '1' : '0');
}
