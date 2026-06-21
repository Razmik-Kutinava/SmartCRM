<script>
	/** @type {{ hints?: Array<{ severity: string, code: string, message: string }> }} */
	let { hints = [] } = $props();

	const styles = {
		critical: 'bg-rose-950/50 border-rose-700/80 text-rose-100',
		warn: 'bg-amber-950/40 border-amber-800/70 text-amber-100',
		info: 'bg-slate-900/60 border-slate-700/80 text-slate-200',
	};
</script>

{#if hints?.length}
	<div class="space-y-2" data-testid="lead-stage-hints">
		<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Что сделать</div>
		<ul class="space-y-1.5">
			{#each hints as h (h.code)}
				<li
					class="text-xs leading-snug rounded-lg border px-3 py-2 {styles[h.severity] || styles.info}"
					data-hint-severity={h.severity}
					data-hint-code={h.code}
				>
					{#if h.severity === 'critical'}<span class="mr-1">●</span>{:else if h.severity === 'warn'}<span class="mr-1">◆</span>{:else}<span class="mr-1 text-slate-500">○</span>{/if}
					{h.message}
				</li>
			{/each}
		</ul>
	</div>
{/if}
