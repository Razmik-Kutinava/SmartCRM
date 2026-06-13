<script>
	import { onMount, onDestroy } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	import { GATE_AGENTS, gateEmoji, rateColor } from '$lib/ops/agentEvalGate.js';

	const API = getApiUrl();

	let insight = $state(null);
	let loading = $state(true);
	let pollInterval = null;

	async function load() {
		try {
			const r = await fetch(`${API}/api/ops/insights`);
			insight = await r.json();
		} catch (e) {
			console.error(e);
		} finally {
			loading = false;
		}
	}

	function agentRateCards(gate) {
		if (!gate?.agents) return [];
		return GATE_AGENTS.map(({ id, label }) => {
			const s = gate.agents[id];
			if (!s) return null;
			return {
				id,
				label,
				pass_rate: s.pass_rate_pct ?? 0,
				threshold: s.threshold_pct ?? 75,
				gate: s.gate ?? 'fail',
				passed: s.passed ?? 0,
				total: s.total ?? 0
			};
		}).filter(Boolean);
	}

	onMount(() => {
		load();
		pollInterval = setInterval(load, 20000);
	});
	onDestroy(() => clearInterval(pollInterval));
</script>

<div class="px-6 py-6 max-w-3xl">
	<p class="text-sm text-gray-400 mb-6">
		Автоматические наблюдения по трейсам (без вызова LLM): что смотреть, когда обновлять промпт и когда гонять eval.
	</p>

	{#if loading}
		<p class="text-gray-500">Загрузка…</p>
	{:else if insight}
		<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-8">
			<h3 class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Сигналы</h3>
			<ul class="text-sm text-gray-300 space-y-1">
				<li>Ошибки в последних трейсах: {insight.signals?.errors_recent ?? 0} (~{insight.signals?.error_pct ?? 0}%)</li>
				<li>
					Фидбек: положительных {insight.signals?.feedback_good ?? 0}, отрицательных {insight.signals?.feedback_bad ?? 0}
				</li>
				<li>Доля негативного фидбека: {insight.signals?.bad_feedback_ratio ?? 0}</li>
			</ul>
		</div>

		<div class="bg-gray-900 border border-violet-900/50 rounded-xl p-4 mb-8">
			<h3 class="text-xs font-medium text-violet-400 uppercase tracking-wide mb-2">Quality gate</h3>
			{#if insight.gate?.found}
				<p class="text-sm text-gray-300 mb-3">
					{gateEmoji(insight.gate.overall_gate)} {insight.gate.overall_gate}
					· <span class="text-gray-500">{insight.gate.artifact_name}</span>
				</p>
				<div class="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-3">
					{#each agentRateCards(insight.gate) as c}
						<div class="bg-gray-950 border border-gray-800 rounded-lg p-2">
							<div class="text-xs text-gray-500">{c.label}</div>
							<div class="text-lg font-bold {rateColor(c.pass_rate, c.threshold)}">{c.pass_rate}%</div>
							<div class="text-xs text-gray-600">{gateEmoji(c.gate)} {c.passed}/{c.total}</div>
						</div>
					{/each}
				</div>
				{#if insight.gate.gaps?.length}
					<ul class="text-xs text-gray-400 space-y-1 mb-2">
						{#each insight.gate.gaps as g}
							<li>• {g}</li>
						{/each}
					</ul>
				{/if}
			{:else}
				<p class="text-sm text-amber-400/90 mb-2">
					Артефакт gate не найден. Сначала запустите gate на
					<a href="/ops/intents/eval" class="text-indigo-400 hover:underline">/ops/intents/eval</a>
					→ вкладка «Quality gate».
				</p>
			{/if}
			<a href="/ops/intents/eval" class="text-xs text-indigo-400 hover:underline">→ Eval / gate</a>
		</div>

		<h2 class="text-sm font-medium text-gray-300 mb-3">Предложения</h2>
		<div class="space-y-3">
			{#each insight.suggestions || [] as p}
				<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
					<div class="flex items-start justify-between gap-3">
						<h3 class="text-white font-medium">{p.title}</h3>
						<span class="text-xs text-gray-500 shrink-0">уверенность {Math.round((p.confidence || 0) * 100)}%</span>
					</div>
					<p class="text-sm text-gray-400 mt-2 leading-relaxed">{p.body}</p>
				</div>
			{/each}
		</div>
	{:else}
		<p class="text-gray-500">Нет данных.</p>
	{/if}
</div>
