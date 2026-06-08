/** Загрузка activity-блоков карточки лида (apiFetch + X-API-Key). */
import { fetchLeadAudit } from '$lib/leads/leadAudit.js';
import { fetchLeadComments } from '$lib/leads/leadComments.js';
import { fetchLeadCommunications } from '$lib/leads/leadCommunications.js';

export async function loadLeadCardActivity(leadId) {
	const n = Number(leadId);
	if (!leadId || Number.isNaN(n)) {
		return { comments: [], audit: [], communications: [] };
	}
	try {
		const [comments, audit, communications] = await Promise.all([
			fetchLeadComments(n, 40).catch(() => []),
			fetchLeadAudit(n, 35).catch(() => []),
			fetchLeadCommunications(n, 40).catch(() => []),
		]);
		return {
			comments,
			audit,
			communications,
		};
	} catch {
		return { comments: [], audit: [], communications: [] };
	}
}
