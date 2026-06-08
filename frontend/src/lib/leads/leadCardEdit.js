/** Черновик полей карточки лида → PATCH /api/leads/{id} */

const DASH = '—';

function normDisplay(v) {
	const s = String(v ?? '').trim();
	return s === DASH ? '' : s;
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function detailsDraftFromLead(lead) {
	if (!lead) {
		return {
			company: '',
			contact: '',
			position: '',
			email: '',
			phone: '',
			website: '',
			industry: '',
			city: '',
			employees: '',
			budget: '',
			nextCall: '',
			scoreStr: '',
			description: '',
		};
	}
	return {
		company: normDisplay(lead.company),
		contact: normDisplay(lead.contact),
		position: normDisplay(lead.position),
		email: normDisplay(lead.email),
		phone: normDisplay(lead.phone),
		website: normDisplay(lead.website),
		industry: normDisplay(lead.industry),
		city: normDisplay(lead.city),
		employees: normDisplay(lead.employees),
		budget: normDisplay(lead.budget),
		nextCall: normDisplay(lead.nextCall ?? lead.next_call),
		scoreStr: lead.score != null && lead.score !== '' ? String(lead.score) : '',
		description: String(lead.description ?? '').trim(),
	};
}

/** @param {ReturnType<typeof detailsDraftFromLead>} draft */
export function patchFromDetailsDraft(draft) {
	const company = draft.company.trim();
	if (!company) throw new Error('Укажите название компании');

	const scoreRaw = draft.scoreStr.trim();
	let score;
	if (scoreRaw === '') {
		score = undefined;
	} else {
		const n = parseInt(scoreRaw, 10);
		if (Number.isNaN(n) || n < 0 || n > 100) {
			throw new Error('Скоринг — целое число от 0 до 100');
		}
		score = n;
	}

	const patch = {
		company,
		contact: draft.contact.trim() || DASH,
		position: draft.position.trim() || DASH,
		email: draft.email.trim() || DASH,
		phone: draft.phone.trim() || DASH,
		website: draft.website.trim() || DASH,
		industry: draft.industry.trim() || DASH,
		city: draft.city.trim() || DASH,
		employees: draft.employees.trim() || DASH,
		budget: draft.budget.trim() || DASH,
		next_call: draft.nextCall.trim() || DASH,
		description: draft.description.trim(),
	};
	if (score !== undefined) patch.score = score;
	return patch;
}
