<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { apiFetch } from '$lib/api.js';
	import { fetchLeads } from '$lib/leadsStorage.js';
	import { CRM_STAGES, loadCrmConfig } from '$lib/crmStages.js';
	import {
		computeAnalyticsReport,
		formatRub,
		PERIOD_LABELS,
	} from '$lib/leads/analyticsMetrics.js';
	import { voiceAnalyticsContext } from '$lib/voice/voiceAction.js';

	let metrics = $state(null);
	let loading = $state(true);
	let err = $state('');
	let exporting = $state(false);
	let voiceCtx = $state(null);
	let activeView = $state('');
	let selectedFunnelSource = $state('');

	function readFilters() {
		const params = $page.url.searchParams;
		const voice = voiceCtx || {};
		const period = params.get('period') || voice.period || '';
		const source = params.get('source') || voice.source || '';
		const view = params.get('view') || voice.intent?.replace?.('analytics_', '') || '';
		activeView = view;
		return { period, source, view };
	}

	function summaryQuery(filters) {
		const q = new URLSearchParams();
		if (filters.period) q.set('period', filters.period);
		if (filters.source) q.set('source', filters.source);
		const qs = q.toString();
		return qs ? `/api/leads/analytics/summary?${qs}` : '/api/leads/analytics/summary';
	}

	async function loadMetrics() {
		loading = true;
		err = '';
		const filters = readFilters();
		try {
			const r = await apiFetch(summaryQuery(filters));
			if (r.ok) {
				metrics = await r.json();
				const blocks = metrics?.funnelBySource || [];
				if (blocks.length && !blocks.some((b) => b.source === selectedFunnelSource)) {
					selectedFunnelSource = blocks[0].source;
				}
			} else {
				const leads = await fetchLeads();
				metrics = computeAnalyticsReport(leads, CRM_STAGES, filters);
			}
		} catch (e) {
			try {
				const leads = await fetchLeads();
				metrics = computeAnalyticsReport(leads, CRM_STAGES, filters);
			} catch (e2) {
				err = e2?.message || e?.message || String(e2);
			}
		} finally {
			loading = false;
		}
	}

	onMount(async () => {
		const unsubVoice = voiceAnalyticsContext.subscribe((v) => {
			voiceCtx = v;
		});
		const unsubPage = page.subscribe(() => {
			loadMetrics();
		});
		await loadCrmConfig();
		await loadMetrics();
		return () => {
			unsubVoice();
			unsubPage();
		};
	});

	async function exportReport() {
		exporting = true;
		const filters = readFilters();
		try {
			const q = new URLSearchParams();
			if (filters.period) q.set('period', filters.period);
			if (filters.source) q.set('source', filters.source);
			const qs = q.toString();
			const path = qs ? `/api/leads/analytics/export?${qs}` : '/api/leads/analytics/export';
			const r = await apiFetch(path);
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

	const periodLabel = $derived(
		metrics?.filters?.periodLabel ||
			PERIOD_LABELS[metrics?.filters?.period] ||
			metrics?.filters?.period ||
			voiceCtx?.periodLabel ||
			'',
	);

	const activeFunnelBlock = $derived(
		(metrics?.funnelBySource || []).find((b) => b.source === selectedFunnelSource) ||
			metrics?.funnelBySource?.[0] ||
			null,
	);
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden">
	<div class="px-6 py-3 border-b border-gray-800 bg-gray-900 shrink-0 flex items-center justify-between gap-4">
		<div>
			<h1 class="text-lg font-semibold text-white">Аналитика CRM</h1>
			<p class="text-xs text-gray-500">Воронка и KPI по лидам в БД</p>
			{#if voiceCtx?.periodLabel || voiceCtx?.title || metrics?.filters?.period || metrics?.filters?.source}
				<p class="text-xs text-indigo-400 mt-1" data-testid="voice-analytics-context">
					🎙 {voiceCtx?.title || 'Аналитика'}
					{#if periodLabel} · период: {periodLabel}{/if}
					{#if metrics?.filters?.source || voiceCtx?.source}
						· источник: {metrics?.filters?.source || voiceCtx?.source}
					{/if}
				</p>
			{/if}
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
				<div class="rounded-xl border border-gray-800 bg-gray-900/80 p-4" data-testid="kpi-funnel">
					<div class="text-xs text-gray-500 uppercase">Всего лидов</div>
					<div class="text-3xl font-bold text-white mt-1">{metrics.total}</div>
				</div>
				<div
					class="rounded-xl border border-gray-800 bg-gray-900/80 p-4"
					data-testid="kpi-conversion"
					class:ring-1={activeView === 'conversion'}
					class:ring-indigo-500={activeView === 'conversion'}
				>
					<div class="text-xs text-gray-500 uppercase">Конверсия в сделку</div>
					<div class="text-3xl font-bold text-green-400 mt-1">{metrics.conversionPct}%</div>
					{#if metrics.winRatePct != null}
						<div class="text-xs text-gray-500 mt-1">Win-rate: {metrics.winRatePct}%</div>
					{/if}
				</div>
				<div
					class="rounded-xl border border-gray-800 bg-gray-900/80 p-4"
					data-testid="kpi-cycle"
					class:ring-1={activeView === 'cycle'}
					class:ring-indigo-500={activeView === 'cycle'}
				>
					<div class="text-xs text-gray-500 uppercase">Средний чек</div>
					<div class="text-2xl font-bold text-white mt-1">{formatRub(metrics.avgDealRub)}</div>
					<div class="text-xs text-gray-500 mt-1">по выигранным с суммой</div>
				</div>
				<div class="rounded-xl border border-gray-800 bg-gray-900/80 p-4" data-testid="kpi-cycle-days">
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

			<div class="max-w-3xl" data-testid="analytics-funnel" class:ring-1={activeView === 'funnel'} class:ring-indigo-500={activeView === 'funnel'} class:rounded-xl={activeView === 'funnel'} class:p-2={activeView === 'funnel'}>
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

			{#if metrics.cohorts?.length}
				<div
					class="max-w-3xl"
					data-testid="analytics-cohorts"
					class:ring-1={activeView === 'cohorts'}
					class:ring-indigo-500={activeView === 'cohorts'}
					class:rounded-xl={activeView === 'cohorts'}
					class:p-2={activeView === 'cohorts'}
				>
					<h2 class="text-sm font-medium text-white mb-3">Когорты по месяцу входа</h2>
					<p class="text-xs text-gray-500 mb-3">Лиды, пришедшие в месяц → сколько выиграли</p>
					<div class="space-y-2">
						{#each metrics.cohorts as row}
							<div class="flex items-center gap-3 text-sm flex-wrap">
								<span class="text-gray-300 w-24 shrink-0">{row.label}</span>
								<div class="flex-1 min-w-[120px] h-2 rounded-full bg-gray-800 overflow-hidden">
									<div
										class="h-full bg-emerald-600 rounded-full"
										style="width: {row.conversionPct}%"
									></div>
								</div>
								<span class="text-green-400 w-14">{row.conversionPct}%</span>
								<span class="text-gray-500 text-xs">
									{row.total} лид. · ✓{row.won} · ✗{row.lost} · …{row.active}
								</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			{#if metrics.funnelBySource?.length}
				<div
					class="max-w-3xl"
					data-testid="analytics-funnel-by-source"
					class:ring-1={activeView === 'source_funnel' || activeView === 'source'}
					class:ring-indigo-500={activeView === 'source_funnel' || activeView === 'source'}
					class:rounded-xl={activeView === 'source_funnel' || activeView === 'source'}
					class:p-2={activeView === 'source_funnel' || activeView === 'source'}
				>
					<h2 class="text-sm font-medium text-white mb-2">Воронка по источнику</h2>
					<p class="text-xs text-gray-500 mb-3">Сколько лидов на каждой стадии — отдельно по каналу</p>
					<div class="flex flex-wrap gap-2 mb-4">
						{#each metrics.funnelBySource as block}
							<button
								type="button"
								class="px-3 py-1 text-xs rounded-lg border transition-colors
									{selectedFunnelSource === block.source
									? 'bg-indigo-600 border-indigo-500 text-white'
									: 'border-gray-700 text-gray-400 hover:text-white'}"
								onclick={() => (selectedFunnelSource = block.source)}
							>
								{block.source}
								<span class="opacity-70 ml-1">({block.total})</span>
							</button>
						{/each}
					</div>
					{#if activeFunnelBlock}
						<div class="text-xs text-gray-500 mb-2">
							Конверсия: <span class="text-green-400">{activeFunnelBlock.conversionPct}%</span>
							· выиграно {activeFunnelBlock.wonCount} / проиграно {activeFunnelBlock.lostCount}
						</div>
						<div class="space-y-2">
							{#each activeFunnelBlock.funnel as item}
								<div class="flex items-center gap-3">
									<span class="text-xs text-gray-500 w-36 shrink-0">{item.stage}</span>
									<div class="flex-1 h-2 rounded-full bg-gray-800 overflow-hidden">
										<div
											class="h-full bg-violet-600 rounded-full transition-all"
											style="width: {item.pct}%"
										></div>
									</div>
									<span class="text-xs text-gray-400 w-12 text-right">{item.count}</span>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/if}

			{#if metrics.conversionBySource?.length}
				<div
					class="max-w-3xl"
					data-testid="analytics-conversion-by-source"
					class:ring-1={activeView === 'conversion'}
					class:ring-indigo-500={activeView === 'conversion'}
					class:rounded-xl={activeView === 'conversion'}
					class:p-2={activeView === 'conversion'}
				>
					<h2 class="text-sm font-medium text-white mb-3">Конверсия по источнику</h2>
					<div class="space-y-2">
						{#each metrics.conversionBySource as row}
							<div class="flex items-center gap-3 text-sm">
								<span class="text-gray-400 w-40 shrink-0 truncate" title={row.source}>{row.source}</span>
								<span class="text-gray-500 w-16">{row.total} лид.</span>
								<span class="text-green-400 w-20">{row.conversionPct}%</span>
								<span class="text-gray-600 text-xs">выиграно: {row.won}</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</div>
</div>
