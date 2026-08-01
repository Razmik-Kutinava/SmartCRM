/** Маппинг enrich → PATCH лида. */
import { mergeCheckoJson, mergeTechJson } from '$lib/search/mergeLeadJson.js';

export function isValidPhone(phone) {
	const s = String(phone || '').trim();
	if (!s) return false;
	const digits = s.replace(/\D/g, '');
	return digits.length >= 10;
}

export function isValidEmail(email) {
	const s = String(email || '').trim();
	if (!s || !s.includes('@')) return false;
	const [local, domain] = s.split('@');
	return Boolean(local && domain && domain.includes('.'));
}

const EMAIL_FIND_RE = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g;

/** @param {unknown} obj @param {number} [depth] */
function walkStrings(obj, depth = 0) {
	if (depth > 6) return [];
	if (typeof obj === 'string') return [obj];
	if (Array.isArray(obj)) return obj.flatMap((v) => walkStrings(v, depth + 1));
	if (obj && typeof obj === 'object') {
		return Object.values(obj).flatMap((v) => walkStrings(v, depth + 1));
	}
	return [];
}

/**
 * Regex по bitrixExtra / tech.UF — то же, что бэкенд emails_from_bitrix_blobs.
 * @param {{ bitrixExtra?: Record<string, unknown>, tech?: Record<string, unknown> } | null | undefined} lead
 */
export function emailsFromBitrixBlobs(lead) {
	const chunks = [];
	if (lead?.bitrixExtra && typeof lead.bitrixExtra === 'object') {
		chunks.push(...walkStrings(lead.bitrixExtra));
	}
	// camelCase licenseRegistration тоже
	const lic = lead?.bitrixExtra?.licenseRegistration || lead?.bitrixExtra?.license_registration;
	if (lic) chunks.push(String(lic));
	const tech = lead?.tech;
	if (tech && typeof tech === 'object') {
		const uf = tech.bitrix24?.uf;
		chunks.push(...walkStrings(uf && typeof uf === 'object' ? uf : tech));
	}
	const found = [];
	for (const chunk of chunks) {
		const m = String(chunk).match(EMAIL_FIND_RE);
		if (m) found.push(...m);
	}
	return filterEmailList(found);
}

function filterEmailList(emails) {
	const out = [];
	const seen = new Set();
	for (const e of emails || []) {
		const s = String(e || '').trim();
		if (!isValidEmail(s)) continue;
		const key = s.toLowerCase();
		if (seen.has(key)) continue;
		seen.add(key);
		out.push(s);
	}
	return out;
}

/**
 * @param {Record<string, unknown> | null | undefined} checko
 * @param {unknown} lead
 */
export function mergeUfEmailsIntoChecko(checko, lead) {
	const base =
		checko && typeof checko === 'object' && !Array.isArray(checko) ? { ...checko } : {};
	const company =
		base.company && typeof base.company === 'object' && !Array.isArray(base.company)
			? { ...base.company }
			: {};
	const merged = filterEmailList([...(company.emails || []), ...emailsFromBitrixBlobs(lead)]);
	if (merged.length) {
		company.emails = merged;
		base.company = company;
	}
	return base;
}

