/** Воронка Kanban: группировка и оптимистичный перенос стадии (DnD). */

export const FUNNEL_DRAG_MIME = 'application/x-smartcrm-lead-id';

const STAGE_BORDER = {
	Новый: 'border-gray-700',
	Квалифицирован: 'border-blue-800',
	'КП отправлено': 'border-yellow-800',
	Переговоры: 'border-indigo-800',
	Выигран: 'border-green-800',
	Проигран: 'border-red-900',
};

/** @param {Array<{ id: number, stage?: string }>} leads @param {string[]} stages */
export function groupLeadsByStage(leads, stages) {
	const m = Object.fromEntries(stages.map((s) => [s, []]));
	const fallback = stages[0] || 'Новый';
	for (const l of leads) {
		let s = l.stage;
		if (!m[s]) s = fallback;
		m[s].push(l);
	}
	return m;
}

/** @param {Array<{ id: number, stage?: string }>} leads */
export function moveLeadStage(leads, leadId, newStage) {
	const id = Number(leadId);
	return leads.map((l) => (l.id === id ? { ...l, stage: newStage } : l));
}

export function stageColor(stage) {
	return STAGE_BORDER[stage] || 'border-gray-700';
}

/** @param {DataTransfer | null | undefined} dt */
export function parseLeadDragId(dt) {
	if (!dt) return null;
	const raw = dt.getData(FUNNEL_DRAG_MIME) || dt.getData('text/plain');
	const id = parseInt(String(raw), 10);
	return Number.isFinite(id) ? id : null;
}

/** @param {DragEvent} e @param {number} leadId */
export function setLeadDragData(e, leadId) {
	if (!e.dataTransfer) return;
	e.dataTransfer.setData(FUNNEL_DRAG_MIME, String(leadId));
	e.dataTransfer.setData('text/plain', String(leadId));
	e.dataTransfer.effectAllowed = 'move';
}
