<script>
	import { onMount } from 'svelte';
	import { fetchLeads, apiUpdateLead } from '$lib/leadsStorage.js';
	import { CRM_STAGES, loadCrmConfig } from '$lib/crmStages.js';
	import {
		groupLeadsByStage,
		moveLeadStage,
		parseLeadDragId,
		setLeadDragData,
		stageColor,
	} from '$lib/leads/funnelDnD.js';

	let leads = $state([]);
	let loading = $state(true);
	let err = $state('');
	let moveErr = $state('');
	let draggingId = $state(null);
	let dropTarget = $state(/** @type {string | null} */ (null));
	let saving = $state(false);

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

	const byStage = $derived.by(() => groupLeadsByStage(leads, CRM_STAGES));

	function onDragStart(e, lead) {
		moveErr = '';
		draggingId = lead.id;
		setLeadDragData(e, lead.id);
	}

	function onDragEnd() {
		draggingId = null;
		dropTarget = null;
	}

	function onColumnDragOver(e, stage) {
		e.preventDefault();
		if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
		dropTarget = stage;
	}

	function onColumnDragLeave(stage) {
		if (dropTarget === stage) dropTarget = null;
	}

	async function onColumnDrop(e, targetStage) {
		e.preventDefault();
		dropTarget = null;
		draggingId = null;
		if (saving) return;

		const leadId = parseLeadDragId(e.dataTransfer);
		if (leadId == null) return;

		const lead = leads.find((l) => l.id === leadId);
		if (!lead || lead.stage === targetStage) return;

		const snapshot = leads;
		leads = moveLeadStage(leads, leadId, targetStage);
		saving = true;
		moveErr = '';
		try {
			const updated = await apiUpdateLead(leadId, { stage: targetStage });
			leads = moveLeadStage(leads, leadId, updated.stage ?? targetStage);
		} catch (ex) {
			leads = snapshot;
			moveErr = ex?.message || String(ex);
		} finally {
			saving = false;
		}
	}
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden">
	<div class="px-6 py-3 border-b border-gray-800 bg-gray-900 shrink-0">
		<h1 class="text-lg font-semibold text-white">Воронка</h1>
		<p class="text-xs text-gray-500">Перетащите карточку в другую колонку · клик открывает сделку</p>
		{#if moveErr}
			<p class="text-xs text-red-400 mt-1 whitespace-pre-line">{moveErr}</p>
		{/if}
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
						class="w-64 flex flex-col rounded-xl border bg-gray-900/95 {stageColor(stage)} border-t-2 shrink-0 transition-shadow {dropTarget === stage ? 'ring-2 ring-indigo-500/80' : ''}"
					>
						<div class="px-3 py-2 border-b border-gray-800 flex items-center justify-between">
							<span class="text-sm font-medium text-white">{stage}</span>
							<span class="text-xs text-gray-500">{byStage[stage]?.length ?? 0}</span>
						</div>
						<div
							class="flex-1 overflow-y-auto p-2 space-y-2 min-h-[120px]"
							ondragover={(e) => onColumnDragOver(e, stage)}
							ondragleave={() => onColumnDragLeave(stage)}
							ondrop={(e) => onColumnDrop(e, stage)}
							role="list"
							aria-label="Колонка {stage}"
						>
							{#each byStage[stage] || [] as lead (lead.id)}
								<div
									draggable="true"
									role="listitem"
									ondragstart={(e) => onDragStart(e, lead)}
									ondragend={onDragEnd}
									class="rounded-lg border border-gray-800 bg-gray-950/80 transition-colors cursor-grab active:cursor-grabbing {draggingId === lead.id ? 'opacity-40' : 'hover:border-indigo-700'}"
								>
									<a
										href="/leads/{lead.id}"
										draggable="false"
										class="block p-3"
									>
										<div class="font-medium text-white text-sm leading-snug">{lead.company}</div>
										<div class="text-xs text-gray-500 mt-1">{lead.contact}</div>
										<div class="flex items-center justify-between mt-2">
											<span class="text-xs text-green-400 font-semibold">{lead.score ?? '—'}</span>
											<span class="text-[10px] text-gray-600">{lead.budget || '—'}</span>
										</div>
									</a>
								</div>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
