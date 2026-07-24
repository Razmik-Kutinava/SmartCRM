/** Мета для вкладки Клиент→Карточка (адрес/ОКВЭД из lead+checko, без правок Паспорта). */

import { passportSource } from '$lib/leads/leadPassport.js';

const DASH = '—';

function clean(v) {
	const s = String(v ?? '').trim();
	if (!s || s === DASH) return '';
	return s;
}

/**
 * Юр./фактический адрес из Checko (read-only на карточке).
 * @param {Record<string, unknown> | null | undefined} lead
 */
export function cardAddressFromLead(lead) {
	const { co } = passportSource(lead);
	const candidates = [
		co.address,
		co.Адрес,
		co.legal_address,
		co.legalAddress,
		co.full_address,
		typeof co.address_full === 'string' ? co.address_full : '',
	];
	for (const c of candidates) {
		const s = clean(c);
		if (s) return s;
	}
	return '';
}

/**
 * Строка ОКВЭД для карточки (поля лида или Checko).
 * @param {Record<string, unknown> | null | undefined} lead
 */
export function cardOkvedLineFromLead(lead) {
	const main = clean(lead?.okvedMain ?? lead?.okved_main);
	const name = clean(lead?.okvedName ?? lead?.okved_name);
	if (main && name) return `${main} — ${name}`;
	if (main) return main;
	if (name) return name;
	const { co } = passportSource(lead);
	const code = clean(co.okved);
	const coName = clean(co.okved_name);
	if (code && coName) return `${code} — ${coName}`;
	return code || coName || '';
}

/** Канонический порядок секций (Апрув 1). */
export const CLIENT_CARD_SECTION_IDS = [
	'company',
	'contacts',
	'website',
	'industry',
	'employees',
	'turnover',
	'agents',
	'system',
	'bitrix-uf',
];
