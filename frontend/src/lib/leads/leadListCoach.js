/** Суфлёр «что сделать» в строке списка лидов (зеркало backend/core/lead_list_coach.py). */

export const COACH_SEVERITY_CLASS = {
	critical: 'text-rose-300 bg-rose-950/50 border-rose-900/60',
	warn: 'text-amber-200 bg-amber-950/40 border-amber-900/50',
	info: 'text-sky-200/90 bg-sky-950/30 border-sky-900/40',
};

/** @param {Array<{ severity?: string, code?: string, text?: string }>} coach */
export function coachItemsForLead(lead) {
	const rows = lead?.listCoach;
	return Array.isArray(rows) ? rows.filter((r) => r?.text) : [];
}

/** @param {string} severity */
export function coachSeverityClass(severity) {
	return COACH_SEVERITY_CLASS[severity] || COACH_SEVERITY_CLASS.info;
}
