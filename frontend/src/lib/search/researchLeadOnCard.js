/** One-click «Исследовать» на карточке → research-lead → PATCH. */
import { apiPost } from '$lib/api.js';
import { apiUpdateLead } from '$lib/leadsStorage.js';
import {
	leadToEnrichPayload,
	researchResultToLeadPatch,
} from '$lib/search/researchLeadApply.js';

export const RESEARCH_STATUS_LABELS = {
	searching: 'Ищу в интернете (Serper / Brave / Tavily)…',
	synthesizing: 'Синтез выжимки (Groq → Ollama)…',
	saving: 'Сохраняю в карточку…',
	done_llm: 'Готово · выжимка от LLM',
	done_fallback: 'Готово без LLM · выжимка из поиска',
	error: 'Исследование не удалось',
};

export function researchStatusLabel(status) {
	return RESEARCH_STATUS_LABELS[String(status || '')] || 'Исследование…';
}

/** Запрос идёт одним POST, поэтому фазу «синтез» показываем по таймеру. */
const SYNTH_HINT_MS = 8000;

export async function researchLeadOnCard(lead, { force = true, onProgress = null } = {}) {
	const notify = (status) => {
		if (typeof onProgress === 'function') onProgress(status, researchStatusLabel(status));
	};
	if (!lead?.id) throw new Error('Нет лида');
	const payload = leadToEnrichPayload(lead);
	if (!payload?.company?.trim()) throw new Error('Укажите название компании');

	notify('searching');
	const synthTimer = setTimeout(() => notify('synthesizing'), SYNTH_HINT_MS);
	let data;
	try {
		const r = await apiPost('/api/search/research-lead', { lead: payload, force });
		data = await r.json();
		if (!r.ok || data.ok === false) {
			throw new Error(data.detail || data.error || `HTTP ${r.status}`);
		}
	} catch (e) {
		notify('error');
		throw e;
	} finally {
		clearTimeout(synthTimer);
	}

	const finalStatus = data?.web_research?.status || (data?.web_research?.llm ? 'done_llm' : 'done_fallback');
	const patch = researchResultToLeadPatch(data, lead);
	if (!Object.keys(patch).length) {
		notify(finalStatus);
		return { data, patch: {}, applied: false, status: finalStatus };
	}

	notify('saving');
	await apiUpdateLead(lead.id, patch);
	notify(finalStatus);
	return { data, patch, applied: true, status: finalStatus };
}
