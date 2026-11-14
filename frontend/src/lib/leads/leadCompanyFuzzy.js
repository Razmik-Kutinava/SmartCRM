/** Нечёткий матч названия компании для /leads/list (зеркало core/lead_company_fuzzy.py). */

export const FUZZY_TOP_N = 5;

const SEARCH_FIELDS = ['company', 'contact', 'description', 'city', 'industry', 'email', 'phone'];

export function normalizeCompanyQuery(raw) {
	return String(raw || '')
		.trim()
		.toLowerCase()
		.replace(/ё/g, 'е')
		.replace(/\s+/g, ' ');
}

function compact(text) {
	return String(text || '').replace(/\s+/g, '');
}

/** Простой SequenceMatcher.ratio (difflib-подобный). */
function sequenceRatio(a, b) {
	const s = String(a || '');
	const t = String(b || '');
	if (!s && !t) return 1;
	if (!s || !t) return 0;
	const n = s.length;
	const m = t.length;
	const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
	for (let i = 1; i <= n; i++) {
		for (let j = 1; j <= m; j++) {
			if (s[i - 1] === t[j - 1]) dp[i][j] = dp[i - 1][j - 1] + 1;
			else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
		}
	}
	return (2 * dp[n][m]) / (n + m);
}

export function companyNameSimilarity(query, company) {
	const q = normalizeCompanyQuery(query);
	const c = normalizeCompanyQuery(company);
	if (!q || !c) return 0;
	if (q === c) return 1;
	if (q.includes(c) || c.includes(q)) return 0.96;

	const qC = compact(q);
	const cC = compact(c);
	const ratios = [sequenceRatio(q, c), sequenceRatio(qC, cC)];

	const qTokens = q.split(' ').filter(Boolean);
	const cTokens = c.split(' ').filter(Boolean);
	if (qTokens.length && cTokens.length) {
		let tokenHits = 0;
		for (const qt of qTokens) {
			let best = 0;
			for (const ct of cTokens) {
				best = Math.max(best, sequenceRatio(qt, ct));
			}
			tokenHits += best;
		}
		ratios.push(tokenHits / qTokens.length);
	}

	let prefix = 0;
	const lim = Math.min(qC.length, cC.length);
	while (prefix < lim && qC[prefix] === cC[prefix]) prefix += 1;
	if (qC.length && prefix) {
		ratios.push(0.55 + 0.45 * (prefix / Math.max(qC.length, cC.length)));
	}

	return Math.max(...ratios);
}

export function rankLeadsByCompanyFuzzy(leads, query, { limit = FUZZY_TOP_N } = {}) {
	const q = normalizeCompanyQuery(query);
	const rows = Array.isArray(leads) ? leads : [];
	if (!q) return rows.slice(0, limit);
	const scored = rows.map((lead, i) => ({
		score: companyNameSimilarity(q, String(lead?.company || '')),
		i,
		lead,
	}));
	scored.sort((a, b) => b.score - a.score || a.i - b.i);
	const n = Math.max(1, Number(limit) || FUZZY_TOP_N);
	return scored.slice(0, n).map((x) => x.lead);
}

export function leadMatchesSearchExact(lead, query) {
	const q = normalizeCompanyQuery(query);
	if (!q) return true;
	const hay = SEARCH_FIELDS.map((k) => String(lead?.[k] || '').toLowerCase().replace(/ё/g, 'е')).join(' ');
	return hay.includes(q);
}

/** Exact/includes сначала; иначе топ-N fuzzy по company. */
export function filterLeadsSearch(leads, query, { fuzzyLimit = FUZZY_TOP_N } = {}) {
	const rows = Array.isArray(leads) ? leads : [];
	const q = String(query || '').trim();
	if (!q) return rows;
	const exact = rows.filter((l) => leadMatchesSearchExact(l, q));
	if (exact.length) return exact;
	return rankLeadsByCompanyFuzzy(rows, q, { limit: fuzzyLimit }).map((lead) => ({
		...lead,
		_searchMatch: 'fuzzy',
	}));
}
