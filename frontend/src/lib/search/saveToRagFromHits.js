/** Нормализация результатов поиска → документы для POST /api/rag/ingest-batch */
import { apiPost } from '$lib/api.js';

/**
 * @param {Record<string, unknown>} hit
 * @param {string} [label]
 */
export function webHitToDoc(hit, label = '') {
	const title = String(hit.title || label || 'Результат поиска');
	const text = [title, hit.snippet, hit.url ? `Источник: ${hit.url}` : '']
		.filter(Boolean)
		.join('\n\n');
	return {
		text: String(text),
		metadata: {
			source: String(hit.url || hit.source || ''),
			title,
		},
	};
}

/** @param {Array<Record<string, unknown>>} hits */
export function webHitsToDocs(hits) {
	return (hits || []).map((h, i) => webHitToDoc(h, `Результат ${i + 1}`));
}

/** @param {Record<string, unknown>} company */
export function prospectCompanyToDoc(company) {
	const title = String(company.name || 'Компания');
	const parts = [title];
	if (company.fit_reason) parts.push(`Fit: ${company.fit_reason}`);
	if (company.snippet) parts.push(String(company.snippet));
	if (company.fit_score != null) parts.push(`Скор: ${company.fit_score}%`);
	if (company.url) parts.push(`Источник: ${company.url}`);
	return {
		text: parts.join('\n\n'),
		metadata: { source: String(company.url || ''), title },
	};
}

/** @param {Array<Record<string, unknown>>} companies */
export function prospectCompaniesToDocs(companies) {
	return (companies || []).map((c) => prospectCompanyToDoc(c));
}

/**
 * @param {Record<string, string>} enriched
 * @param {string} [company]
 */
export function enrichDataToDocs(enriched, company = '') {
	const keys = Object.keys(enriched || {});
	if (!keys.length) return [];
	const lines = keys.map((k) => `${k}: ${enriched[k]}`);
	const title = company ? `Обогащение: ${company}` : 'Обогащение лида';
	return [
		{
			text: [title, ...lines].join('\n\n'),
			metadata: { title, source_type: 'enrich' },
		},
	];
}

/**
 * @param {Record<string, unknown>} result
 * @param {string} query
 */
export function freeSearchToDocs(result, query) {
	const docs = webHitsToDocs(/** @type {Array<Record<string, unknown>>} */ (result?.raw_results));
	if (result?.answer) {
		docs.unshift({
			text: [`Вопрос: ${query}`, `AI-ответ:`, String(result.answer)].join('\n\n'),
			metadata: { title: `free-${query.slice(0, 48)}`, source_type: 'free_answer' },
		});
	}
	return docs;
}

/**
 * @param {Record<string, unknown>} result
 * @param {string} company
 */
export function enrichResultToDocs(result, company) {
	return [
		...enrichDataToDocs(
			/** @type {Record<string, string>} */ (result?.enriched || {}),
			company,
		),
		...webHitsToDocs(/** @type {Array<Record<string, unknown>>} */ (result?.raw_results)),
	];
}

/**
 * @param {string} answer
 * @param {string} task
 * @param {string} agentId
 * @param {Array<Record<string, unknown>>} rawResults
 */
export function agentTaskToDocs(answer, task, agentId, rawResults = []) {
	const docs = [];
	if (answer?.trim()) {
		docs.push({
			text: [`Задача: ${task}`, `Ответ агента (${agentId}):`, answer].join('\n\n'),
			metadata: { title: `agent-task-${agentId}`, source_type: 'agent_task' },
		});
	}
	return [...docs, ...webHitsToDocs(rawResults)];
}

/** @param {string} agentId */
export function normalizeAgentForRag(agentId) {
	if (!agentId || agentId === 'default') return 'all';
	return agentId;
}

/**
 * @param {object} opts
 * @param {Array<{ text: string, metadata?: Record<string, unknown> }>} opts.documents
 * @param {string} opts.forAgent
 * @param {string} opts.tags
 * @param {boolean} opts.dryRun
 */
export async function ingestSearchDocuments({ documents, forAgent, tags, dryRun }) {
	const resp = await apiPost('/api/rag/ingest-batch', {
		documents,
		for_agent: forAgent,
		tags,
		dry_run: dryRun,
	});
	const data = await resp.json();
	if (!resp.ok || !data.ok) {
		throw new Error(data.detail || `HTTP ${resp.status}`);
	}
	return data;
}
