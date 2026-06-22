/** Фильтрация и сортировка списка лидов (/leads/list). */
import { leadPriorityTier } from '$lib/crmStages.js';

export const SORT_OPTIONS = [
	{ id: 'score_desc', label: 'Балл ↓' },
	{ id: 'score_asc', label: 'Балл ↑' },
	{ id: 'priority_desc', label: 'Приоритет ↓' },
	{ id: 'warnings_desc', label: 'Предупреждения ↓' },
	{ id: 'score_delta_desc', label: 'Расхождение ↓' },
	{ id: 'company_asc', label: 'Компания А–Я' },
];

const STAGE_ALIASES = {
	переговоры: 'Переговоры',
	новый: 'Новый',
	квалифицирован: 'Квалифицирован',
	выигран: 'Выигран',
	проигран: 'Проигран',
};

function normalizeStage(raw) {
	const low = String(raw || '').trim().toLowerCase();
	return STAGE_ALIASES[low] || String(raw || '').trim();
}

/** Маппинг слотов Hermes list_leads → состояние UI списка. */
export function leadListViewFromVoiceSlots(slots = {}) {
	const f = String(slots.filter || 'all').toLowerCase();
	const q = String(slots.query || '').trim();
	const out = {
		filterStage: 'all',
		filterPriority: 'all',
		sortBy: 'score_desc',
		search: q,
		filterIndustry: '',
		filterCity: '',
	};
	if (f === 'hot' || f === 'горячих') {
		out.filterPriority = 'high';
		out.sortBy = 'priority_desc';
	} else if (f === 'cold' || f === 'холодных') {
		out.filterPriority = 'low';
		out.sortBy = 'score_asc';
	} else if (f === 'new' || f === 'новых') {
		out.filterStage = 'Новый';
	} else if (f === 'won' || f === 'выигранных') {
		out.filterStage = 'Выигран';
	}
	if (slots.stage) out.filterStage = normalizeStage(slots.stage);
	if (slots.industry) out.filterIndustry = String(slots.industry).trim();
	if (slots.city) out.filterCity = String(slots.city).trim();
	return out;
}

/** Применить view из voice_action.payload.filter */
export function applyVoiceListFilter(view = {}) {
	return {
		filterStage: view.filterStage ?? 'all',
		filterPriority: view.filterPriority ?? 'all',
		sortBy: view.sortBy ?? 'score_desc',
		search: view.search ?? '',
		filterIndustry: view.industry ?? view.filterIndustry ?? '',
		filterCity: view.city ?? view.filterCity ?? '',
		minScore: view.minScore != null && view.minScore !== '' ? Number(view.minScore) : null,
	};
}

export const PRIORITY_FILTERS = [
	{ id: 'all', label: 'Все приоритеты' },
	{ id: 'critical', label: 'Критический' },
	{ id: 'high', label: 'Высокий' },
	{ id: 'medium', label: 'Средний' },
	{ id: 'low', label: 'Низкий' },
];

export const SCORE_RISK_FILTERS = [
	{ id: 'all', label: 'Все по баллам' },
	{ id: 'warnings', label: 'С предупреждениями' },
	{ id: 'divergent', label: 'Расхождение с подсказкой' },
];

export const EMPLOYEES_BAND_FILTERS = [
	{ id: 'all', label: 'Любой размер' },
	{ id: '1-50', label: '1–50 сотр.' },
	{ id: '51-250', label: '51–250' },
	{ id: '251-1000', label: '251–1000' },
	{ id: '1000+', label: '1000+' },
];

export const GROUP_BY_OPTIONS = [
	{ id: 'none', label: 'Без группировки' },
	{ id: 'okved_section', label: 'ОКВЭД секция' },
	{ id: 'employees_band', label: 'Размер компании' },
	{ id: 'stage', label: 'Этап' },
];

const EMPTY_GROUP_KEY = '__empty__';

function groupKeyForLead(lead, groupBy) {
	switch (groupBy) {
		case 'okved_section':
			return String(lead.okvedSection || '').trim() || EMPTY_GROUP_KEY;
		case 'employees_band':
			return String(lead.employeesBand || '').trim() || EMPTY_GROUP_KEY;
		case 'stage':
			return String(lead.stage || '').trim() || EMPTY_GROUP_KEY;
		default:
			return '';
	}
}

/** Подпись заголовка группы для UI. */
export function groupLabelForKey(key, groupBy) {
	if (!key || key === EMPTY_GROUP_KEY) {
		if (groupBy === 'okved_section') return 'Без ОКВЭД';
		if (groupBy === 'employees_band') return 'Размер не указан';
		if (groupBy === 'stage') return 'Без этапа';
		return '—';
	}
	if (groupBy === 'okved_section') return `Секция ${key}`;
	if (groupBy === 'employees_band') return `${key} сотр.`;
	return key;
}

/**
 * Разбить отфильтрованный список на сворачиваемые группы.
 * @returns {Array<{ key: string, label: string, leads: Array<Record<string, unknown>>, count: number }>}
 */
export function groupLeads(leads, groupBy = 'none') {
	if (!groupBy || groupBy === 'none') {
		return [{ key: '', label: '', leads, count: leads.length }];
	}
	const buckets = new Map();
	for (const l of leads) {
		const k = groupKeyForLead(l, groupBy);
		if (!buckets.has(k)) buckets.set(k, []);
		buckets.get(k).push(l);
	}
	const keys = [...buckets.keys()].sort((a, b) => {
		if (a === EMPTY_GROUP_KEY) return 1;
		if (b === EMPTY_GROUP_KEY) return -1;
		return a.localeCompare(b, 'ru');
	});
	return keys.map((k) => {
		const rows = buckets.get(k) || [];
		return {
			key: k,
			label: groupLabelForKey(k, groupBy),
			leads: rows,
			count: rows.length,
		};
	});
}

