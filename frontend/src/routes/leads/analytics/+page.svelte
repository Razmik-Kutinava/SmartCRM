<script>
	import { onMount } from 'svelte';
	import { apiFetch } from '$lib/api.js';
	import { fetchLeads } from '$lib/leadsStorage.js';
	import { CRM_STAGES, loadCrmConfig } from '$lib/crmStages.js';
	import { computeAnalytics, formatRub } from '$lib/leads/analyticsMetrics.js';

	let metrics = $state(null);
	let loading = $state(true);
	let err = $state('');
	let exporting = $state(false);

	onMount(async () => {
		await loadCrmConfig();
		try {
			const r = await apiFetch('/api/leads/analytics/summary');
			if (r.ok) {
				metrics = await r.json();
			} else {
				const leads = await fetchLeads();
				metrics = computeAnalytics(leads, CRM_STAGES);
			}
		} catch (e) {
			try {
				const leads = await fetchLeads();
				metrics = computeAnalytics(leads, CRM_STAGES);
			} catch (e2) {
				err = e2?.message || e?.message || String(e2);
			}
		} finally {
			loading = false;
		}
	});

	async function exportReport() {
		exporting = true;
		try {
			const r = await apiFetch('/api/leads/analytics/export');
			if (!r.ok) throw new Error(`Экспорт: HTTP ${r.status}`);
			const blob = await r.blob();
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `analytics-${new Date().toISOString().slice(0, 10)}.csv`;
			a.click();
			URL.revokeObjectURL(url);
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			exporting = false;
		}
	}
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden">
	<div class="px-6 py-3 border-b border-gray-800 bg-gray-900 shrink-0 flex items-center justify-between gap-4">
		<div>
			<h1 class="text-lg font-semibold text-white">Аналитика CRM</h1>
			<p class="text-xs text-gray-500">Воронка и KPI по лидам в БД</p>
		</div>
		<button
			type="button"
			class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors disabled:opacity-50"
			disabled={loading || exporting || !metrics}
			onclick={exportReport}
		>
			{exporting ? 'Экспорт…' : '📥 Экспорт отчёта'}
		</button>
	</div>
	<div class="flex-1 overflow-y-auto p-6 space-y-6">
		{#if loading}
			<p class="text-gray-500">Загрузка…</p>
		{:else if err}
			<p class="text-red-400">{err}</p>
		{:else if metrics}
			<div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 max-w-5xl">
				<div class="rounded-xl border border-gray-800 bg-gray-900/80 p-4">
					<div class="text-xs text-gray-500 uppercase">Всего лидов</div>
					<div class="text-3xl font-bold text-white mt-1">{metrics.total}</div>
				</div>
				<div class="rounded-xl border border-gray-800 bg-gray-900/80 p-4">
					<div class="text-xs text-gray-500 uppercase">Конверсия в сделку</div>
					<div class="text-3xl font-bold text-green-400 mt-1">{metrics.conversionPct}%</div>
					{#if metrics.winRatePct != null}
						<div class="text-xs text-gray-500 mt-1">Win-rate: {metrics.winRatePct}%</div>
					{/if}
				</div>
				<div class="rounded-xl border border-gray-800 bg-gray-900/80 p-4">
					<div class="text-xs text-gray-500 uppercase">Средний чек</div>
					<div class="text-2xl font-bold text-white mt-1">{formatRub(metrics.avgDealRub)}</div>
					<div class="text-xs text-gray-500 mt-1">по выигранным с суммой</div>
				</div>
				<div class="rounded-xl border border-gray-800 bg-gray-900/80 p-4">
					<div class="text-xs text-gray-500 uppercase">Цикл сделки</div>
					<div class="text-3xl font-bold text-indigo-400 mt-1">
						{metrics.avgCycleDays != null ? `${metrics.avgCycleDays} дн.` : '—'}
					</div>
				</div>
			</div>

			<div class="grid sm:grid-cols-2 gap-4 max-w-5xl">
				<div class="rounded-xl border border-gray-800 bg-gray-900/80 p-4">
					<div class="text-xs text-gray-500 uppercase">Средний скоринг</div>
					<div class="text-3xl font-bold text-indigo-400 mt-1">{metrics.avgScore}</div>
				</div>
				<div class="rounded-xl border border-gray-800 bg-gray-900/80 p-4">
					<div class="text-xs text-gray-500 uppercase">Выиграно / проиграно</div>
					<div class="text-3xl font-bold text-white mt-1">
						{metrics.wonCount} / {metrics.lostCount}
					</div>
				</div>
			</div>

			<div class="max-w-3xl">
				<h2 class="text-sm font-medium text-white mb-3">Воронка по этапам</h2>
				<div class="space-y-2">
					{#each metrics.funnel as item}
						<div class="flex items-center gap-3">
							<span class="text-xs text-gray-500 w-36 shrink-0">{item.stage}</span>
							<div class="flex-1 h-2 rounded-full bg-gray-800 overflow-hidden">
								<div
									class="h-full bg-indigo-600 rounded-full transition-all"
									style="width: {item.pct}%"
								></div>
							</div>
							<span class="text-xs text-gray-400 w-12 text-right">{item.count}</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>
