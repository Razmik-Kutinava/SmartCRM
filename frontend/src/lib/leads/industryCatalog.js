/** Отрасль лида — справочник и проверка пустоты */

import { apiFetch } from '$lib/api.js';

const EMPTY = new Set(['', '—', '-', 'null', 'undefined']);

export function isIndustryEmpty(value) {
	const s = String(value ?? '').trim();
	return !s || EMPTY.has(s);
}

export async function fetchLeadIndustries() {
	const data = await fetchLeadIndustryCatalog();
	return data.industries || [];
}

export async function fetchLeadIndustryCatalog() {
	const r = await apiFetch('/api/leads/industries');
	if (!r.ok) throw new Error(`industries ${r.status}`);
	const data = await r.json();
	return {
		industries: data.industries || [],
		items: data.items || [],
		withoutIndustryCount: data.withoutIndustryCount ?? 0,
	};
}

export async function saveLeadIndustry(leadId, { industry, industryVerified = true }) {
	const ind = String(industry || '').trim();
	if (!ind) throw new Error('Выбери отрасль');
	const { apiUpdateLead, fetchLeadById, fetchLeads, writeLeadsCache } = await import('$lib/leadsStorage.js');
	await apiUpdateLead(leadId, { industry: ind, industry_verified: Boolean(industryVerified) });
	await fetchLeadById(leadId);
	const fresh = await fetchLeads();
	writeLeadsCache(fresh);
	const updated = fresh.find((l) => l.id === leadId) || { id: leadId, industry: ind, industryVerified };
	try {
		const { leadMailingLead } = await import('$lib/leads/leadMailingUi.js');
		leadMailingLead.update((cur) => (cur?.id === leadId ? { ...cur, ...updated } : cur));
	} catch {
		/* store optional */
	}
	return updated;
}
