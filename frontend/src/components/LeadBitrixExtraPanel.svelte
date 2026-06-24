<script>
	import { licenseDisplayRows, rawBitrixUfEntries } from '$lib/leads/leadBitrixExtra.js';

	/** @type {{ lead: Record<string, unknown> | null | undefined }} */
	let { lead } = $props();

	let ufOpen = $state(false);

	const licenseRows = $derived(licenseDisplayRows(lead));
	const ufRows = $derived(rawBitrixUfEntries(lead));
</script>

{#if licenseRows.length > 0}
	<section class="space-y-2" data-testid="lead-bitrix-license-panel">
		<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Лицензия / подписка</div>
		<dl class="rounded-lg border border-gray-800 bg-gray-950/50 divide-y divide-gray-800/80 text-sm">
			{#each licenseRows as row (row.key)}
				<div class="flex gap-3 px-3 py-2">
					<dt class="text-gray-500 text-xs shrink-0 w-[38%] sm:w-[34%]">{row.label}</dt>
					<dd class="text-gray-200 text-sm break-words min-w-0">{row.value}</dd>
				</div>
			{/each}
		</dl>
	</section>
{/if}

{#if ufRows.length > 0}
	<section class="space-y-2" data-testid="lead-bitrix-uf-panel">
		<button
			type="button"
			class="flex w-full items-center justify-between gap-2 text-left text-xs text-gray-500 uppercase tracking-wide font-medium hover:text-gray-300"
			onclick={() => { ufOpen = !ufOpen; }}
			aria-expanded={ufOpen}
		>
			<span>Поля Битрикс (сырые UF)</span>
			<span class="text-[10px] normal-case text-gray-600">{ufRows.length} · {ufOpen ? '▲' : '▼'}</span>
		</button>
		{#if ufOpen}
			<dl class="rounded-lg border border-gray-800 bg-gray-950/30 divide-y divide-gray-800/60 text-xs font-mono max-h-64 overflow-y-auto">
				{#each ufRows as row (row.key)}
					<div class="px-3 py-2">
						<div class="text-violet-300/80 break-all">{row.key}</div>
						<div class="text-gray-400 mt-0.5 break-words whitespace-pre-wrap">{row.value}</div>
					</div>
				{/each}
			</dl>
		{/if}
	</section>
{/if}
