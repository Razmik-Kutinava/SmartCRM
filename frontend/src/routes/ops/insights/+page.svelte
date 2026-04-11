<script>
	import { onMount, onDestroy } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

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

	onMount(() => {
		load();
		pollInterval = setInterval(load, 20000);
	});
	onDestroy(() => clearInterval(pollInterval));
</script>

<div class="px-6 py-6 max-w-3xl">
	<p class="text-sm text-gray-400 mb-6">
		Автоматические наблюдения по трейсам (без вызова LLM): что смотреть, когда обновлять промпт и когда гонять eval. Проценты
		уверенности — относительная оценка полезности, не вероятность модели.
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
				<li>Доля негативного фидбека (где есть оценки): {insight.signals?.bad_feedback_ratio ?? 0}</li>
			</ul>
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
