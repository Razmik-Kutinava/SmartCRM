/** Метрики воронки и KPI (зеркало backend/core/analytics_metrics.py). */

export const WON_STAGE = 'Выигран';
export const LOST_STAGE = 'Проигран';

export const PERIOD_LABELS = {
	week: 'неделя',
	month: 'месяц',
	quarter: 'квартал',
	year: 'год',
	last_year: 'прошлый год',
};

const PERIOD_DAYS = { week: 7, month: 30, quarter: 90, year: 365 };

export function parseBudgetRub(raw) {
	if (!raw) return null;
	const s = String(raw).replace(/\s/g, '').replace(/[^\d.,]/g, '').replace(',', '.');
	if (!s) return null;
	const v = Number(s);
	return Number.isFinite(v) && v > 0 ? v : null;
}

export function leadAmountRub(lead) {
	if (lead?.amountRub != null && lead.amountRub !== '') {
		const v = Number(lead.amountRub);
		if (Number.isFinite(v) && v > 0) return v;
	}
	const amt = lead?.amount;
	const cur = String(lead?.currency || '').toUpperCase();
	if (amt != null && amt !== '' && (cur === 'RUB' || cur === 'RUR')) {
		const v = Number(amt);
		if (Number.isFinite(v) && v > 0) return v;
	}
	return parseBudgetRub(lead?.budget);
}

function parseIsoDate(value) {
	if (!value) return null;
	const d = new Date(value);
	return Number.isNaN(d.getTime()) ? null : d;
}

function parseCreatedDate(lead) {
	if (lead?.createdAt) return parseIsoDate(lead.createdAt);
	const c = lead?.created;
	if (c && c !== '—') {
		const m = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(String(c));
		if (m) return new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
	}
	return null;
}

function normalizeStage(stage, stages) {
	const s = String(stage || 'Новый').trim();
	return stages.includes(s) ? s : 'Новый';
}

function leadSource(lead) {
	return String(lead?.source || '—').trim() || '—';
}

/** @param {object[]} leads @param {string | null | undefined} period */
export function filterLeadsByPeriod(leads, period) {
	if (!period) return leads;
	const now = new Date();
	let start;
	let end;
	if (period === 'last_year') {
		start = new Date(now.getFullYear() - 1, 0, 1);
		end = new Date(now.getFullYear(), 0, 1);
	} else {
		const days = PERIOD_DAYS[period] || 7;
		start = new Date(now.getTime() - days * 86400000);
		end = null;
	}
	return leads.filter((lead) => {
		const created = parseCreatedDate(lead);
		if (!created) return false;
		if (period === 'last_year') return created >= start && created < end;
		return created >= start;
	});
}

/** @param {object[]} leads @param {string | null | undefined} source */
export function filterLeadsBySource(leads, source) {
	if (!source) return leads;
	const needle = String(source).trim().toLowerCase();
	return leads.filter((lead) => leadSource(lead).toLowerCase().includes(needle));
}

/** @param {object[]} leads @param {string[]} stages */
export function computeConversionBySource(leads, stages) {
	const buckets = new Map();
	for (const lead of leads) {
		const src = leadSource(lead);
		const row = buckets.get(src) || { source: src, total: 0, won: 0 };
		row.total += 1;
		if (normalizeStage(lead.stage, stages) === WON_STAGE) row.won += 1;
		buckets.set(src, row);
	}
	return [...buckets.values()]
		.sort((a, b) => b.total - a.total)
		.map((row) => ({
			...row,
			conversionPct: row.total ? Math.round((1000 * row.won) / row.total) / 10 : 0,
		}));
}

/** @param {object[]} leads @param {string[]} stages */
export function computeFunnelBySource(leads, stages, topSources = 8) {
	const buckets = new Map();
	for (const lead of leads) {
		const src = leadSource(lead);
		if (!buckets.has(src)) buckets.set(src, []);
		buckets.get(src).push(lead);
	}
	return [...buckets.entries()]
		.sort((a, b) => b[1].length - a[1].length)
		.slice(0, topSources)
		.map(([source, srcLeads]) => {
			const mini = computeAnalytics(srcLeads, stages);
			return {
				source,
				total: mini.total,
				wonCount: mini.wonCount,
				lostCount: mini.lostCount,
				conversionPct: mini.conversionPct,
				funnel: mini.funnel,
			};
		});
}

/** @param {object[]} leads @param {string[]} stages @param {{ period?: string, source?: string }} [filters] */
export function computeAnalyticsReport(leads, stages, filters = {}) {
	const filtered = filterLeadsBySource(filterLeadsByPeriod(leads, filters.period), filters.source);
	const metrics = computeAnalytics(filtered, stages);
	return {
		...metrics,
		conversionBySource: computeConversionBySource(filtered, stages),
		funnelBySource: computeFunnelBySource(filtered, stages),
		closureForecast: computeClosureForecast(filtered, stages),
		filters: {
			period: filters.period || '',
			periodLabel: filters.period ? PERIOD_LABELS[filters.period] || filters.period : '',
			source: filters.source || '',
		},
	};
}

