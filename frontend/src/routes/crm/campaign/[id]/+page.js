import { redirect } from '@sveltejs/kit';
import { CRM_REDIRECT_STATUS, crmCampaignRedirect } from '$lib/leads/crmRedirectMap.js';

export function load({ params }) {
	throw redirect(CRM_REDIRECT_STATUS, crmCampaignRedirect(params.id));
}
