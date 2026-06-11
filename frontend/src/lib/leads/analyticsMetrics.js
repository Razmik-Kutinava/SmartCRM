/** Метрики воронки и KPI (зеркало backend/core/analytics_metrics.py). */

export const WON_STAGE = 'Выигран';
export const LOST_STAGE = 'Проигран';

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
