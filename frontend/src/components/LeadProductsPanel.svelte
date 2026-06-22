<script>
	import {
		formatProductPrice,
		leadProductsFromLead,
		leadProductsSummary,
		PRODUCT_STATUS_LABELS,
		productsByStatus,
	} from '$lib/leads/leadProducts.js';

	let { lead = {} } = $props();

	const products = $derived(leadProductsFromLead(lead));
	const summary = $derived(leadProductsSummary(products));
	const sections = $derived([
		{ key: 'sold', title: PRODUCT_STATUS_LABELS.sold, items: productsByStatus(products, 'sold') },
		{ key: 'pipeline', title: PRODUCT_STATUS_LABELS.pipeline, items: productsByStatus(products, 'pipeline') },
		{ key: 'owned', title: PRODUCT_STATUS_LABELS.owned, items: productsByStatus(products, 'owned') },
	]);
</script>

<div class="space-y-4" data-testid="lead-products-panel">
	<div class="flex flex-wrap gap-2 text-xs" data-testid="lead-products-kpi">
		<span class="px-2 py-1 rounded-full bg-emerald-950/50 text-emerald-300 border border-emerald-900/40">
			Продано: {summary.sold}
		</span>
		<span class="px-2 py-1 rounded-full bg-amber-950/40 text-amber-300 border border-amber-900/40">
			В продаже: {summary.pipeline}
		</span>
		<span class="px-2 py-1 rounded-full bg-sky-950/40 text-sky-300 border border-sky-900/40">
			У клиента: {summary.owned}
		</span>
	</div>

	{#if !products.length}
		<p class="text-sm text-gray-500">
			Продукты подтянутся при импорте из Битрикс24 (UF, товарные позиции лида и сделок).
			Можно также указать вручную в карточке клиента → «Уже купили».
		</p>
	{:else}
		{#each sections as sec (sec.key)}
			{#if sec.items.length}
				<section data-testid="lead-products-section-{sec.key}">
					<h3 class="text-xs uppercase tracking-wider text-gray-500 mb-2">{sec.title}</h3>
					<ul class="space-y-2">
						{#each sec.items as item, i (sec.key + '-' + i)}
							<li
								class="rounded-lg border border-gray-800 bg-gray-900/60 px-3 py-2 flex flex-wrap justify-between gap-2"
								data-testid="lead-product-row"
							>
								<div class="min-w-0">
									<div class="text-sm text-gray-100 font-medium">{item.name}</div>
									{#if item.dealStage}
										<div class="text-[11px] text-gray-500 mt-0.5">Стадия: {item.dealStage}</div>
									{/if}
									{#if item.source}
										<div class="text-[10px] text-gray-600 mt-0.5">Источник: {item.source}</div>
									{/if}
								</div>
								<div class="text-right text-sm text-gray-300 shrink-0">
									{formatProductPrice(item.price, item.currency)}
									{#if item.quantity && Number(item.quantity) !== 1}
										<div class="text-[11px] text-gray-500">× {item.quantity}</div>
									{/if}
								</div>
							</li>
						{/each}
					</ul>
				</section>
			{/if}
		{/each}
	{/if}
</div>