/** CRM-поля из блока enriched. */
export function enrichedToLeadPatch(enriched) {
	if (!enriched || typeof enriched !== 'object') return {};
	const patch = {};
	if (enriched.phone && isValidPhone(enriched.phone)) patch.phone = enriched.phone;
	if (enriched.email && isValidEmail(enriched.email)) patch.email = enriched.email;
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

/**
 * @param {Array<Record<string, unknown>> | null | undefined} existingContacts
 * @param {Record<string, unknown> | null | undefined} passport
 * @param {Record<string, unknown> | null | undefined} lead
 */
function mergePassportContacts(existingContacts, passport, lead = null) {
	const list = Array.isArray(existingContacts) ? [...existingContacts] : [];

	const hasPhone = (phones, p) => {
		const dig = String(p || '').replace(/\D/g, '');
		return (phones || []).some((x) => String(x).replace(/\D/g, '') === dig);
	};
	const hasEmail = (emails, e) => {
		const low = String(e || '').trim().toLowerCase();
		return (emails || []).some((x) => String(x).trim().toLowerCase() === low);
	};
	const contactOverlap = (a, b) => {
		const ap = a?.phones || [];
		const ae = a?.emails || [];
		for (const p of b?.phones || []) if (hasPhone(ap, p)) return true;
		for (const e of b?.emails || []) if (hasEmail(ae, e)) return true;
		if (a?.name && b?.name && String(a.name).toLowerCase() === String(b.name).toLowerCase()) return true;
		return false;
	};

	// 1) Явные контакты из веб-extract / passport.contacts
	const webContacts = Array.isArray(passport?.contacts) ? passport.contacts : [];
	for (const c of webContacts) {
		if (!c || typeof c !== 'object') continue;
		const phones = (c.phones || []).filter(isValidPhone);
		const emails = (c.emails || []).filter(isValidEmail);
		const name = String(c.name || '').trim() || 'Контакт';
		const entry = {
			id: c.id || `web-${Date.now()}-${list.length}`,
			name,
			role: c.role === 'other' || c.role === 'gatekeeper' ? c.role : 'lpr',
			position: String(c.position || '').trim(),
			phones,
			emails,
			messengers: Array.isArray(c.messengers) ? c.messengers : [],
		};
		if (!phones.length && !emails.length && !name) continue;
		if (list.some((x) => contactOverlap(x, entry))) continue;
		list.push(entry);
	}

	// 2) Checko company → один LPR, если ещё нет LPR с телефонами/email
	const co = passport?.checko?.company || {};
	const phones = (co.phones || []).filter(isValidPhone);
	const emails = (co.emails || []).filter(isValidEmail);
	const director = co.director;
	const post = co.director_post;
	if (phones.length || emails.length || (director && director !== '—')) {
		const hasLpr = list.some((c) => c?.role === 'lpr' && (c.phones?.length || c.emails?.length));
		if (!hasLpr) {
			list.push({
				id: `checko-${Date.now()}`,
				name: director && director !== '—' ? director : 'Контакт компании',
				role: 'lpr',
				position: post && post !== '—' ? post : '',
				phones,
				emails,
				messengers: [],
			});
		}
	}

	// 3) lead.email / company.emails / UF → в ЛПР, если у него emails пусто
	// (иначе 🔍 и enrich находят почту, а в карточке контакта она не появляется)
	const spareEmails = filterEmailList([
		...(co.emails || []),
		...emailsFromBitrixBlobs(lead),
		lead?.email && lead.email !== '—' ? lead.email : '',
	]);
	if (spareEmails.length && list.length) {
		const lprIdx = list.findIndex((c) => c?.role === 'lpr');
		const idx = lprIdx >= 0 ? lprIdx : 0;
		const row = list[idx];
		const existing = filterEmailList(row.emails || []);
		// Только если у ЛПР почта пуста — не раздуваем уже заполненный контакт
		if (!existing.length) {
			list[idx] = { ...row, emails: spareEmails };
		}
	}

	return list.length ? list : existingContacts;
}

/** Полный ответ enrich-lead → PATCH (CRM + паспорт). */
export function enrichResultToLeadPatch(result, lead = null) {
	const patch = enrichedToLeadPatch(result?.enriched || {});
	const passport = result?.passport;
	if (!passport) {
		// Даже без нового passport — UF-почта может дописать company.emails на старом checko
		const ufChecko = mergeUfEmailsIntoChecko(lead?.checko, lead);
		if (ufChecko?.company?.emails?.length) {
			patch.checkoJson = mergeCheckoJson(lead?.checko, ufChecko);
			const spare = ufChecko.company.emails;
			if (spare[0] && (!lead?.email || lead.email === '—') && !patch.email) {
				patch.email = spare[0];
			}
			const mergedContacts = mergePassportContacts(lead?.contacts, { checko: ufChecko }, lead);
			if (mergedContacts?.length) patch.contacts = mergedContacts;
		}
		return patch;
	}

	if (passport.inn) patch.inn = passport.inn;
	if (passport.ogrn) patch.ogrn = passport.ogrn;
	if (passport.checko) {
		const withUf = mergeUfEmailsIntoChecko(passport.checko, lead);
		patch.checkoJson = mergeCheckoJson(lead?.checko, withUf);
	} else {
		const ufOnly = mergeUfEmailsIntoChecko(lead?.checko, lead);
		if (ufOnly?.company?.emails?.length) {
			patch.checkoJson = mergeCheckoJson(lead?.checko, ufOnly);
		}
	}
	if (passport.financials) patch.financialsJson = passport.financials;
	if (passport.tech && Object.keys(passport.tech).length) {
		patch.techJson = mergeTechJson(lead?.tech, passport.tech);
	}

	const cityEmpty = !lead?.city || lead.city === '—';
	const industryEmpty = !lead?.industry || lead.industry === '—';
	if (passport.city && cityEmpty) patch.city = passport.city;
	if (passport.industry && industryEmpty) patch.industry = passport.industry;

	// CRM phone/email из checko.company, если enriched пуст
	const checkoForCo = patch.checkoJson || passport.checko || {};
	const coPhones = (checkoForCo?.company?.phones || []).filter(isValidPhone);
	const coEmails = (checkoForCo?.company?.emails || []).filter(isValidEmail);
	if (coPhones[0] && !patch.phone && (!lead?.phone || lead.phone === '—')) patch.phone = coPhones[0];
	if (coEmails[0] && !patch.email && (!lead?.email || lead.email === '—')) patch.email = coEmails[0];

	const profKeys = [
		['okved_main', 'okvedMain'],
		['okved_name', 'okvedName'],
		['okved_section', 'okvedSection'],
		['employees_band', 'employeesBand'],
		['portrait_score', 'portraitScore'],
	];
	for (const [snake, camel] of profKeys) {
		if (passport[snake] != null && passport[snake] !== '') patch[camel] = passport[snake];
		if (passport[camel] != null && passport[camel] !== '') patch[camel] = passport[camel];
	}

	const co = checkoForCo?.company || {};
	if (co.employees_count != null && (!lead?.employees || lead.employees === '—')) {
		patch.employees = String(co.employees_count);
	}
	if (co.director && co.director !== '—' && (!lead?.contact || lead.contact === '—')) {
		patch.contact = co.director;
	}
	if (co.director_post && co.director_post !== '—' && (!lead?.position || lead.position === '—')) {
		patch.position = co.director_post;
	}

	const passportForMerge = {
		...passport,
		checko: patch.checkoJson || passport.checko,
	};
	const mergedContacts = mergePassportContacts(lead?.contacts, passportForMerge, lead);
	if (mergedContacts?.length) patch.contacts = mergedContacts;

	return patch;
}

/** @deprecated используй enrichResultToLeadPatch */
export function enrichedToLeadPatchWithPassport(result, lead) {
	return enrichResultToLeadPatch(result, lead);
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
		checko: lead.checko || undefined,
	};
}
