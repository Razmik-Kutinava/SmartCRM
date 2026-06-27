/** Фильтрация и сортировка списка лидов (/leads/list). */
import { leadPriorityTier } from '$lib/crmStages.js';
import { leadMatchesCoverageFilter } from '$lib/leads/leadCoverage.js';
import { leadMatchesManagerFilter } from '$lib/leads/leadManager.js';
import {
	deliveryTypeFromLead,
	subscriptionStatus,
} from '$lib/leads/leadBitrixExtra.js';

export const SORT_OPTIONS = [
	{ id: 'my_day', label: 'Мой день ↑' },
	{ id: 'tasks_urgent', label: 'Дела срочные ↑' },
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
		filterIndustryBucket: 'all',
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
	if (slots.industry) {
		const bucket = resolveIndustryBucketFilter(slots.industry);
		if (bucket) out.filterIndustryBucket = bucket;
		else out.filterIndustry = String(slots.industry).trim();
	}
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
		filterIndustryBucket: view.filterIndustryBucket ?? view.industryBucket ?? 'all',
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

/** Укрупнённые отрасли (синхрон с backend/core/okved_industry_map.py). */
export const INDUSTRY_BUCKET_OPTIONS = [
	{ id: 'all', label: 'Все отрасли' },
	{ id: 'IT и телеком', label: 'IT и телеком' },
	{ id: 'Финансы и страхование', label: 'Финансы и страхование' },
	{ id: 'Ритейл и e-commerce', label: 'Ритейл и e-commerce' },
	{ id: 'Производство', label: 'Производство' },
	{ id: 'Строительство', label: 'Строительство' },
	{ id: 'Транспорт и логистика', label: 'Транспорт и логистика' },
	{ id: 'Государственный сектор', label: 'Государственный сектор' },
	{ id: 'Образование', label: 'Образование' },
	{ id: 'Медицина и фарма', label: 'Медицина и фарма' },
	{ id: 'Энергетика', label: 'Энергетика' },
	{ id: 'Нефть и газ', label: 'Нефть и газ' },
	{ id: 'HoReCa', label: 'HoReCa' },
	{ id: 'Агропром', label: 'Агропром' },
	{ id: 'Медиа и реклама', label: 'Медиа и реклама' },
	{ id: 'Другое', label: 'Другое' },
];

export const GROUP_BY_OPTIONS = [
	{ id: 'none', label: 'Без группировки' },
	{ id: 'industry_bucket', label: 'Отрасль' },
	{ id: 'okved_section', label: 'ОКВЭД секция' },
	{ id: 'employees_band', label: 'Размер компании' },
	{ id: 'stage', label: 'Этап' },
];

const EMPTY_GROUP_KEY = '__empty__';

function resolveIndustryBucketFilter(text) {
	const t = String(text || '').trim();
	if (!t) return '';
	const low = t.toLowerCase();
	const exact = INDUSTRY_BUCKET_OPTIONS.find(
		(o) => o.id !== 'all' && o.id.toLowerCase() === low,
	);
	if (exact) return exact.id;
	for (const opt of INDUSTRY_BUCKET_OPTIONS) {
		if (opt.id === 'all') continue;
		if (opt.id.toLowerCase().includes(low) || low.includes(opt.id.toLowerCase().split(' ')[0])) {
			return opt.id;
		}
	}
	return '';
}

function groupKeyForLead(lead, groupBy) {
	switch (groupBy) {
		case 'industry_bucket':
			return String(lead.industryBucket || lead.industry || '').trim() || EMPTY_GROUP_KEY;
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
		if (groupBy === 'industry_bucket') return 'Без отрасли';
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

/** Счётчики отраслей (industryBucket) в текущем списке. */
export function distinctIndustryBuckets(leads) {
	const counts = new Map();
	for (const l of leads || []) {
		const b = String(l.industryBucket || l.industry || '').trim();
		if (!b || b === '—') continue;
		counts.set(b, (counts.get(b) || 0) + 1);
	}
	return [...counts.entries()]
		.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'ru'))
		.map(([id, count]) => ({ id, label: `${id} (${count})` }));
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

export const TASK_DUE_FILTERS = [
	{ id: 'all', label: 'Все дела' },
	{ id: 'today', label: 'Дело сегодня' },
	{ id: 'tomorrow', label: 'Дело завтра' },
	{ id: 'overdue', label: 'Просрочено' },
	{ id: 'has_open', label: 'Есть открытые' },
	{ id: 'on_date', label: 'На дату' },
];

/** Лид имеет открытое дело со сроком на ISO-дату (YYYY-MM-DD). */
export function leadHasOpenTaskOnDate(lead, isoDate) {
	const d = String(isoDate || '').trim();
	if (!d) return false;
	const dates = lead?.openTaskDueDates;
	if (Array.isArray(dates) && dates.length) {
		return dates.includes(d);
	}
	return false;
}

/** Сегодня в формате input[type=date] (локальная TZ). */
export function todayIsoDate(now = new Date()) {
	const y = now.getFullYear();
	const m = String(now.getMonth() + 1).padStart(2, '0');
	const day = String(now.getDate()).padStart(2, '0');
	return `${y}-${m}-${day}`;
}

export const SUBSCRIPTION_FILTERS = [
	{ id: 'all', label: 'Все подписки' },
	{ id: 'expiring', label: 'Истекает (30 дн.)' },
	{ id: 'expired', label: 'Просрочена' },
	{ id: 'has_date', label: 'Есть дата' },
];

/** Уникальные типы поставки из bitrixExtra.deliveryType. */
export function distinctDeliveryTypes(leads) {
	const counts = new Map();
	for (const l of leads || []) {
		const dt = deliveryTypeFromLead(l);
		if (!dt) continue;
		counts.set(dt, (counts.get(dt) || 0) + 1);
	}
	return [...counts.entries()]
		.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'ru'))
		.map(([id, count]) => ({ id, label: `${id} (${count})` }));
}

