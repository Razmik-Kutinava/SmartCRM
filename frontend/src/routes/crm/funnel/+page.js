import { redirect } from '@sveltejs/kit';
import { CRM_REDIRECT_STATUS, CRM_STATIC_REDIRECTS } from '$lib/leads/crmRedirectMap.js';

export function load() {
	throw redirect(CRM_REDIRECT_STATUS, CRM_STATIC_REDIRECTS['/crm/funnel']);
}
