/** API и хелперы Ops — краулинг вендоров → RAG tech_specialist. */
import { getApiUrl } from '$lib/websocket.js';

const API = getApiUrl();

export function emptyVendor() {
	return {
		id: '',
		name: '',
		seed_url: 'https://',
		doc_urls: [],
		enabled: false,
		use_sitemap: false,
		max_pages: 30,
		max_depth: 2
	};
}

/** doc_urls в UI — многострочное поле ↔ массив */
export function docUrlsToText(urls) {
	return (urls || []).join('\n');
}

export function docUrlsFromText(text) {
	return (text || '')
		.split('\n')
		.map((s) => s.trim())
		.filter((s) => s.startsWith('http'));
}

export async function fetchVendorCrawlConfig() {
	const r = await fetch(`${API}/api/rag/vendor-crawl/config`);
	if (!r.ok) throw new Error('config load failed');
	const d = await r.json();
	return d.config;
}

export async function saveVendorCrawlConfig(config) {
	const r = await fetch(`${API}/api/rag/vendor-crawl/config`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(config)
	});
	if (!r.ok) {
		const err = await r.json().catch(() => ({}));
		throw new Error(err.detail || 'save failed');
	}
	return (await r.json()).config;
}

export async function fetchVendorCrawlStatus() {
	const r = await fetch(`${API}/api/rag/vendor-crawl/status`);
	if (!r.ok) throw new Error('status failed');
	return r.json();
}

export async function runVendorCrawl({ vendorId = null, dryRun = false } = {}) {
	const r = await fetch(`${API}/api/rag/vendor-crawl/run`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ vendor_id: vendorId, dry_run: dryRun })
	});
	const body = await r.json().catch(() => ({}));
	if (!r.ok) throw new Error(body.detail || 'run failed');
	return body;
}
