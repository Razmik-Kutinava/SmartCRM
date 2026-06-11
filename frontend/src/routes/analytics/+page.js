import { redirect } from '@sveltejs/kit';

/** Убрать mock `/analytics` → канон `/leads/analytics`. */
export function load() {
	throw redirect(308, '/leads/analytics');
}
