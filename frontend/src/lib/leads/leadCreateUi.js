/** Модалка «Новый лид» — store + host (глобально из layout). */

import { writable, derived } from 'svelte/store';

/** @type {import('svelte/store').Writable<boolean>} */
export const leadCreateOpen = writable(false);

/** @type {import('svelte/store').Writable<string>} */
export const leadCreateSource = writable('UI');

/** @type {import('svelte/store').Writable<((lead: object) => void) | null>} */
const _onCreated = writable(null);

/** @param {{ source?: string, onCreated?: (lead: object) => void }} [opts] */
export function openLeadCreateModal(opts = {}) {
	leadCreateSource.set(opts.source || 'UI');
	_onCreated.set(typeof opts.onCreated === 'function' ? opts.onCreated : null);
	leadCreateOpen.set(true);
}

export function closeLeadCreateModal() {
	leadCreateOpen.set(false);
	_onCreated.set(null);
}

/** @param {object} lead */
export function notifyLeadCreated(lead) {
	let cb = null;
	const unsub = _onCreated.subscribe((v) => { cb = v; });
	unsub();
	if (cb) cb(lead);
}

export const leadCreateVisible = derived(leadCreateOpen, ($open) => $open);
