/** HTTP API задач CRM (через apiFetch + X-API-Key). */
import { apiFetch, apiPatch, apiPost } from '$lib/api.js';

export async function fetchTasks(params = {}) {
	const q = new URLSearchParams();
	if (params.status) q.set('status', params.status);
	if (params.leadId != null) q.set('lead_id', String(params.leadId));
	if (params.lead) q.set('lead', params.lead);
	const suffix = q.toString() ? `?${q}` : '';
	const r = await apiFetch(`/api/tasks${suffix}`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function createTask(body) {
	const r = await apiPost('/api/tasks', body);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function patchTask(taskId, patch) {
	const r = await apiPatch(`/api/tasks/${taskId}`, patch);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}
