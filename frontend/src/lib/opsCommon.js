/** Общие хелперы для экранов Ops (русский UI). */

export function fmtTime(ts) {
	return new Date(ts * 1000).toLocaleTimeString('ru-RU', {
		hour: '2-digit',
		minute: '2-digit',
		second: '2-digit'
	});
}

export function intentColor(intent) {
	const map = {
		create_lead: 'bg-emerald-900 text-emerald-300',
		update_lead: 'bg-blue-900 text-blue-300',
		delete_lead: 'bg-red-900 text-red-300',
		list_leads: 'bg-indigo-900 text-indigo-300',
		create_task: 'bg-amber-900 text-amber-300',
		list_tasks: 'bg-yellow-900 text-yellow-300',
		write_email: 'bg-pink-900 text-pink-300',
		search_web: 'bg-cyan-900 text-cyan-300',
		noop: 'bg-gray-800 text-gray-400'
	};
	return map[intent] || 'bg-gray-800 text-gray-400';
}

export function modelLabel(model) {
	if (!model) return '—';
	if (model.includes('llama') || model.includes('groq') || model.includes('instant')) return 'Groq';
	if (model.includes('hermes')) return 'Hermes3';
	if (model.includes('qwen')) return 'Qwen';
	return model;
}

export function severityBadge(sev) {
	const map = {
		critical: 'bg-red-950 text-red-300 border border-red-800',
		medium: 'bg-amber-950 text-amber-200 border border-amber-800',
		low: 'bg-slate-800 text-slate-300 border border-slate-600'
	};
	return map[sev] || map.low;
}

export function severityLabel(sev) {
	const map = { critical: 'Критично', medium: 'Средне', low: 'Низкий приоритет' };
	return map[sev] || sev;
}
