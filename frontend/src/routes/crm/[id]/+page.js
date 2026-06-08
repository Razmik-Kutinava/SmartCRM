import { redirect } from '@sveltejs/kit';
import { CRM_REDIRECT_STATUS, crmLeadIdRedirect } from '$lib/leads/crmRedirectMap.js';

export function load({ params }) {
	throw redirect(CRM_REDIRECT_STATUS, crmLeadIdRedirect(params.id));
}
