<script>
	import { onMount, onDestroy } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	import { intentColor } from '$lib/opsCommon.js';

	const API = getApiUrl();

	let stats = $state(null);
	let pollInterval = null;

	async function loadStats() {
		try {
			const r = await fetch(`${API}/api/ops/stats`);
			stats = await r.json();
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
	{:else}
		<div class="text-center text-gray-500 py-20">Загружается…</div>
	{/if}
</div>
