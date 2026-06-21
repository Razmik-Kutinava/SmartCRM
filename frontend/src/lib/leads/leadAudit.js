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
	industry_verified: 'Отрасль проверена',
	products_owned: 'Уже купили',
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

/** @param {string} field @param {string} value */
export function formatAuditValue(field, value) {
	const v = String(value ?? '').trim();
	if (!v) return '—';
	if (field === 'approvals') {
		try {
			const o = JSON.parse(v);
			if (!o || typeof o !== 'object') return v;
			const on = Object.entries(o).filter(([, flag]) => Boolean(flag));
			return on.length ? `отмечено: ${on.length}` : 'без отметок';
		} catch {
			return 'изменено';
		}
	}
	if (v.length > 120) return `${v.slice(0, 117)}…`;
	return v;
}

/** Скрыть строки аудита, дублирующие ленту действий. */
export function isAuditRowHidden(row) {
	const et = row?.eventType;
	if (et === 'communication') return true;
	return false;
}

export async function fetchLeadAudit(leadId, limit = 35) {
	const n = Number(leadId);
	if (!leadId || Number.isNaN(n)) return [];
	const r = await apiFetch(`/api/leads/${n}/audit?limit=${limit}`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}
