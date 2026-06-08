/** Правила переходов стадий CRM — подсказки UI и разбор ошибок PATCH. */
import { auditFieldLabel } from '$lib/leads/leadAudit.js';

/** @param {unknown} parsed */
export function parseStageTransitionBlocked(parsed) {
	const d = parsed?.detail;
	if (
		d &&
		typeof d === 'object' &&
		d.code === 'stage_transition_blocked' &&
		Array.isArray(d.messages)
	) {
		return d.messages;
	}
	return null;
}

/** @param {string[]} messages */
export function formatStageTransitionBlocked(messages) {
	return messages.join('\n');
}

/** @param {number} status @param {string} text @param {unknown} parsed */
export function formatLeadPatchError(status, text, parsed) {
	const blocked = parseStageTransitionBlocked(parsed);
	if (blocked) return formatStageTransitionBlocked(blocked);
	const d = parsed?.detail;
	if (typeof d === 'string') return d;
	if (Array.isArray(d)) return d.map((x) => x.msg || x).join('; ');
	if (d && typeof d === 'object') return JSON.stringify(d);
	return text || `HTTP ${status}`;
}

/** @param {Record<string, unknown> | null | undefined} rule */
export function describeTransitionRule(rule) {
	if (!rule || typeof rule !== 'object') return '';
	const parts = [];
	for (const f of rule.require_non_empty || []) {
		parts.push(auditFieldLabel(String(f)));
	}
	if (rule.require_positive_amount_rub) parts.push('сумма ₽ > 0');
	return parts.length ? parts.join(', ') : '';
}

/** @param {unknown} rules @param {string} stage */
export function rulesForTargetStage(rules, stage) {
	if (!Array.isArray(rules)) return [];
	return rules.filter((r) => r && typeof r === 'object' && r.to_stage === stage);
}
