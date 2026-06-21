/** UI-хелперы для компактного «Пути сделки». */

/** @param {{ groups?: Array<Record<string, unknown>>, nextStep?: Record<string, unknown> | null }} dealPath */
export function dealPathNextStep(dealPath) {
	if (dealPath?.nextStep) return dealPath.nextStep;
	const groups = dealPath?.groups || [];
	for (const group of groups) {
		for (const step of group.steps || []) {
			if (!step.done) {
				return { ...step, groupId: group.id, groupTitle: group.title };
			}
		}
	}
	return null;
}

/** @param {{ groups?: Array<Record<string, unknown>> }} dealPath */
export function dealPathTotals(dealPath) {
	const groups = dealPath?.groups || [];
	let done = 0;
	let total = 0;
	for (const g of groups) {
		done += g.progress?.done ?? 0;
		total += g.progress?.total ?? 0;
	}
	return { done, total };
}

/** @param {string} stage @param {{ relatedStages?: string[], progress?: { done: number, total: number } }} group */
export function isDealPathGroupActive(stage, group) {
	const stages = group.relatedStages || [];
	if (!stages.length) return true;
	if (stages.includes(stage)) return true;
	return (group.progress?.done ?? 0) < (group.progress?.total ?? 0);
}
