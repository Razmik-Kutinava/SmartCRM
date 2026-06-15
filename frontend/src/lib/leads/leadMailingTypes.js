/** Типы рассылок с карточки лида — реестр для расширения. */

export const MAILING_TYPE_NURTURE = 'nurture';

/** @typedef {{ id: string, label: string, icon: string, description: string, enabled: (lead: object) => boolean }} LeadMailingType */

/** @type {LeadMailingType[]} */
export const LEAD_MAILING_TYPES = [
	{
		id: MAILING_TYPE_NURTURE,
		label: 'Цепочка касаний',
		icon: '🔗',
		description: 'LLM + RAG · 1 / 3 / 20 писем',
		enabled: (lead) => lead != null && lead.id != null,
	},
];

/** @param {object | null | undefined} lead */
export function enabledMailingTypes(lead) {
	return LEAD_MAILING_TYPES.filter((t) => t.enabled(lead));
}

/** @param {string} id */
export function getMailingType(id) {
	return LEAD_MAILING_TYPES.find((t) => t.id === id) ?? null;
}

/** Deep link на полную панель /email */
export function emailPanelDeepLink(leadId, panel = 'nurture') {
	return `/email?lead=${encodeURIComponent(String(leadId))}&panel=${encodeURIComponent(panel)}`;
}
