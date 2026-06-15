<script>
	import {
		leadIndustryLead,
		leadIndustryOpen,
		closeLeadIndustryModal,
		notifyLeadIndustrySaved,
	} from '$lib/leads/leadIndustryUi.js';
	import { fetchLeadIndustries, saveLeadIndustry, isIndustryEmpty } from '$lib/leads/industryCatalog.js';

	let industry = $state('');
	let verified = $state(true);
	let options = $state([]);
	let busy = $state(false);
	let error = $state('');

	const lead = $derived($leadIndustryLead);
	const open = $derived($leadIndustryOpen);

	$effect(() => {
		if (!open || !lead) return;
		industry = isIndustryEmpty(lead.industry) ? '' : String(lead.industry).trim();
		verified = lead.industryVerified !== false;
		error = '';
		fetchLeadIndustries().then((rows) => { options = rows; }).catch(() => { options = []; });
	});

	async function onSave() {
		if (!lead?.id) return;
		busy = true;
		error = '';
		try {
			const updated = await saveLeadIndustry(lead.id, { industry, industryVerified: verified });
			notifyLeadIndustrySaved(updated);
			closeLeadIndustryModal();
		} catch (e) {
			error = e?.message || String(e);
		} finally {
			busy = false;
		}
	}
</script>

{#if open && lead}
	<div class="fixed inset-0 z-[110] flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true" data-testid="lead-industry-modal">
		<div class="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-950 p-5 shadow-2xl">
			<h2 class="text-sm font-semibold text-white mb-1">Указать отрасль</h2>
			<p class="text-xs text-gray-500 mb-4">{lead.company} — нужна отрасль для рассылки и сегментов</p>
			{#if error}<p class="text-xs text-red-300 mb-2">{error}</p>{/if}
			<label class="block text-xs text-gray-500 mb-1">Отрасль</label>
			<input
				list="lead-industry-options"
				bind:value={industry}
				class="w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm text-white mb-3"
				placeholder="Выбери или введи…"
				data-testid="lead-industry-input"
			/>
			<datalist id="lead-industry-options">
				{#each options as opt (opt)}<option value={opt}></option>{/each}
			</datalist>
			<label class="flex items-center gap-2 text-sm text-gray-300 mb-4">
				<input type="checkbox" bind:checked={verified} class="accent-indigo-500" data-testid="lead-industry-verified" />
				Отрасль проверена оператором
			</label>
			<div class="flex justify-end gap-2">
				<button type="button" class="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300" onclick={closeLeadIndustryModal}>Отмена</button>
				<button type="button" class="px-3 py-1.5 text-sm rounded-lg bg-indigo-600 text-white disabled:opacity-50" disabled={busy || !industry.trim()} onclick={onSave} data-testid="lead-industry-save">Сохранить</button>
			</div>
		</div>
	</div>
{/if}
