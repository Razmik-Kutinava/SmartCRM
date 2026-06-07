<script>
	import { onMount } from 'svelte';
	import { fetchLeads } from '$lib/leadsStorage.js';
	import { CRM_STAGES, loadCrmConfig } from '$lib/crmStages.js';

	let leads = $state([]);
	let loading = $state(true);
	let err = $state('');

	onMount(async () => {
		await loadCrmConfig();
		try {
			leads = await fetchLeads();
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			loading = false;
		}
	});

	const byStage = $derived.by(() => {
		const m = Object.fromEntries(CRM_STAGES.map((s) => [s, 0]));
		for (const l of leads) {
			const s = CRM_STAGES.includes(l.stage) ? l.stage : 'Новый';
			m[s] += 1;
		}
		return m;
	});

	const avgScore = $derived.by(() => {
		if (!leads.length) return 0;
		const sum = leads.reduce((a, l) => a + (Number(l.score) || 0), 0);
		return Math.round(sum / leads.length);
	});
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden">
	<div class="px-6 py-3 border-b border-gray-800 bg-gray-900 shrink-0">
		<h1 class="text-lg font-semibold text-white">Аналитика CRM</h1>
		<p class="text-xs text-gray-500">Сводка по лидам в локальной БД</p>
	</div>
	<div class="flex-1 overflow-y-auto p-6 space-y-6">
		{#if loading}
			<p class="text-gray-500">Загрузка…</p>
		{:else if err}
			<p class="text-red-400">{err}</p>
		{:else}
			<div class="grid sm:grid-cols-2 gap-4 max-w-3xl">
				<div class="rounded-xl border border-gray-800 bg-gray-900/80 p-4">
					<div class="text-xs text-gray-500 uppercase">Всего лидов</div>
					<div class="text-3xl font-bold text-white mt-1">{leads.length}</div>
				</div>
				<div class="rounded-xl border border-gray-800 bg-gray-900/80 p-4">
					<div class="text-xs text-gray-500 uppercase">Средний скоринг</div>
					<div class="text-3xl font-bold text-indigo-400 mt-1">{avgScore}</div>
				</div>
			</div>
			<div class="max-w-3xl">
				<h2 class="text-sm font-medium text-white mb-3">По этапам</h2>
				<div class="space-y-2">
					{#each CRM_STAGES as st}
						<div class="flex items-center gap-3">
							<span class="text-xs text-gray-500 w-36 shrink-0">{st}</span>
							<div class="flex-1 h-2 rounded-full bg-gray-800 overflow-hidden">
								<div
									class="h-full bg-indigo-600 rounded-full transition-all"
									style="width: {leads.length
										? (100 * byStage[st]) / leads.length
										: 0}%"
								></div>
							</div>
							<span class="text-xs text-gray-400 w-8 text-right">{byStage[st]}</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>
