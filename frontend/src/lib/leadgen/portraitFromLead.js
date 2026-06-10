/** Заполняет поля портрета из карточки лида CRM. */
export function portraitFieldsFromLead(lead) {
	if (!lead) return {};
	const out = {};
	const inn = String(lead.inn || '').trim();
	if (inn) out.inn = inn;
	const industry = String(lead.industry || '').trim();
	if (industry && industry !== '—') out.industry = industry;
	const city = String(lead.city || '').trim();
	if (city && city !== '—') out.city = city;
	const emp = lead.employees;
	if (emp != null && emp !== '' && emp !== '—') {
		const n = parseInt(String(emp).replace(/\D/g, ''), 10);
		if (n > 0) out.empMin = String(n);
	}
	const rev =
		lead.financials?.revenue ??
		lead.checko?.revenue ??
		lead.budget;
	if (typeof rev === 'number' && rev > 0) {
		out.revenueMln = String(Math.round(rev / 1_000_000));
	}
	return out;
}
