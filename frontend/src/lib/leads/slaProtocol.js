/** SLA-протоколы лида. */
import { apiFetch } from '$lib/api.js';

export async function fetchSlaProtocols() {
	const r = await apiFetch('/api/leads/sla-protocols');
	if (!r.ok) throw new Error(`SLA protocols: HTTP ${r.status}`);
	return r.json();
}

export async function assignLeadSlaProtocol(leadId, protocolId, restart = false) {
	const r = await apiFetch(`/api/leads/${leadId}/sla-protocol`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ protocol_id: protocolId || null, restart }),
	});
	const body = await r.json().catch(() => ({}));
	if (!r.ok) throw new Error(body?.detail || `HTTP ${r.status}`);
	return body;
}
