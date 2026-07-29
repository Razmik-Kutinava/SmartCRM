/** Apply research-lead → PATCH: поля + checkoJson.analyses.web_research. */
import {
	enrichResultToLeadPatch,
	leadToEnrichPayload,
} from '$lib/search/enrichLeadApply.js';

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
	analyses.web_research = webResearch;
	return { ...base, analyses };
}

/**
 * @param {Record<string, unknown>} result
 * @param {Record<string, unknown> | null} lead
 */
export function researchResultToLeadPatch(result, lead = null) {
	const patch = enrichResultToLeadPatch(result, lead);
	const web = result?.web_research;
	if (!web) return patch;

	const existing =
		lead?.checko && typeof lead.checko === 'object'
			? lead.checko
			: patch.checkoJson && typeof patch.checkoJson === 'object'
				? patch.checkoJson
				: {};
	patch.checkoJson = mergeWebResearchIntoChecko(existing, web);

	const summary = String(web.summary || result.answer || '').trim();
	if (summary) {
		const marker = '--- Исследование (веб) ---';
		const prev = String(lead?.description || patch.description || '').trim();
		const short = summary.length > 900 ? `${summary.slice(0, 900)}…` : summary;
		const block = `${marker}\n${short}`;
		if (!prev.includes(marker)) {
			patch.description = prev ? `${prev}\n\n${block}` : block;
		}
	}
	return patch;
}

export { leadToEnrichPayload };
