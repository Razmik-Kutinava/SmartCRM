/** API тендеров: сохранённые, анализ, external_id. */
import { apiFetch } from '$lib/api.js';

export function tenderExternalId(t) {
	if (!t) return '';
	const id = t.id ?? t.url ?? t.title ?? '';
	const src = t.source || 'unknown';
	if (String(id).includes(':')) return String(id);
	return `${src}:${id}`;
}

async function parseJson(r) {
	if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
	return r.json();
}

export async function fetchSavedTenders(status = 'saved') {
	const r = await apiFetch(`/api/tenders/saved?status=${status}`);
	return parseJson(r);
}

export async function saveTender(payload) {
	const r = await apiFetch('/api/tenders/saved', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(payload),
	});
	return parseJson(r);
}

export async function patchTenderSaved(id, patch) {
	const r = await apiFetch(`/api/tenders/saved/${id}`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(patch),
	});
	return parseJson(r);
}

export async function extractTenderDocument(file) {
	const fd = new FormData();
	fd.append('file', file);
	const r = await apiFetch('/api/tenders/documents/extract', {
		method: 'POST',
		body: fd,
	});
	return parseJson(r);
}

export async function analyzeTender(tender, agent, documentText = '') {
	const r = await apiFetch('/api/tenders/analyze', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ tender, agent, document_text: documentText }),
	});
	return parseJson(r);
}

export function sourceLabel(source) {
	const map = {
		gosplan: 'ЕИС / Gosplan',
		tenderguru: 'TenderGuru',
		serper: 'Serper',
		tavily: 'Tavily',
		zakupki: 'Закупки',
	};
	return map[source] || source || '—';
}
