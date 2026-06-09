/** Маппинг enrich → PATCH лида. */
export function enrichedToLeadPatch(enriched) {
	if (!enriched || typeof enriched !== 'object') return {};
	const patch = {};
	if (enriched.phone) patch.phone = enriched.phone;
	if (enriched.email) patch.email = enriched.email;
	if (enriched.website) patch.website = enriched.website;
	if (enriched.employees) patch.employees = enriched.employees;
	if (enriched.revenue) patch.budget = String(enriched.revenue);
	if (enriched.decision_maker) patch.contact = enriched.decision_maker;

	const descParts = [];
	if (enriched.description) descParts.push(enriched.description);
	if (enriched.address) descParts.push(`Адрес: ${enriched.address}`);
	if (enriched.linkedin) descParts.push(`LinkedIn: ${enriched.linkedin}`);
	if (descParts.length) patch.description = descParts.join('\n');

	return patch;
}

/** Лид из CRM → тело enrich-lead. */
export function leadToEnrichPayload(lead) {
	if (!lead) return null;
	return {
		company: lead.company || '',
		industry: lead.industry && lead.industry !== '—' ? lead.industry : '',
		inn: lead.inn || undefined,
		phone: lead.phone,
		email: lead.email,
		website: lead.website,
		address: lead.city,
		employees: lead.employees,
		description: lead.description,
	};
}
