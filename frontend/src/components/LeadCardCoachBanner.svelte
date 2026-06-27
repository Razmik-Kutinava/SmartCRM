<script>
	import { coachSeverityClass } from '$lib/leads/leadListCoach.js';

	/** @type {{ items?: Array<{ severity: string, code: string, text: string, panel?: string }>, onOpen?: (panel: string) => void }} */
	let { items = [], onOpen = () => {} } = $props();
</script>

{#if items?.length}
	<section
		class="mb-4 rounded-xl border border-amber-900/40 bg-amber-950/20 p-3 sm:p-4"
		data-testid="lead-card-coach-banner"
	>
		<div class="flex items-center justify-between gap-2 mb-2">
			<h2 class="text-xs font-semibold uppercase tracking-wide text-amber-200/90">
				Что сделать для полноты лида
			</h2>
			<span class="text-[10px] text-gray-500 tabular-nums">{items.length}</span>
		</div>
		<ul class="space-y-1.5">
			{#each items as item (item.code + item.text)}
				<li>
					<button
						type="button"
						class="w-full text-left text-xs leading-snug rounded-lg border px-3 py-2 transition-colors hover:brightness-110 {coachSeverityClass(item.severity)}"
						data-coach-code={item.code}
						data-coach-panel={item.panel || 'stages'}
						onclick={() => onOpen(item.panel || 'stages')}
					>
						{#if item.severity === 'critical'}
							<span class="mr-1">●</span>
						{:else if item.severity === 'warn'}
							<span class="mr-1">◆</span>
						{:else}
							<span class="mr-1 opacity-60">○</span>
						{/if}
						{item.text}
					</button>
				</li>
			{/each}
		</ul>
	</section>
{/if}
