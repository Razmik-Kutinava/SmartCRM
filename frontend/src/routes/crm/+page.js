import { redirect } from '@sveltejs/kit';

/** Совместимость: /crm → лиды */
export function load() {
	throw redirect(308, '/leads/list');
}