/** Уникальные секции ОКВЭД (первые 2 цифры) из списка лидов. */
export function distinctOkvedSections(leads) {
	const counts = new Map();
	for (const l of leads || []) {
		const s = String(l.okvedSection || '').trim();
		if (!s) continue;
		counts.set(s, (counts.get(s) || 0) + 1);
	}
	return [...counts.entries()]
		.sort((a, b) => a[0].localeCompare(b[0], 'ru'))
		.map(([id, count]) => ({ id, label: `Секция ${id} (${count})` }));
}

const PRIORITY_RANK = { critical: 4, high: 3, medium: 2, low: 1 };

export function priorityRank(tierKey) {
	return PRIORITY_RANK[tierKey] ?? 0;
}

export function leadMatchesSearch(lead, query) {
	const q = String(query || '').trim().toLowerCase();
	if (!q) return true;
	const hay = [
		lead.company,
		lead.contact,
		lead.description,
		lead.city,
		lead.industry,
		lead.email,
		lead.phone,
	]
		.map((x) => String(x || '').toLowerCase())
		.join(' ');
	return hay.includes(q);
}

/** @param {Array<Record<string, unknown>>} leads */
function fieldContains(leadVal, filterVal) {
	const f = String(filterVal || '').trim().toLowerCase();
	if (!f) return true;
	return String(leadVal || '').toLowerCase().includes(f);
}

export function filterLeads(
	leads,
	{
		search = '',
		filterStage = 'all',
		filterPriority = 'all',
		filterScoreRisk = 'all',
		filterIndustry = '',
		filterCity = '',
		filterEmployeesBand = 'all',
		filterOkvedSection = 'all',
		minScore = null,
	},
	config = null,
) {
	return leads.filter((l) => {
		if (filterStage !== 'all' && l.stage !== filterStage) return false;
		if (filterPriority !== 'all') {
			const tier = leadPriorityTier(l.score, config);
			if (tier.key !== filterPriority) return false;
		}
		if (filterScoreRisk === 'warnings' && !l.hasScoreWarnings) return false;
		if (filterScoreRisk === 'divergent' && !l.scoreDivergent) return false;
		if (minScore != null && Number.isFinite(minScore)) {
			const sc = Number(l.score);
			if (!Number.isFinite(sc) || sc < minScore) return false;
		}
		if (!fieldContains(l.industry, filterIndustry)) return false;
		if (!fieldContains(l.city, filterCity)) return false;
		if (filterEmployeesBand !== 'all') {
			const band = String(l.employeesBand || '').trim();
			if (band !== filterEmployeesBand) return false;
		}
		if (filterOkvedSection !== 'all') {
			const sec = String(l.okvedSection || '').trim();
			if (sec !== filterOkvedSection) return false;
		}
		return leadMatchesSearch(l, search);
	});
}

/** @param {Record<string, unknown>} lead */
function scoreDeltaOf(lead) {
	if (lead.scoreDelta != null && Number.isFinite(Number(lead.scoreDelta))) {
		return Number(lead.scoreDelta);
	}
	const mgr = Number(lead.score);
	const sug = Number(lead.suggestedScore);
	if (!Number.isFinite(mgr) || !Number.isFinite(sug)) return 0;
	return Math.abs(mgr - sug);
}

/** @param {Array<Record<string, unknown>>} leads */
export function sortLeads(leads, sortBy = 'score_desc', config = null) {
	const rows = [...leads];
	const scoreOf = (l) => {
		const n = Number(l.score);
		return Number.isFinite(n) ? n : 0;
	};
	const warningsOf = (l) => {
		const n = Number(l.scoreWarningsCount);
		return Number.isFinite(n) ? n : 0;
	};
	const companyOf = (l) => String(l.company || '').toLocaleLowerCase('ru');

	switch (sortBy) {
		case 'score_asc':
			return rows.sort((a, b) => scoreOf(a) - scoreOf(b));
		case 'warnings_desc':
			return rows.sort((a, b) => warningsOf(b) - warningsOf(a) || scoreDeltaOf(b) - scoreDeltaOf(a));
		case 'score_delta_desc':
			return rows.sort((a, b) => scoreDeltaOf(b) - scoreDeltaOf(a) || warningsOf(b) - warningsOf(a));
		case 'priority_desc':
			return rows.sort((a, b) => {
				const ta = leadPriorityTier(a.score, config);
				const tb = leadPriorityTier(b.score, config);
				const dr = priorityRank(tb.key) - priorityRank(ta.key);
				if (dr !== 0) return dr;
				return scoreOf(b) - scoreOf(a);
			});
		case 'company_asc':
			return rows.sort((a, b) => companyOf(a).localeCompare(companyOf(b), 'ru'));
		case 'score_desc':
		default:
			return rows.sort((a, b) => scoreOf(b) - scoreOf(a));
	}
}

export function applyLeadListView(leads, opts, config = null) {
	const filtered = filterLeads(leads, opts, config);
	return sortLeads(filtered, opts.sortBy || 'score_desc', config);
}
