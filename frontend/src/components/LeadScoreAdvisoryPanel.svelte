<script>
	import { formatScoreBreakdownLines } from '$lib/leads/scoreBreakdown.js';

	/** @type {{ scoreAdvisory?: Record<string, unknown> | null }} */
	let { scoreAdvisory = null } = $props();

	const disabled = $derived(Boolean(scoreAdvisory?.disabled));
	const suggested = $derived(scoreAdvisory?.suggestedScore);
	const bdLines = $derived(
		scoreAdvisory?.breakdown ? formatScoreBreakdownLines(scoreAdvisory.breakdown) : []
	);
	const warnings = $derived(
		Array.isArray(scoreAdvisory?.warnings) ? scoreAdvisory.warnings.filter(Boolean) : []
	);
</script>

{#if !disabled && suggested != null}
	<details class="text-xs border border-gray-800 rounded-lg bg-gray-950/50" data-testid="lead-score-advisory-panel">
		<summary class="cursor-pointer px-2.5 py-2 text-gray-500 hover:text-gray-300 select-none">
			Подсказка скоринга (система): <span class="text-amber-400/90 tabular-nums">{suggested}/100</span>
		</summary>
		<div class="px-2.5 pb-2.5 space-y-2 border-t border-gray-800">
			<p class="text-[10px] text-gray-600 pt-2 leading-snug">
				Не меняет балл менеджера в шапке — только справка для РОП.
			</p>
			{#if warnings.length}
				<ul class="space-y-1">
					{#each warnings as w}
						<li class="text-amber-200/80 text-[11px]">⚠ {w}</li>
					{/each}
				</ul>
			{/if}
			{#if bdLines.length}
				<ul class="space-y-0.5" data-testid="lead-score-breakdown">
					{#each bdLines as line}
						<li class="flex justify-between gap-2 text-gray-400">
							<span>{line.label}</span>
							<span class="text-gray-200 font-mono tabular-nums">{line.value}</span>
						</li>
					{/each}
				</ul>
			{/if}
		</div>
	</details>
{/if}
