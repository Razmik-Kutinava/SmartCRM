/** Глобальный UI рассылки с карточки лида — store, без prop-drilling. */

import { derived, writable } from 'svelte/store';
import { isIndustryEmpty } from './industryCatalog.js';
import { openLeadIndustryModal } from './leadIndustryUi.js';

/** @type {import('svelte/store').Writable<object | null>} */
export const leadMailingLead = writable(null);

/** @type {import('svelte/store').Writable<boolean>} */
export const leadMailingOpen = writable(false);

function _openDrawer(lead) {
	leadMailingLead.set(lead);
	leadMailingOpen.set(true);
}

/** @param {object | null | undefined} lead */
export function openLeadMailing(lead) {
	if (!lead || lead.id == null) return;
	if (isIndustryEmpty(lead.industry)) {
		openLeadIndustryModal(lead, { onSaved: (saved) => _openDrawer(saved) });
		return;
	}
	_openDrawer(lead);
}

export function closeLeadMailing() {
	leadMailingOpen.set(false);
	leadMailingLead.set(null);
}

export const leadMailingVisible = derived(
	[leadMailingOpen, leadMailingLead],
	([open, lead]) => Boolean(open && lead && lead.id != null)
);
