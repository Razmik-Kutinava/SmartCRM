/**
 * Воронка и пороги приоритета: дефолт + подгрузка с GET /api/crm/config.
 */
import { browser } from '$app/environment';

export const DEFAULT_CRM_STAGES = [
	'Новый',
	'Квалифицирован',
	'КП отправлено',
	'Переговоры',
	'Выигран',
	'Проигран',
];

/** @type {string[]} — мутируется после loadCrmConfig(); для SSR остаётся дефолт */
export let CRM_STAGES = [...DEFAULT_CRM_STAGES];

/** @type {CrmUiConfig | null} */
let _configCache = null;

/**
 * @typedef {{
 *   stages: string[],
 *   priority_thresholds: { critical?: number, high?: number, medium?: number },
 *   score_range: { min?: number, max?: number },
 *   default_new_lead_score?: number
 * }} CrmUiConfig
 */

function apiBase() {
	if (!browser) return 'http://127.0.0.1:8000';
	const pub = import.meta.env.PUBLIC_API_URL;
	if (pub) return String(pub).replace(/\/$/, '');
	return '';
}

/**
 * Подтягивает этапы и пороги с бэкенда (как в Ops → CRM / CRM Points).
 * Безопасно вызывать из onMount; при ошибке оставляет дефолт.
 */
export async function loadCrmConfig() {
	const url = `${apiBase()}/api/crm/config`;
	try {
		const r = await fetch(url);
		if (!r.ok) throw new Error(String(r.status));
		/** @type {CrmUiConfig} */
		const data = await r.json();
		_configCache = data;
		if (Array.isArray(data.stages) && data.stages.length) {
			CRM_STAGES.length = 0;
			CRM_STAGES.push(...data.stages.map((s) => String(s).trim()).filter(Boolean));
		}
		return data;
	} catch {
		return null;
	}
}

export function getCachedCrmConfig() {
	return _configCache;
}

/**
 * Приоритет лида по порогам из настроек и шкале score (аналог CRM Points).
 * Если пороги «не влезают» в max (например legacy 130), сжимаем к шкале.
 */
export function leadPriorityTier(score, config = null) {
	const s = Number(score);
	const sc = Number.isFinite(s) ? s : 0;
	const cfg = config || _configCache || {};
	const range = cfg.score_range || { min: 0, max: 100 };
	const min = Number(range.min) || 0;
	const max = Number(range.max) || 100;
	const span = Math.max(1, max - min);
	const t = cfg.priority_thresholds || {};
	let crit = Number(t.critical);
	let high = Number(t.high);
	let med = Number(t.medium);
	if (!Number.isFinite(crit)) crit = min + span * 0.85;
	if (!Number.isFinite(high)) high = min + span * 0.65;
	if (!Number.isFinite(med)) med = min + span * 0.35;
	const norm = (x) => {
		if (x <= max) return x;
		return min + ((x - min) / (200 - min)) * span;
	};
	const nc = norm(crit);
	const nh = norm(high);
	const nm = norm(med);
	if (sc >= nc) return { key: 'critical', label: 'Критический' };
	if (sc >= nh) return { key: 'high', label: 'Высокий' };
	if (sc >= nm) return { key: 'medium', label: 'Средний' };
	return { key: 'low', label: 'Низкий' };
}

export function priorityTierBadgeClass(tier) {
	const m = {
		critical: 'bg-rose-950 text-rose-200 border border-rose-800',
		high: 'bg-amber-950 text-amber-200 border border-amber-800',
		medium: 'bg-slate-800 text-slate-200 border border-slate-600',
		low: 'bg-gray-800 text-gray-400 border border-gray-700',
	};
	return m[tier?.key] || m.low;
}
