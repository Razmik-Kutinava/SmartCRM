/** Глобальный UI рассылки с карточки лида — store, без prop-drilling. */

import { derived, writable } from 'svelte/store';

/** @type {import('svelte/store').Writable<object | null>} */
export const leadMailingLead = writable(null);

/** @type {import('svelte/store').Writable<boolean>} */
export const leadMailingOpen = writable(false);

/** @param {object | null | undefined} lead */
export function openLeadMailing(lead) {
	if (!lead || lead.id == null) return;
	leadMailingLead.set(lead);
	leadMailingOpen.set(true);
}

export function closeLeadMailing() {
	leadMailingOpen.set(false);
	leadMailingLead.set(null);
}

export const leadMailingVisible = derived(
	[leadMailingOpen, leadMailingLead],
	([open, lead]) => Boolean(open && lead && lead.id != null)
);
