<script>
	let {
		icon = '📋',
		title = '',
		preview = '',
		meta = '',
		accent = 'indigo',
		alert = false,
		onclick = () => {},
		testId = 'lead-hub-tile',
	} = $props();

	const accents = {
		indigo: 'border-indigo-800/60 hover:border-indigo-500/70 bg-indigo-950/20 hover:bg-indigo-950/35 shadow-indigo-950/30',
		emerald: 'border-emerald-800/50 hover:border-emerald-500/60 bg-emerald-950/15 hover:bg-emerald-950/30 shadow-emerald-950/25',
		violet: 'border-violet-800/50 hover:border-violet-500/60 bg-violet-950/15 hover:bg-violet-950/30 shadow-violet-950/25',
		sky: 'border-sky-800/50 hover:border-sky-500/60 bg-sky-950/15 hover:bg-sky-950/30 shadow-sky-950/20',
		amber: 'border-amber-800/50 hover:border-amber-500/60 bg-amber-950/15 hover:bg-amber-950/30 shadow-amber-950/20',
		rose: 'border-rose-800/50 hover:border-rose-500/60 bg-rose-950/15 hover:bg-rose-950/30 shadow-rose-950/20',
	};
	const accentClass = $derived(accents[accent] || accents.indigo);
</script>

<button
	type="button"
	class="group text-left rounded-2xl border p-4 sm:p-5 min-h-[7.5rem] sm:min-h-[8.5rem] flex flex-col justify-between transition-all duration-200 shadow-lg hover:scale-[1.02] active:scale-[0.99] {accentClass}"
	data-testid={testId}
	onclick={onclick}
>
	<div class="flex items-start justify-between gap-2">
		<span class="text-2xl sm:text-3xl" aria-hidden="true">{icon}</span>
		<div class="flex items-center gap-1.5 shrink-0">
			{#if alert}
				<span
					class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800/80"
					data-testid="{testId}-alert"
					title="Требует внимания"
				>!</span>
			{/if}
			<span class="text-[10px] uppercase tracking-wider text-gray-500 group-hover:text-gray-400">Открыть →</span>
		</div>
	</div>
	<div class="mt-3 min-w-0">
		<div class="text-sm sm:text-base font-semibold text-white leading-snug">{title}</div>
		{#if preview}
			<p class="text-xs sm:text-sm text-gray-400 mt-1.5 line-clamp-2 leading-relaxed">{preview}</p>
		{/if}
		{#if meta}
			<p class="text-[11px] text-gray-500 mt-2 font-medium">{meta}</p>
		{/if}
	</div>
</button>