/** @param {object[]} leads @param {string[]} stages */
export function computeAnalytics(leads, stages) {
	const sts = stages?.length ? stages : [];
	const byStage = Object.fromEntries(sts.map((s) => [s, 0]));
	const total = leads.length;
	let won = 0;
	let lost = 0;
	const dealAmounts = [];
	const cycleDays = [];

	for (const lead of leads) {
		const st = normalizeStage(lead.stage, sts);
		byStage[st] = (byStage[st] || 0) + 1;
		if (st === WON_STAGE) {
			won += 1;
			const amt = leadAmountRub(lead);
			if (amt != null) dealAmounts.push(amt);
			const created = parseCreatedDate(lead);
			const updated = parseIsoDate(lead.updatedAt);
			if (created && updated) {
				const delta = Math.round((updated - created) / 86400000);
				if (delta >= 0) cycleDays.push(delta);
			}
		} else if (st === LOST_STAGE) {
			lost += 1;
		}
	}

	const funnel = sts.map((stage) => {
		const count = byStage[stage] || 0;
		const pct = total ? Math.round((1000 * count) / total) / 10 : 0;
		return { stage, count, pct };
	});

	const conversionPct = total ? Math.round((1000 * won) / total) / 10 : 0;
	const winRatePct = won + lost ? Math.round((1000 * won) / (won + lost)) / 10 : null;
	const avgDealRub = dealAmounts.length
		? Math.round(dealAmounts.reduce((a, b) => a + b, 0) / dealAmounts.length)
		: null;
	const avgCycleDays = cycleDays.length
		? Math.round(cycleDays.reduce((a, b) => a + b, 0) / cycleDays.length)
		: null;
	const avgScore = total
		? Math.round(leads.reduce((a, l) => a + (Number(l.score) || 0), 0) / total)
		: 0;

	return {
		total,
		wonCount: won,
		lostCount: lost,
		avgScore,
		byStage,
		funnel,
		conversionPct,
		winRatePct,
		avgDealRub,
		avgCycleDays,
	};
}

export function formatRub(value) {
	if (value == null) return '—';
	return new Intl.NumberFormat('ru-RU', {
		style: 'currency',
		currency: 'RUB',
		maximumFractionDigits: 0,
	}).format(value);
}

const STAGE_CLOSE_BASE = {
	Новый: 8,
	Квалифицирован: 18,
	'КП отправлено': 35,
	Переговоры: 58,
	Выигран: 100,
	Проигран: 0,
};

function forecastTier(pct) {
	if (pct >= 55) return 'high';
	if (pct >= 25) return 'medium';
	return 'low';
}

/** @param {object} lead @param {string[]} stages */
export function forecastLeadClose(lead, stages) {
	const st = normalizeStage(lead.stage, stages);
	const score = Math.max(0, Math.min(100, Number(lead.score) || 50));
	let prob;
	if (st === WON_STAGE) prob = 100;
	else if (st === LOST_STAGE) prob = 0;
	else {
		const base = STAGE_CLOSE_BASE[st] ?? 10;
		prob = Math.round((base * 0.55 + score * 0.45) * 10) / 10;
		prob = Math.max(1, Math.min(95, prob));
	}
	const amount = leadAmountRub(lead);
	return {
		leadId: lead.id,
		company: lead.company || '—',
		stage: st,
		score,
		closeProbabilityPct: prob,
		tier: forecastTier(prob),
		expectedRub: amount != null ? Math.round((amount * prob) / 100) : null,
	};
}

/** @param {object[]} leads @param {string[]} stages */
export function computeClosureForecast(leads, stages, topLimit = 15) {
	const active = leads
		.filter((l) => {
			const st = normalizeStage(l.stage, stages);
			return st !== WON_STAGE && st !== LOST_STAGE;
		})
		.map((l) => forecastLeadClose(l, stages));
	if (!active.length) {
		return { activeLeads: 0, avgProbabilityPct: 0, expectedPipelineRub: 0, tiers: {}, topOpportunities: [] };
	}
	const tiers = { high: 0, medium: 0, low: 0 };
	let probSum = 0;
	let expected = 0;
	for (const row of active) {
		tiers[row.tier] = (tiers[row.tier] || 0) + 1;
		probSum += row.closeProbabilityPct;
		if (row.expectedRub) expected += row.expectedRub;
	}
	const ranked = [...active].sort(
		(a, b) => (b.expectedRub || 0) - (a.expectedRub || 0) || b.closeProbabilityPct - a.closeProbabilityPct,
	);
	return {
		activeLeads: active.length,
		avgProbabilityPct: Math.round((probSum / active.length) * 10) / 10,
		expectedPipelineRub: expected,
		tiers,
		topOpportunities: ranked.slice(0, topLimit),
		method: 'economist_heuristic',
	};
}
