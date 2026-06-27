/** Сводка этапа и сроков в строке списка (зеркало listStageSummary). */

/** @param {Record<string, unknown> | null | undefined} lead */
export function listStageSummary(lead) {
	return lead?.listStageSummary && typeof lead.listStageSummary === 'object'
		? lead.listStageSummary
		: null;
}

/** @param {Record<string, unknown> | null | undefined} summary */
export function dealPathProgressLabel(summary) {
	if (!summary) return '';
	const done = Number(summary.dealPathDone) || 0;
	const total = Number(summary.dealPathTotal) || 0;
	if (total <= 0) return '';
	return `${done}/${total} шагов`;
}

/** @param {Record<string, unknown> | null | undefined} summary */
export function stageDaysLabel(summary) {
	if (!summary) return '';
	const days = Number(summary.daysOnStage) || 0;
	const limit = summary.stageDayLimit;
	if (limit == null || limit === '') return `На этапе ${days} дн.`;
	return `На этапе ${days}/${limit} дн.`;
}

/** @param {string} status */
export function stageTimingClass(status) {
	if (status === 'overdue') return 'text-rose-400';
	if (status === 'soon') return 'text-amber-300';
	return 'text-gray-500';
}

/** @param {string} urgency */
export function taskUrgencyClass(urgency) {
	if (urgency === 'Просрочено') return 'text-rose-400 font-medium';
	if (urgency === 'Сегодня') return 'text-amber-300 font-medium';
	if (urgency === 'Завтра') return 'text-sky-300';
	return 'text-gray-400';
}

/** @param {Record<string, unknown> | null | undefined} summary */
export function taskDueLine(summary) {
	if (!summary) return '';
	const urgency = String(summary.taskUrgency || '').trim();
	const due = String(summary.nextTaskDue || '').trim();
	if (!urgency && !due) return '';
	if (urgency && due) return `${urgency} · ${due}`;
	return urgency || due;
}

/** @param {Record<string, unknown> | null | undefined} summary */
export function dealPathPercent(summary) {
	if (!summary) return 0;
	const total = Number(summary.dealPathTotal) || 0;
	if (total <= 0) return 0;
	return Math.round((100 * (Number(summary.dealPathDone) || 0)) / total);
}