export function leadMatchesSubscriptionFilter(lead, filterId, now = new Date()) {
	if (!filterId || filterId === 'all') return true;
	const st = subscriptionStatus(lead, now);
	if (filterId === 'expiring') return st.kind === 'expiring';
	if (filterId === 'expired') return st.kind === 'expired';
	if (filterId === 'has_date') return st.kind !== 'none';
	return true;
}

export function leadMatchesDeliveryTypeFilter(lead, filterId) {
	if (!filterId || filterId === 'all') return true;
	return deliveryTypeFromLead(lead) === filterId;
}

const TASK_URGENCY_RANK = { overdue: 0, today: 1, upcoming: 2, open: 3, none: 4 };

export function taskUrgencyRank(lead) {
	const u = String(lead.taskUrgency || 'none');
	return TASK_URGENCY_RANK[u] ?? 4;
}

export function needsEnrichBadgeForLead(lead) {
	if (!lead?.needsEnrich) return null;
	return {
		label: 'Дозаполни',
		cls: 'text-fuchsia-300 bg-fuchsia-950/50 border-fuchsia-800/50 animate-pulse',
	};
}

export function taskDueBadgeForLead(lead) {
	if (lead.taskOverdue) return { label: 'Просрочено', cls: 'text-red-400 bg-red-950/60 border-red-900/50' };
	if (lead.taskDueToday) return { label: 'Сегодня', cls: 'text-amber-300 bg-amber-950/50 border-amber-900/40' };
	if (Number(lead.openTaskCount) > 0) return { label: 'Есть дела', cls: 'text-sky-400/90 bg-sky-950/40 border-sky-900/40' };
	return null;
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
		filterIndustryBucket = 'all',
		filterTaskDue = 'all',
		filterTaskDueDate = '',
		filterSubscription = 'all',
		filterDeliveryType = 'all',
		filterCoverage = 'all',
		filterManager = 'all',
		minScore = null,
	},
	config = null,
	now = new Date(),
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
		if (filterIndustryBucket !== 'all') {
			const bucket = String(l.industryBucket || l.industry || '').trim();
			if (bucket !== filterIndustryBucket) return false;
		}
		if (filterTaskDue === 'today' && !l.taskDueToday) return false;
		if (filterTaskDue === 'tomorrow' && !l.taskDueTomorrow) return false;
		if (filterTaskDue === 'overdue' && !l.taskOverdue) return false;
		if (filterTaskDue === 'has_open' && !(Number(l.openTaskCount) > 0)) return false;
		if (filterTaskDue === 'on_date' && !leadHasOpenTaskOnDate(l, filterTaskDueDate)) return false;
		if (!leadMatchesSubscriptionFilter(l, filterSubscription, now)) return false;
		if (!leadMatchesDeliveryTypeFilter(l, filterDeliveryType)) return false;
		if (!leadMatchesCoverageFilter(l, filterCoverage)) return false;
		if (!leadMatchesManagerFilter(l, filterManager)) return false;
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
		case 'my_day':
			return rows.sort((a, b) => {
				const ra = Number(a.dayRank);
				const rb = Number(b.dayRank);
				const da = Number.isFinite(ra) ? ra : 1e9;
				const db = Number.isFinite(rb) ? rb : 1e9;
				if (da !== db) return da - db;
				const amtA = Number(a.amount ?? a.deal_amount ?? 0) || 0;
				const amtB = Number(b.amount ?? b.deal_amount ?? 0) || 0;
				if (amtB !== amtA) return amtB - amtA;
				return companyOf(a).localeCompare(companyOf(b), 'ru');
			});
		case 'tasks_urgent':
			return rows.sort(
				(a, b) =>
					taskUrgencyRank(a) - taskUrgencyRank(b)
					|| scoreOf(b) - scoreOf(a)
					|| companyOf(a).localeCompare(companyOf(b), 'ru'),
			);
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
