<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { fetchLeadActivities, fetchLeadManagers } from '$lib/leadsStorage.js';
	import { ACTIVITY_DUE_FILTERS, parseActivityDueFilter } from '$lib/leads/leadActivitiesList.js';

	let items = $state([]);
	let counts = $state({});
	let loading = $state(true);
	let err = $state('');
	let dueFilter = $state('scheduled');
	let filterManager = $state('all');
	let managerOptions = $state([]);

	const STAGE_COLORS = {
		Новый: 'bg-blue-900/50 text-blue-300',
		Квалифицирован: 'bg-indigo-900/50 text-indigo-300',
		Переговоры: 'bg-purple-900/50 text-purple-300',
		Выигран: 'bg-green-900/50 text-green-300',
		Проигран: 'bg-gray-700 text-gray-400',
	};

	function stageColor(stage) {
		return STAGE_COLORS[stage] || 'bg-gray-800 text-gray-300';
	}

	function chipCls(active) {
		return active
			? 'bg-indigo-600/30 border-indigo-500/80 text-indigo-200'
			: 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600 hover:text-gray-300';
	}

	async function load() {
		loading = true;
		err = '';
		try {
			const mgr = filterManager === 'all' ? null : filterManager;
			const data = await fetchLeadActivities({ due: dueFilter, manager: mgr });
			items = data.items || [];
			counts = data.counts || {};
		} catch (e) {
			err = e?.message || String(e);
			items = [];
		} finally {
			loading = false;
		}
	}

	function setDue(id) {
		dueFilter = id;
		load();
	}

	onMount(async () => {
		const qDue = $page.url.searchParams.get('due');
		if (qDue) dueFilter = parseActivityDueFilter(qDue);
		try {
			const mgr = await fetchLeadManagers();
			managerOptions = mgr.managers || [];
			if (mgr.defaultFilter && filterManager === 'all') {
				filterManager = mgr.defaultFilter;
			}
		} catch {
			managerOptions = [];
		}
		load();
	});

</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden" data-testid="leads-deals-page">
	<div class="shrink-0 px-4 sm:px-6 py-3 border-b border-gray-800 bg-gray-900">
		<div class="flex flex-wrap items-center gap-3">
			<h1 class="text-lg font-semibold text-white">Дела</h1>
			<span class="text-xs text-gray-500">умная очередь дня · как «Мой день»</span>
			<label class="ml-auto min-w-[10rem]">
				<span class="sr-only">Менеджер</span>
				<select
					bind:value={filterManager}
					onchange={() => load()}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-1.5"
					data-testid="leads-deals-manager"
				>
					<option value="all">Все менеджеры</option>
					{#each managerOptions as opt (opt.name)}
						<option value={opt.name}>{opt.name} ({opt.count})</option>
					{/each}
				</select>
			</label>
		</div>
		<div class="mt-3 flex flex-wrap gap-2" data-testid="leads-deals-due-filters">
			{#each ACTIVITY_DUE_FILTERS as [id, label]}
				<button
					type="button"
					class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] border transition-colors {chipCls(dueFilter === id)}"
					data-testid="leads-deals-filter-{id}"
					onclick={() => setDue(id)}
				>
					{label}
					<span class="font-semibold tabular-nums">{counts[id] ?? 0}</span>
				</button>
			{/each}
		</div>
	</div>

	<div class="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6">
		{#if err}
			<p class="text-red-400 text-sm mb-3">{err}</p>
		{/if}
		{#if loading}
			<p class="text-gray-500 text-sm">Загрузка…</p>
		{:else}
			<div class="overflow-x-auto rounded-xl border border-gray-800" data-testid="leads-deals-table">
				<table class="w-full text-sm">
					<thead class="bg-gray-900 text-left text-xs text-gray-500 sticky top-0 z-10">
						<tr>
							<th class="px-4 py-2.5 w-36">Срок дела</th>
							<th class="px-4 py-2.5">Дело</th>
							<th class="px-4 py-2.5">Лид</th>
							<th class="px-4 py-2.5">Стадия</th>
							<th class="px-4 py-2.5">Контакт</th>
							<th class="px-4 py-2.5">Менеджер</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-800">
						{#each items as row (row.leadId + '-' + row.taskId)}
							<tr class="hover:bg-gray-800/40 align-top">
								<td class="px-4 py-3 text-gray-300 whitespace-nowrap tabular-nums font-medium">
									{row.taskDue}
								</td>
								<td class="px-4 py-3 text-white max-w-xs">
									<div class="font-medium">{row.taskTitle}</div>
									{#if row.taskNote}
										<div class="text-xs text-gray-500 line-clamp-1 mt-0.5">{row.taskNote}</div>
									{/if}
								</td>
								<td class="px-4 py-3 max-w-[14rem]">
									<a
										href="/leads/{row.leadId}"
										class="font-medium text-white hover:text-indigo-400 transition-colors"
									>{row.company}</a>
									{#if row.source}
										<div class="text-[10px] text-gray-600 mt-0.5">{row.source}</div>
									{/if}
									{#if row.needsEnrich}
										<span class="text-[10px] text-fuchsia-400 mt-0.5 block">дозаполни карточку</span>
									{/if}
								</td>
								<td class="px-4 py-3">
									<span class="px-2 py-0.5 rounded-full text-xs font-medium {stageColor(row.stage)}">
										{row.stage || '—'}
									</span>
								</td>
								<td class="px-4 py-3 text-gray-400">
									<div>{row.contact}</div>
									{#if row.created}
										<div class="text-[10px] text-gray-600 mt-0.5">лид {row.created}</div>
									{/if}
								</td>
								<td class="px-4 py-3 text-gray-400 text-xs max-w-[9rem] truncate" title={row.managerName}>
									{row.managerName || '—'}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
				{#if items.length === 0}
					<p class="p-8 text-center text-gray-600 text-sm">
						Нет дел в этом сегменте. Попробуйте другой фильтр или дождитесь синка из Битрикса.
					</p>
				{/if}
			</div>
			{#if !loading && items.length > 0}
				<p class="text-xs text-gray-600 mt-3">{items.length} лидов с делами</p>
			{/if}
		{/if}
	</div>
</div>
