<script>
	import EmailNurturePanel from './EmailNurturePanel.svelte';
	import {
		MAILING_TYPE_NURTURE,
		enabledMailingTypes,
		emailPanelDeepLink,
	} from '$lib/leads/leadMailingTypes.js';

	let { open = $bindable(false), lead = null, accounts = [] } = $props();

	let selectedType = $state(null);
	let error = $state('');
	let success = $state('');

	const types = $derived(lead ? enabledMailingTypes(lead) : []);

	function close() {
		open = false;
		selectedType = null;
		error = '';
		success = '';
	}

	function pickType(id) {
		selectedType = id;
		error = '';
		success = '';
	}

	$effect(() => {
		if (!open) {
			selectedType = null;
			return;
		}
		if (types.length === 1) selectedType = types[0].id;
	});
</script>

{#if open && lead}
	<div
		class="fixed inset-0 z-50 flex items-stretch justify-end bg-black/60"
		role="dialog"
		aria-modal="true"
		aria-labelledby="lead-mailing-title"
		data-testid="lead-mailing-drawer"
	>
		<button type="button" class="flex-1 cursor-default" aria-label="Закрыть" onclick={close}></button>
		<div class="w-full max-w-2xl bg-gray-950 border-l border-gray-800 flex flex-col shadow-2xl">
			<header class="flex items-center justify-between px-5 py-4 border-b border-gray-800 shrink-0">
				<div>
					<h2 id="lead-mailing-title" class="text-sm font-semibold text-white">Рассылка · {lead.company}</h2>
					<p class="text-xs text-gray-500 mt-0.5">Точечные касания с карточки лида</p>
				</div>
				<button
					type="button"
					class="text-gray-400 hover:text-white text-xl leading-none px-2"
					onclick={close}
					data-testid="lead-mailing-close"
				>×</button>
			</header>

			{#if error}
				<div class="mx-5 mt-3 px-4 py-2 rounded-xl bg-red-950 border border-red-800 text-red-200 text-sm">{error}</div>
			{/if}
			{#if success}
				<div class="mx-5 mt-3 px-4 py-2 rounded-xl bg-green-950 border border-green-800 text-green-200 text-sm">{success}</div>
			{/if}

			<div class="flex-1 min-h-0 overflow-hidden flex flex-col">
				{#if types.length === 0}
					<p class="p-5 text-sm text-gray-500">Нет доступных типов рассылки для этого лида.</p>
				{:else if !selectedType}
					<div class="p-5 space-y-2">
						<p class="text-xs text-gray-500 uppercase tracking-wide mb-3">Выбери тип</p>
						{#each types as t (t.id)}
							<button
								type="button"
								class="w-full flex items-start gap-3 rounded-xl border border-gray-800 bg-gray-900 hover:bg-gray-800 px-4 py-3 text-left transition-colors"
								onclick={() => pickType(t.id)}
								data-testid="lead-mailing-type-{t.id}"
							>
								<span class="text-lg">{t.icon}</span>
								<span>
									<span class="block text-sm font-medium text-white">{t.label}</span>
									<span class="block text-xs text-gray-500 mt-0.5">{t.description}</span>
								</span>
							</button>
						{/each}
					</div>
				{:else if selectedType === MAILING_TYPE_NURTURE}
					<div class="flex-1 min-h-0 flex flex-col">
						{#if types.length > 1}
							<button
								type="button"
								class="mx-5 mt-3 text-xs text-indigo-400 hover:text-indigo-300 text-left"
								onclick={() => { selectedType = null; }}
							>← Другой тип рассылки</button>
						{/if}
						<EmailNurturePanel
							{accounts}
							leads={[lead]}
							initialLeadId={lead.id}
							lockLead
							compact
							bind:error
							bind:success
						/>
					</div>
				{/if}
			</div>

			<footer class="px-5 py-3 border-t border-gray-800 shrink-0">
				<a
					href={emailPanelDeepLink(lead.id)}
					class="text-xs text-indigo-400 hover:text-indigo-300"
					data-testid="lead-mailing-open-email"
				>Открыть в полной панели /email →</a>
			</footer>
		</div>
	</div>
{/if}
