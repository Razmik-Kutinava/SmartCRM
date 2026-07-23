/** Сводка «что сделать» на хабе карточки лида. */
import { dealPathNextStep, dealPathTotals } from '$lib/leads/leadDealPathUi.js';
import { passportHasData } from '$lib/leads/leadPassport.js';
import { slaStatus, taskDueBadge } from '$lib/tasks/taskSla.js';

const SEV_ORDER = { critical: 0, warn: 1, info: 2 };

/** @param {string} code */
export function coachPanelForCode(code) {
	const c = String(code || '');
	if (c.startsWith('task_') || c === 'no_tasks') return 'work';
	if (c === 'needs_enrich' || c === 'passport_empty' || c.startsWith('score_')) return 'client';
	if (
		[
			'qual_fields',
			'lpr_missing',
			'kp_not_marked',
			'deal_path',
			'deal_progress',
			'stage_stale',
			'stage_stale_soon',
			'wait_stale',
			'repeat_wait_task',
			'kp_daily_touch',
		].some((p) => c.includes(p))
	) {
		return 'header';
	}
	if (c.startsWith('approval_') || c.startsWith('won_doc_')) return 'header';
	return 'header';
}

/**
 * @param {Record<string, unknown> | null} lead
 * @param {Array<Record<string, unknown>>} tasks
 */
export function buildLeadCardCoachItems(lead, tasks = []) {
	if (!lead) return [];
	/** @type {Array<{ severity: string, code: string, text: string, panel: string }>} */
	const items = [];
	const seen = new Set();

	function push(severity, code, text, panel) {
		const key = `${code}:${text}`;
		if (!text?.trim() || seen.has(key)) return;
		seen.add(key);
		items.push({ severity, code, text: text.trim(), panel: panel || coachPanelForCode(code) });
	}

	const mgr = Number(lead.score);
	const sug = lead.scoreAdvisory?.suggestedScore;
	const sugNum = sug != null ? Number(sug) : NaN;
	if (Number.isFinite(sugNum) && Number.isFinite(mgr) && sugNum > mgr + 5) {
		push(
			'warn',
			'score_gap',
			`Подсказка системы: ${sugNum}/100 — у вас ${mgr}. Заполните карточку, документы и закройте дела.`,
			'client',
		);
	}

	for (const h of lead.stageHints || []) {
		if (!h?.message) continue;
		push(h.severity || 'warn', h.code || 'hint', h.message, coachPanelForCode(h.code));
	}

	const openTasks = (tasks || []).filter((t) => t.status !== 'done');
	for (const t of openTasks) {
		const badge = taskDueBadge(t);
		const sla = slaStatus(t);
		if (badge.label === 'Просрочено' || sla.label === 'Просрочено') {
			const due = t.due && t.due !== '—' ? ` · ${t.due}` : '';
			push('critical', `task_${t.id}`, `Просрочено: ${t.title}${due}`, 'work');
		}
	}
	for (const t of openTasks) {
		const badge = taskDueBadge(t);
		if (badge.label === 'Сегодня') {
			push('warn', `task_today_${t.id}`, `Сегодня: ${t.title}`, 'work');
		}
	}

	if (lead.needsEnrich) {
		push(
			'warn',
			'needs_enrich',
			'Дозаполни карточку: паспорт, контакты, сумма сделки — для полного скоринга.',
			'client',
		);
	}

	if (!passportHasData(lead)) {
		push('info', 'passport_empty', 'Паспорт пуст — укажи ИНН и нажми «Обогатить».', 'client');
	}

	const next = dealPathNextStep(lead.dealPath);
	if (next?.label && !seen.has(`deal_path:${next.label}`)) {
		push('warn', 'deal_path', `Путь сделки: ${next.label}`, 'header');
	}

	const { done, total } = dealPathTotals(lead.dealPath);
	if (total > 0 && done < total) {
		push('info', 'deal_progress', `Документы и квалификация: ${done}/${total} шагов закрыто.`, 'header');
	}

	if (lead.waitStale) {
		push('warn', 'wait_stale', 'Долго ждём ответ клиента — обнови дело или этап.', 'header');
	}

	for (const w of lead.scoreAdvisory?.warnings || []) {
		if (w) push('warn', `score_${String(w).slice(0, 24)}`, String(w), 'client');
	}

	if (openTasks.length === 0 && lead.stage !== 'Проигран') {
		push('info', 'no_tasks', 'Нет открытых дел — создай задачу с типом и сроком.', 'work');
	}

	return items
		.sort((a, b) => (SEV_ORDER[a.severity] ?? 9) - (SEV_ORDER[b.severity] ?? 9))
		.slice(0, 8);
}

/** @param {Array<{ panel?: string }>} items */
export function hubTileAlertsFromCoach(items) {
	/** @type {Record<string, boolean>} */
	const alerts = {};
	for (const item of items || []) {
		const p = item.panel;
		if (!p || p === 'header' || p === 'dealPath' || p === 'stages') continue;
		alerts[p] = true;
	}
	return alerts;
}
