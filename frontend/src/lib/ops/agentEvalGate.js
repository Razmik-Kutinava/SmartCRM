/** Quality gate 6 агентов — хелперы UI */

export const GATE_AGENTS = [
	{ id: 'hermes', label: 'Hermes' },
	{ id: 'analyst', label: 'Analyst' },
	{ id: 'economist', label: 'Economist' },
	{ id: 'marketer', label: 'Marketer' },
	{ id: 'strategist', label: 'Strategist' },
	{ id: 'tech_specialist', label: 'Tech' }
];

export function gateEmoji(gate) {
	if (gate === 'pass') return '✅';
	if (gate === 'warn') return '🟡';
	if (gate === 'fail') return '🔴';
	return '🔲';
}

export function rateColor(pct, threshold) {
	if (pct >= threshold) return 'text-emerald-400';
	if (pct >= threshold - 5) return 'text-amber-400';
	return 'text-red-400';
}

/** Строки таблицы для вкладки агента */
export function gateRowsForAgent(gateData, agentTab) {
	if (!gateData?.found || !gateData.agents) return [];
	if (agentTab === 'all') {
		const rows = [];
		for (const [agent, block] of Object.entries(gateData.agents)) {
			for (const r of block.results || []) {
				rows.push({ ...r, agent });
			}
		}
		return rows;
	}
	const block = gateData.agents[agentTab];
	if (!block) return [];
	return (block.results || []).map((r) => ({ ...r, agent: agentTab }));
}

export function agentSummaryCards(gateData) {
	if (!gateData?.found) return [];
	return GATE_AGENTS.map(({ id, label }) => {
		const s = gateData.agents?.[id]?.summary;
		if (!s) return { id, label, missing: true };
		return {
			id,
			label,
			pass_rate: s.pass_rate_pct,
			threshold: s.threshold_pct,
			gate: s.gate,
			passed: s.passed,
			failed: s.failed,
			total: s.total
		};
	}).filter(Boolean);
}
