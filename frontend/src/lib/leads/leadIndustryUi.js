/** Модалка «указать отрасль» — store + host */

import { writable, derived } from 'svelte/store';

/** @type {import('svelte/store').Writable<object | null>} */
export const leadIndustryLead = writable(null);

/** @type {import('svelte/store').Writable<boolean>} */
export const leadIndustryOpen = writable(false);

/** @type {import('svelte/store').Writable<((lead: object) => void) | null>} */
const _onSaved = writable(null);

/** @param {object} lead @param {{ onSaved?: (lead: object) => void }} [opts] */
export function openLeadIndustryModal(lead, opts = {}) {
	if (!lead?.id) return;
	leadIndustryLead.set(lead);
	_onSaved.set(typeof opts.onSaved === 'function' ? opts.onSaved : null);
	leadIndustryOpen.set(true);
}

export function closeLeadIndustryModal() {
	leadIndustryOpen.set(false);
	leadIndustryLead.set(null);
	_onSaved.set(null);
}

export function notifyLeadIndustrySaved(lead) {
	let cb = null;
	const unsub = _onSaved.subscribe((v) => { cb = v; });
	unsub();
	if (cb) cb(lead);
}

export const leadIndustryVisible = derived(
	[leadIndustryOpen, leadIndustryLead],
	([open, lead]) => Boolean(open && lead?.id),
);
