/** Quality gate 6 агентов — хелперы UI */

export const DEFAULT_GATE_DATASET = 'eval-failed-gate';

export const GATE_AGENTS = [
	{ id: 'hermes', label: 'Hermes' },
	{ id: 'analyst', label: 'Analyst' },
	{ id: 'economist', label: 'Economist' },
	{ id: 'marketer', label: 'Marketer' },
	{ id: 'strategist', label: 'Strategist' },
	{ id: 'tech_specialist', label: 'Tech' }
];

export const GATE_RUN_MODES = [
	{ id: 'all', label: 'Hermes + 5 агентов' },
	{ id: 'hermes_only', label: 'Только Hermes' },
	{ id: 'agents_only', label: 'Только 5 агентов' }
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

export function gateDownloadUrl(apiBase) {
	return `${apiBase}/api/ops/eval/agents-gate/latest/download`;
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

export function failedRowsForTab(gateData, agentTab) {
	return gateRowsForAgent(gateData, agentTab).filter((r) => !r.passed);
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

export function runModeToBody(mode, hermesLimit, agentLimit) {
	const body = {
		save_artifact: true,
		write_acceptance: false,
		hermes_limit: hermesLimit || 0,
		agent_limit: agentLimit || 0,
		hermes_only: false,
		agents_only: false
	};
	if (mode === 'hermes_only') body.hermes_only = true;
	if (mode === 'agents_only') body.agents_only = true;
	return body;
}
