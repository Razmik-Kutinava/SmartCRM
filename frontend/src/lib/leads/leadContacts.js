/** Контакты лида: черновик → PATCH contacts */
import { CONTACT_ROLE_OPTIONS } from './leadContactRoles.js';

export { CONTACT_ROLE_OPTIONS };

function linesToList(text) {
	return String(text || '')
		.split(/\r?\n/)
		.map((s) => s.trim())
		.filter(Boolean);
}

function listToLines(list) {
	if (!Array.isArray(list)) return '';
	return list.filter(Boolean).join('\n');
}

function newContactDraft(role = 'other') {
	return {
		id: crypto.randomUUID?.() || `c${Date.now()}`,
		name: '',
		role,
		position: '',
		phonesText: '',
		emailsText: '',
		messengersText: '',
	};
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function contactsDraftFromLead(lead) {
	const raw = lead?.contacts;
	if (Array.isArray(raw) && raw.length) {
		return raw.map((c) => ({
			id: String(c.id || crypto.randomUUID?.() || `c${Date.now()}`),
			name: String(c.name || '').trim(),
			role: String(c.role || 'other'),
			position: String(c.position || '').trim(),
			phonesText: listToLines(c.phones),
			emailsText: listToLines(c.emails),
			messengersText: listToLines(c.messengers),
		}));
	}
	const name = String(lead?.contact || '').trim();
	if (!name || name === '—') return [];
	return [
		{
			id: 'legacy',
			name,
			role: 'lpr',
			position: String(lead?.position || '').replace(/^—$/, '').trim(),
			phonesText: listToLines([lead?.phone].filter((p) => p && p !== '—')),
			emailsText: listToLines([lead?.email].filter((e) => e && e !== '—')),
			messengersText: '',
		},
	];
}

/** @param {ReturnType<typeof contactsDraftFromLead>} draft */
export function contactsPatchFromDraft(draft) {
	return draft
		.map((c) => ({
			id: c.id,
			name: c.name.trim(),
			role: c.role || 'other',
			position: c.position.trim(),
			phones: linesToList(c.phonesText),
			emails: linesToList(c.emailsText),
			messengers: linesToList(c.messengersText),
		}))
		.filter((c) => c.name || c.position || c.phones.length || c.emails.length || c.messengers.length);
}

export function isLprContactComplete(contact) {
	if (contact.role !== 'lpr') return false;
	const name = String(contact.name || '').trim();
	const position = String(contact.position || '').trim();
	const hasChannel =
		linesToList(contact.phonesText).length > 0 ||
		linesToList(contact.emailsText).length > 0 ||
		linesToList(contact.messengersText).length > 0;
	return Boolean(name && position && hasChannel);
}

export { newContactDraft };
