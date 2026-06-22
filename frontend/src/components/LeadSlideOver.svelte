<script>
	/** Большая панель справа (~65% ширины), не маленький popup. */
	let {
		open = false,
		title = '',
		subtitle = '',
		onClose = () => {},
		children,
		testId = 'lead-slide-over',
	} = $props();

	function onBackdrop(e) {
		if (e.target === e.currentTarget) onClose();
	}

	function onKey(e) {
		if (e.key === 'Escape' && open) onClose();
	}
</script>

<svelte:window onkeydown={onKey} />

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-40 flex justify-end bg-black/60 backdrop-blur-[2px]"
		data-testid="{testId}-backdrop"
		onclick={onBackdrop}
		role="presentation"
	>
		<div
			class="h-full w-full sm:w-[92%] md:w-[80%] lg:w-[68%] xl:w-[62%] max-w-6xl bg-gray-950 border-l border-gray-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200"
			data-testid={testId}
			role="dialog"
			aria-modal="true"
			aria-label={title}
		>
			<header class="shrink-0 flex items-start justify-between gap-4 px-5 sm:px-6 py-4 border-b border-gray-800 bg-gray-900/90">
				<div class="min-w-0">
					<h2 class="text-lg font-semibold text-white truncate">{title}</h2>
					{#if subtitle}
						<p class="text-sm text-gray-500 mt-0.5 truncate">{subtitle}</p>
					{/if}
				</div>
				<button
					type="button"
					class="shrink-0 w-10 h-10 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 text-xl leading-none transition-colors"
					onclick={onClose}
					aria-label="Закрыть"
					data-testid="{testId}-close"
				>×</button>
			</header>
			<div class="flex-1 overflow-y-auto p-4 sm:p-6 min-h-0">
				{@render children?.()}
			</div>
		</div>
	</div>
{/if}
