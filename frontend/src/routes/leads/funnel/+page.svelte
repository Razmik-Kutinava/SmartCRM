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
		const m = Object.fromEntries(CRM_STAGES.map((s) => [s, []]));
		for (const l of leads) {
			let s = l.stage;
			if (!m[s]) s = 'Новый';
			m[s].push(l);
		}
		return m;
	});

	function stageColor(stage) {
		const map = {
			Новый: 'border-gray-700',
			Квалифицирован: 'border-blue-800',
			'КП отправлено': 'border-yellow-800',
			Переговоры: 'border-indigo-800',
			Выигран: 'border-green-800',
			Проигран: 'border-red-900',
		};
		return map[stage] || 'border-gray-700';
	}
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden">
	<div class="px-6 py-3 border-b border-gray-800 bg-gray-900 shrink-0">
		<h1 class="text-lg font-semibold text-white">Воронка</h1>
		<p class="text-xs text-gray-500">Карточки по этапам · клик открывает сделку</p>
	</div>

	{#if loading}
		<div class="flex-1 flex items-center justify-center text-gray-500 text-sm">Загрузка…</div>
	{:else if err}
		<div class="p-6 text-red-400 text-sm">{err}</div>
	{:else}
		<div class="flex-1 overflow-x-auto overflow-y-hidden p-4">
			<div class="flex gap-3 h-full min-w-max pb-2">
				{#each CRM_STAGES as stage}
					<div
						class="w-64 flex flex-col rounded-xl border bg-gray-900/95 {stageColor(stage)} border-t-2 shrink-0"
					>
						<div class="px-3 py-2 border-b border-gray-800 flex items-center justify-between">
							<span class="text-sm font-medium text-white">{stage}</span>
							<span class="text-xs text-gray-500">{byStage[stage]?.length ?? 0}</span>
						</div>
						<div class="flex-1 overflow-y-auto p-2 space-y-2 min-h-[120px]">
							{#each byStage[stage] || [] as lead}
								<a
									href="/leads/{lead.id}"
									class="block rounded-lg border border-gray-800 bg-gray-950/80 p-3 hover:border-indigo-700 transition-colors"
								>
									<div class="font-medium text-white text-sm leading-snug">{lead.company}</div>
									<div class="text-xs text-gray-500 mt-1">{lead.contact}</div>
									<div class="flex items-center justify-between mt-2">
										<span class="text-xs text-green-400 font-semibold">{lead.score ?? '—'}</span>
										<span class="text-[10px] text-gray-600">{lead.budget || '—'}</span>
									</div>
								</a>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
