/** Канонический список экранов `/leads/*` для смоука и регрессии. */

export const LEADS_ROOT_REDIRECT = '/leads/list';

/** Вкладки в `leads/+layout.svelte` */
export const LEADS_TAB_ROUTES = [
	'/leads/funnel',
	'/leads/list',
	'/leads/calendar',
	'/leads/tasks',
	'/leads/focus',
	'/leads/analytics',
];

/** Статические пути (включая корень) */
export const LEADS_STATIC_ROUTES = ['/leads', ...LEADS_TAB_ROUTES];

/** @param {string | number} id */
export function leadsCardPath(id) {
	return `/leads/${id}`;
}

/** @param {string | number} id */
export function leadsCampaignPath(id) {
	return `/leads/campaign/${id}`;
}
