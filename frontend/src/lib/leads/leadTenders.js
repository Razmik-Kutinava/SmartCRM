/**
 * Тендеры на карточке лида: кэш + живой поиск.
 */
import { apiGet, apiPost } from '../api.js';

/** @param {Record<string, any>|null|undefined} lead */
export function leadTendersFromLead(lead) {
	const snap = lead?.checko?.analyses?.lead_tenders;
	return snap && typeof snap === 'object' ? snap : null;
}

/**
 * @param {Record<string, any>|null|undefined} lead
 * @returns {{ preview: string, meta: string }}
 */
export function leadTendersHubPreview(lead) {
	const snap = leadTendersFromLead(lead) || {};
	const n =
		(Array.isArray(snap.current) ? snap.current.length : 0) +
		(Array.isArray(snap.past) ? snap.past.length : 0) +
		(Array.isArray(snap.web) ? snap.web.length : 0);
	const inn = String(lead?.inn || '').trim();
	if (n) {
		const llm = snap.usage?.llm_tokens ?? 0;
		return {
			preview: `${n} закупок в снимке`,
			meta: `LLM-токенов ${llm} · поиск запросами`,
		};
	}
	return {
		preview: 'Прошлые и текущие закупки',
		meta: inn ? `ИНН ${inn}` : 'нужен ИНН или имя',
	};
}

/**
 * @param {Array<Record<string, any>>|null|undefined} providers
 */
export function formatTendersUsage(providers, llmTokens = 0) {
	const rows = Array.isArray(providers) ? providers : [];
	const active = rows.filter((p) => Number(p.requests) > 0);
	const skipped = rows.filter((p) => p.billed === 'skipped' || Number(p.requests) === 0);
	const spent = active.map((p) => `${p.provider}: ${p.requests} (${p.billed}${p.tokens != null ? `, токены ${p.tokens}` : ''})`);
	const head = `LLM-токенов поисковика: ${llmTokens || 0} (поиск не через Groq)`;
	if (!spent.length && !skipped.length) return head;
	const tail = spent.length ? spent.join('; ') : 'внешние ключи не заданы — запросов 0';
	return `${head}. ${tail}`;
}

/** @param {number|string} leadId */
export async function fetchLeadTenders(leadId) {
	const res = await apiGet(`/api/leads/${leadId}/tenders`);
	const body = await res.json().catch(() => ({}));
	if (!res.ok) {
		throw new Error(typeof body?.detail === 'string' ? body.detail : 'Не удалось загрузить тендеры');
	}
	return body;
}

/** @param {number|string} leadId */
export async function searchLeadTenders(leadId) {
	const res = await apiPost(`/api/leads/${leadId}/tenders/search`, {});
	const body = await res.json().catch(() => ({}));
	if (!res.ok) {
		throw new Error(typeof body?.detail === 'string' ? body.detail : 'Ошибка поиска тендеров');
	}
	return body;
}
