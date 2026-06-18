const API = '';

export function emptyWatch() {
	return {
		id: `watch_${Date.now()}`,
		name: 'Новое правило',
		keywords: '',
		okpd_codes: [],
		law: 'all',
		region: null,
		price_min: null,
		price_max: null,
		enabled: true
	};
}

export async function fetchTenderMonitorConfig() {
	const r = await fetch(`${API}/api/tenders/monitor/config`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function saveTenderMonitorConfig(cfg) {
	const r = await fetch(`${API}/api/tenders/monitor/config`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(cfg)
	});
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function fetchTenderMonitorStatus() {
	const r = await fetch(`${API}/api/tenders/monitor/status`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function runTenderMonitor({ watchId = null, dryRun = false } = {}) {
	const r = await fetch(`${API}/api/tenders/monitor/run`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ watch_id: watchId, dry_run: dryRun })
	});
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export function okpdToText(codes) {
	return (codes || []).join('\n');
}

export function okpdFromText(text) {
	return (text || '')
		.split(/[\n,;]+/)
		.map((s) => s.trim())
		.filter(Boolean);
}
