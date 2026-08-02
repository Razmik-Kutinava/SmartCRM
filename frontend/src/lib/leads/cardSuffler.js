/** Суфлёр карточки: чего не хватает для полноты работы с клиентом (зеркало backend agent_gaps). */

const FIELD_HINTS = {
	inn: 'ИНН',
	okved: 'ОКВЭД / вид деятельности',
	industry: 'отрасль',
	contact: 'ЛПР / контактное лицо',
	email: 'email',
	phone: 'телефон',
	financials: 'фин. показатели (выручка / обороты в паспорте)',
	website: 'сайт / домен',
	employees: 'численность сотрудников',
	tech_stack: 'технологии клиента (сайт / раздел ИТ в исследовании)',
	web_research: 'веб-исследование (кнопка 🔍 Исследовать)',
};

const CARD_PRIORITY = [
	'inn',
	'okved',
	'industry',
	'contact',
	'email',
	'phone',
	'financials',
	'website',
	'employees',
	'tech_stack',
	'web_research',
];

const FIN_BRIEF_MARKERS = [
	'выручка',
	'оборот',
	'млн руб',
	'млрд',
	'revenue',
	'фин.',
	'финанс',
	'прибыль',
	'убыток',
	'баланс',
];

function filled(value) {
	if (value == null) return false;
	if (Array.isArray(value) || (typeof value === 'object' && value)) {
		return Object.keys(value).length > 0 || (Array.isArray(value) && value.length > 0);
	}
	const text = String(value).trim();
	return Boolean(text) && !['—', '-', 'нет', 'n/a', 'None'].includes(text);
}

function phoneOk(p) {
	return filled(p) && String(p).replace(/\D/g, '').length >= 10;
}

function phonesAnywhere(lead, company, wr) {
	if (phoneOk(lead?.phone)) return true;
	for (const p of company.phones || []) if (phoneOk(p)) return true;
	for (const c of lead?.contacts || []) {
		for (const p of c?.phones || []) if (phoneOk(p)) return true;
	}
	const extract = wr.passport_extract && typeof wr.passport_extract === 'object' ? wr.passport_extract : {};
	for (const p of extract.phones || []) if (phoneOk(p)) return true;
	return false;
}

function emailsAnywhere(lead, company, wr) {
	if (filled(lead?.email) && String(lead.email).includes('@')) return true;
	for (const e of company.emails || []) if (filled(e) && String(e).includes('@')) return true;
	for (const c of lead?.contacts || []) {
		for (const e of c?.emails || []) if (filled(e) && String(e).includes('@')) return true;
	}
	const extract = wr.passport_extract && typeof wr.passport_extract === 'object' ? wr.passport_extract : {};
	for (const e of extract.emails || []) if (filled(e) && String(e).includes('@')) return true;
	return false;
}

function contactAnywhere(lead, company) {
	if (filled(lead?.contact)) return true;
	if (filled(company.director) && company.director !== '—') return true;
	for (const c of lead?.contacts || []) if (filled(c?.name)) return true;
	return false;
}

function financialsAnywhere(lead, company, fin, brief) {
	if (filled(fin)) return true;
	if (filled(lead?.financials)) return true;
	if (filled(lead?.budget) || filled(lead?.amount_rub)) return true;
	for (const key of ['revenue', 'turnover', 'выручка', 'оборот', 'income']) {
		if (filled(company[key])) return true;
	}
	const low = String(brief || '').toLowerCase();
	return FIN_BRIEF_MARKERS.some((m) => low.includes(m));
}

function presenceFromLead(lead) {
	const checko = lead?.checko && typeof lead.checko === 'object' ? lead.checko : {};
	const company = checko.company && typeof checko.company === 'object' ? checko.company : {};
	const analyses = checko.analyses && typeof checko.analyses === 'object' ? checko.analyses : {};
	const wr =
		analyses.web_research && typeof analyses.web_research === 'object'
			? analyses.web_research
			: {};
	const brief = String(wr.agent_brief || wr.summary || '').trim();
	const fin = checko.financials || lead?.financials;
	let tech = lead?.tech || checko.tech || {};
	if (typeof tech === 'string') {
		try {
			tech = JSON.parse(tech);
		} catch {
			tech = {};
		}
	}
	const dns =
		(wr.domain_signals && typeof wr.domain_signals === 'object' && wr.domain_signals) ||
		(tech.domain_signals && typeof tech.domain_signals === 'object' && tech.domain_signals) ||
		{};
	const inn = lead?.inn || company.inn;
	const okved = company.okved || company.okved_name || lead?.okved;
	const techFilled = Boolean(
		(tech &&
			(tech.all_technologies?.length ||
				tech.cms?.length ||
				tech.by_category ||
				tech.maturity_level)) ||
			brief.includes('## 6') ||
			brief.includes('BuiltWith') ||
			dns.has_mx ||
			dns.summary,
	);

	return {
		inn: filled(inn),
		okved: filled(okved),
		industry: filled(lead?.industry) || filled(company.industry) || filled(company.okved_name),
		contact: contactAnywhere(lead, company),
		email: emailsAnywhere(lead, company, wr),
		phone: phonesAnywhere(lead, company, wr),
		financials: financialsAnywhere(lead, company, fin, brief),
		website: filled(lead?.website) || filled(company.website),
		employees: filled(lead?.employees) || filled(company.employees) || filled(company.employees_count),
		tech_stack: techFilled,
		web_research: Boolean(brief) && !brief.toLowerCase().startsWith('ошибка'),
	};
}

/** @param {Record<string, any> | null | undefined} lead */
export function cardSufflerFromLead(lead) {
	const presence = presenceFromLead(lead || {});
	const missing_keys = [];
	const gaps = [];
	for (const key of CARD_PRIORITY) {
		if (!presence[key]) {
			missing_keys.push(key);
			gaps.push(FIELD_HINTS[key] || key);
		}
	}
	return {
		ok: missing_keys.length === 0,
		gaps,
		missing_keys,
	};
}
