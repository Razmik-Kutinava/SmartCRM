<script>
	import { onMount, onDestroy } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	import { intentColor } from '$lib/opsCommon.js';

	const API = getApiUrl();

	let stats = $state(null);
	let agentStats = $state(null);
	let pollInterval = null;

	async function loadStats() {
		try {
			const [rStats, rAgents] = await Promise.all([
				fetch(`${API}/api/ops/stats`),
				fetch(`${API}/api/ops/analytics/agents?period_days=30`),
			]);
			stats = await rStats.json();
			if (rAgents.ok) agentStats = await rAgents.json();
		} catch (e) {
			console.error('stats error', e);
		}
	}

	onMount(() => {
		loadStats();
		pollInterval = setInterval(loadStats, 5000);
	});
	onDestroy(() => clearInterval(pollInterval));
</script>

<div class="px-6 py-6 max-w-4xl">
	<p class="text-sm text-gray-400 mb-6">Агрегаты по буферу трейсов (последние записи в памяти сервера).</p>

	{#if stats}
		<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
			<div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
				<div class="text-2xl font-bold text-white">{stats.total}</div>
				<div class="text-xs text-gray-500 mt-1">Команд всего</div>
			</div>
			<div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
				<div class="text-2xl font-bold text-white">{stats.avg_ms}<span class="text-sm font-normal text-gray-500">ms</span></div>
				<div class="text-xs text-gray-500 mt-1">Среднее время</div>
			</div>
			<div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
				<div class="text-2xl font-bold text-emerald-400">{stats.good}</div>
				<div class="text-xs text-gray-500 mt-1">Положительный фидбек</div>
			</div>
			<div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
				<div class="text-2xl font-bold text-red-400">{stats.bad}</div>
				<div class="text-xs text-gray-500 mt-1">Отрицательный фидбек</div>
			</div>
		</div>

		<div class="grid grid-cols-2 gap-4 mb-6">
			<div class="bg-gray-900 rounded-xl p-4 border border-gray-800 flex items-center gap-4">
				<div class="text-3xl opacity-80">⚡</div>
				<div>
					<div class="text-lg font-bold text-white">{stats.groq_pct}%</div>
					<div class="text-xs text-gray-500">Через Groq API</div>
				</div>
			</div>
			<div class="bg-gray-900 rounded-xl p-4 border border-gray-800 flex items-center gap-4">
				<div class="text-3xl opacity-80">🧠</div>
				<div>
					<div class="text-lg font-bold text-white">{stats.ollama_pct}%</div>
					<div class="text-xs text-gray-500">Через Ollama (fallback)</div>
				</div>
			</div>
		</div>

		<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
			<h3 class="text-sm font-medium text-gray-300 mb-3">Распределение по интентам</h3>
			<div class="space-y-2">
				{#each Object.entries(stats.by_intent || {}) as [intent, count]}
					<div class="flex items-center gap-3">
						<div class="w-36 shrink-0">
							<span class="text-xs px-2 py-0.5 rounded-full {intentColor(intent)}">{intent}</span>
						</div>
						<div class="flex-1 bg-gray-800 rounded-full h-2">
							<div
								class="h-2 rounded-full bg-indigo-500"
								style="width: {stats.total ? Math.round((count / stats.total) * 100) : 0}%"
							></div>
						</div>
						<div class="text-xs text-gray-400 w-8 text-right">{count}</div>
					</div>
				{/each}
			</div>
		</div>

		{#if agentStats?.agents?.some((a) => a.invocations > 0)}
			<div class="bg-gray-900 rounded-xl border border-gray-800 p-4 mt-6" data-testid="agent-effectiveness">
				<div class="flex items-center justify-between gap-4 mb-3 flex-wrap">
					<div>
						<h3 class="text-sm font-medium text-gray-300">Эффективность агентов</h3>
						<p class="text-xs text-gray-500 mt-0.5">
							По трейсам за {agentStats.periodDays || 30} дн. — 👍/👎 оператора
						</p>
					</div>
					<div class="flex gap-2 text-xs">
						<a href="/ops/intents/traces" class="text-indigo-400 hover:underline">Трейсы</a>
						<a href="/ops/intents/improve" class="text-indigo-400 hover:underline">A/B промптов</a>
						<a href="/ops/agents" class="text-indigo-400 hover:underline">Промпты агентов</a>
					</div>
				</div>
				{#if agentStats.attention?.length}
					<div class="mb-3 text-xs text-amber-400 bg-amber-900/20 border border-amber-800/40 rounded-lg px-3 py-2">
						Нужно внимание: {agentStats.attention.join(', ')} — откройте промпт или A/B по 👎
					</div>
				{/if}
				<div class="space-y-3">
					{#each agentStats.agents.filter((a) => a.invocations > 0) as row}
						<div class="flex flex-wrap items-center gap-3 text-sm border-b border-gray-800/60 pb-3 last:border-0">
							<span class="text-white font-medium w-28 shrink-0">{row.label}</span>
							<span class="text-gray-500 w-16">{row.invocations} выз.</span>
							<span class="text-emerald-400">👍 {row.good}</span>
							<span class="text-red-400">👎 {row.bad}</span>
							{#if row.satisfactionPct != null}
								<span class="text-gray-400">{row.satisfactionPct}% ок</span>
							{:else}
								<span class="text-gray-600">нет фидбека</span>
							{/if}
							{#if row.errors}
								<span class="text-red-300 text-xs">ошибок {row.errors}</span>
							{/if}
							<a href={row.improveUrl} class="ml-auto text-xs text-indigo-400 hover:underline">Улучшить →</a>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{:else}
		<div class="text-center text-gray-500 py-20">Загружается…</div>
	{/if}
</div>
