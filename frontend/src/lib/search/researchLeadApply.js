/** Apply research-lead → PATCH: поля + checkoJson.analyses.web_research. */
import {
	enrichResultToLeadPatch,
	leadToEnrichPayload,
} from '$lib/search/enrichLeadApply.js';
import { mergeCheckoJson } from '$lib/search/mergeLeadJson.js';

/** Что агентам нужно из исследования — пишем в web_research, чтобы не терялось. */
export const AGENT_RESEARCH_REQUIREMENTS = {
	analyst: ['отрасль', 'продукты/услуги', 'контакты/ЛПР', 'сигналы покупки'],
	economist: ['численность', 'фин.сигналы/выручка', 'сегмент', 'география'],
	marketer: ['отрасль и боли', 'контакты', 'язык/позиционирование'],
	tech_specialist: ['технологии/ИТ (BuiltWith)', 'сайт/домен', 'DNS/MX', 'масштаб'],
	strategist: ['сводка профиля', 'пробелы (раздел риски)'],
};

/**
 * @param {unknown} existingChecko
 * @param {Record<string, unknown> | null | undefined} webResearch
 */
export function mergeWebResearchIntoChecko(existingChecko, webResearch) {
	if (!webResearch || typeof webResearch !== 'object') {
		return existingChecko && typeof existingChecko === 'object' ? { ...existingChecko } : {};
	}
	let base = {};
	if (existingChecko && typeof existingChecko === 'object' && !Array.isArray(existingChecko)) {
		base = { ...existingChecko };
	}
	const analyses =
		base.analyses && typeof base.analyses === 'object' && !Array.isArray(base.analyses)
			? { ...base.analyses }
			: {};
	const enriched = {
		...webResearch,
		agent_requirements: webResearch.agent_requirements || AGENT_RESEARCH_REQUIREMENTS,
	};
	analyses.web_research = enriched;
	return { ...base, analyses };
}

/**
 * Сводка для карточки: никогда не пустая и без «Ошибка синтеза…».
 * Если бэкенд не дал текст — собираем читаемый список источников на фронте.
 * @param {Record<string, any> | null | undefined} web
 * @param {Record<string, any> | null | undefined} result
 */
export function ensureSummary(web, result = null) {
	const summary = String(web?.summary || result?.answer || '').trim();
	const bad =
		!summary ||
		/^ошибка синтеза/i.test(summary) ||
		/^ошибка исследования/i.test(summary) ||
		/connection attempts failed/i.test(summary);
	if (!bad) return summary;

	const hits = Array.isArray(web?.raw_results) ? web.raw_results : [];
	if (!hits.length) return '';
	const lines = hits.slice(0, 12).map((h, i) => {
		const title = String(h?.title || h?.url || '—').trim();
		const url = String(h?.url || h?.link || '').trim();
		const snip = String(h?.snippet || h?.description || '')
			.replace(/\s+/g, ' ')
			.trim()
			.slice(0, 240);
		return `[${i + 1}] ${title}${url ? ` — ${url}` : ''}${snip ? `\n    ${snip}` : ''}`;
	});
	return ['Выжимка без LLM — факты из веб-поиска:', ...lines].join('\n');
}

/**
 * @param {Record<string, unknown>} result
 * @param {Record<string, unknown> | null} lead
 */
export function researchResultToLeadPatch(result, lead = null) {
	const patch = enrichResultToLeadPatch(result, lead);
	const web = result?.web_research;
	const resolvedInn = result?.resolved_inn?.inn || result?.passport?.inn || result?.enriched?.inn;
	if (resolvedInn && (!lead?.inn || lead.inn === '—')) {
		patch.inn = String(resolvedInn).replace(/\D/g, '') || resolvedInn;
	}
	if (!web) return patch;

	// lead.checko + passport.checko из patch — не терять company/financials
	const existing = mergeCheckoJson(
		lead?.checko && typeof lead.checko === 'object' ? lead.checko : {},
		patch.checkoJson && typeof patch.checkoJson === 'object' ? patch.checkoJson : {},
	);
	patch.checkoJson = mergeWebResearchIntoChecko(existing, web);

	const summary = ensureSummary(web, result);
	if (summary) {
		const marker = '--- Исследование (веб) ---';
		const prev = String(lead?.description || patch.description || '').trim();
		const short = summary.length > 3500 ? `${summary.slice(0, 3500)}…` : summary;
		const block = `${marker}\n${short}`;
		const cleaned = prev
			.replace(/\n*--- Исследование \(веб\) ---[\s\S]*$/m, '')
			.replace(/\n*Ошибка синтеза выжимки:[\s\S]*$/im, '')
			.trim();
		patch.description = cleaned ? `${cleaned}\n\n${block}` : block;
	}
	return patch;
}

export { leadToEnrichPayload };
