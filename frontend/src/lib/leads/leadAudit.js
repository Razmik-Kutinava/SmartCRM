/** Аудит изменений полей лида (apiFetch + X-API-Key). */
import { apiFetch } from '$lib/api.js';

/** @type {Record<string, string>} */
export const AUDIT_FIELD_LABELS = {
	company: 'Компания',
	contact: 'Контакт',
	position: 'Должность',
	email: 'Email',
	phone: 'Телефон',
	stage: 'Стадия',
	score: 'Балл',
	source: 'Источник',
	budget: 'Бюджет',
	website: 'Сайт',
	employees: 'Сотрудники',
	industry: 'Отрасль',
	city: 'Город',
	responsible: 'Ответственный',
	next_call: 'След. звонок',
	description: 'Описание',
	amount_rub: 'Сумма ₽',
	paid_amount_rub: 'Оплачено ₽',
	approvals: 'Апрувы',
	communication: 'Касание',
};

/** @param {string} field */
export function auditFieldLabel(field) {
	return AUDIT_FIELD_LABELS[field] || field;
}

export async function fetchLeadAudit(leadId, limit = 35) {
	const n = Number(leadId);
	if (!leadId || Number.isNaN(n)) return [];
	const r = await apiFetch(`/api/leads/${n}/audit?limit=${limit}`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}
