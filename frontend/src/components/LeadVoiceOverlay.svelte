<script>
	/** Модалка лида поверх всего (голос «открой её»): blur + iframe embed карточки. */
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { voiceLeadOverlay, closeVoiceLeadOverlay } from '$lib/voice/voiceLeadFocus.js';
	import { fetchLeadById } from '$lib/leadsStorage.js';

	let overlay = $state(/** @type {{ id: number, company: string } | null} */ (null));
	let title = $state('');
	let loading = $state(false);

	$effect(() => {
		const unsub = voiceLeadOverlay.subscribe((v) => {
			overlay = v;
			if (v?.id) {
				title = v.company || `Лид #${v.id}`;
				loading = true;
				fetchLeadById(v.id)
					.then((lead) => {
						if (get(voiceLeadOverlay)?.id === v.id) {
							title = String(lead?.company || title);
						}
					})
					.catch(() => {})
					.finally(() => {
						loading = false;
					});
			} else {
				title = '';
			}
		});
		return unsub;
	});

	function onBackdrop(e) {
		if (e.target === e.currentTarget) closeVoiceLeadOverlay();
	}

	function onKey(e) {
		if (e.key === 'Escape' && overlay) closeVoiceLeadOverlay();
	}

	function openFull() {
		const id = overlay?.id;
		closeVoiceLeadOverlay();
		if (id) goto(`/leads/${id}`);
	}
</script>

<svelte:window onkeydown={onKey} />

{#if overlay}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[60] flex items-stretch justify-center sm:justify-end bg-black/70 backdrop-blur-md"
		data-testid="lead-voice-overlay-backdrop"
		onclick={onBackdrop}
		role="presentation"
	>
		<div
			class="h-full w-full sm:w-[94%] md:w-[85%] lg:w-[72%] xl:w-[65%] max-w-6xl bg-gray-950 border-l border-gray-700 shadow-2xl flex flex-col"
			data-testid="lead-voice-overlay"
			role="dialog"
			aria-modal="true"
			aria-label={title || 'Лид'}
		>
			<header class="shrink-0 flex items-center justify-between gap-3 px-4 sm:px-5 py-3 border-b border-gray-800 bg-gray-900/95">
				<div class="min-w-0">
					<p class="text-[10px] uppercase tracking-wider text-indigo-300/80">Голос · карточка</p>
					<h2 class="text-base sm:text-lg font-semibold text-white truncate">
						{title || `Лид #${overlay.id}`}
						{#if loading}<span class="text-xs text-gray-500 font-normal ml-2">загрузка…</span>{/if}
					</h2>
				</div>
				<div class="flex items-center gap-2 shrink-0">
					<button
						type="button"
						class="px-3 py-1.5 rounded-lg text-xs bg-indigo-700 hover:bg-indigo-600 text-white"
						onclick={openFull}
						data-testid="lead-voice-overlay-full"
					>На весь экран</button>
					<button
						type="button"
						class="w-9 h-9 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 text-xl leading-none"
						onclick={closeVoiceLeadOverlay}
						aria-label="Закрыть"
						data-testid="lead-voice-overlay-close"
					>×</button>
				</div>
			</header>
			<div class="flex-1 min-h-0 bg-gray-950">
				<iframe
					title={title || `Лид ${overlay.id}`}
					src={`/leads/${overlay.id}?embed=1`}
					class="w-full h-full border-0"
					data-testid="lead-voice-overlay-frame"
				></iframe>
			</div>
		</div>
	</div>
{/if}
