/** Редиректы /crm/* → /leads/* (308, обратная совместимость). */

export const CRM_REDIRECT_STATUS = 308;

/** @type {Record<string, string>} */
export const CRM_STATIC_REDIRECTS = {
	'/crm': '/leads/list',
	'/crm/list': '/leads/list',
	'/crm/funnel': '/leads/funnel',
	'/crm/calendar': '/leads/calendar',
	'/crm/tasks': '/leads/tasks',
	'/crm/focus': '/leads/focus',
	'/crm/analytics': '/leads/analytics',
};

/** @param {string | number} leadId */
export function crmLeadIdRedirect(leadId) {
	return `/leads/${leadId}`;
}

/** @param {string | number} campaignId */
export function crmCampaignRedirect(campaignId) {
	return `/leads/campaign/${campaignId}`;
}
