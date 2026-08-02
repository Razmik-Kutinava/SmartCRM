<script>
	/**
	 * Общий суфлёр на карточке лида — чего не хватает до 🔍 / агентов.
	 */
	import { cardSufflerFromLead } from '$lib/leads/cardSuffler.js';

	let { lead = null, researchGaps = null } = $props();

	let suffler = $derived(
		Array.isArray(researchGaps) && researchGaps.length
			? { ok: false, gaps: researchGaps, missing_keys: [] }
			: cardSufflerFromLead(lead),
	);
</script>

{#if !suffler.ok && suffler.gaps?.length}
	<div
		class="mx-4 sm:mx-6 mb-2 rounded-xl border border-amber-800/60 bg-amber-950/35 px-3 py-2.5"
		data-testid="lead-card-suffler"
	>
		<div class="flex items-start justify-between gap-2">
			<div class="text-xs font-semibold text-amber-300">
				Суфлёр — чего не хватает для полного анализа
			</div>
			<span class="text-[10px] text-amber-700 shrink-0">{suffler.gaps.length}</span>
		</div>
		<ul class="mt-1.5 space-y-0.5 columns-1 sm:columns-2 gap-x-4">
			{#each suffler.gaps as gap}
				<li class="text-xs text-amber-100/90 break-inside-avoid">• {gap}</li>
			{/each}
		</ul>
		<p class="mt-1.5 text-[11px] text-amber-700/90">
			Заполни поля или нажми 🔍 Исследовать — сначала ИНН → Checko (ОКВЭД/фин) → сайт → веб.
		</p>
	</div>
{:else if suffler.ok}
	<div
		class="mx-4 sm:mx-6 mb-2 rounded-xl border border-emerald-900/50 bg-emerald-950/20 px-3 py-2"
		data-testid="lead-card-suffler-ok"
	>
		<div class="text-xs text-emerald-400/90">Суфлёр: ключевых пробелов нет — можно запускать агентов.</div>
	</div>
{/if}
