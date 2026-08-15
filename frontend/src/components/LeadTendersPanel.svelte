<script>
	import {
		fetchLeadTenders,
		formatTendersUsage,
		leadTendersFromLead,
		searchLeadTenders,
	} from '$lib/leads/leadTenders.js';

	/** @type {{ lead?: Record<string, any>, onApplied?: (lead: Record<string, any>) => void }} */
	let { lead = {}, onApplied } = $props();

	let snap = $state(leadTendersFromLead(lead));
	let loading = $state(false);
	let error = $state('');

	async function loadCached() {
		if (!lead?.id) return;
		try {
			const body = await fetchLeadTenders(lead.id);
			snap = body;
		} catch (e) {
			error = e?.message || String(e);
		}
	}

	async function runSearch() {
		if (!lead?.id || loading) return;
		loading = true;
		error = '';
		try {
			const body = await searchLeadTenders(lead.id);
			snap = body;
			if (body?.lead && onApplied) onApplied(body.lead);
		} catch (e) {
			error = e?.message || String(e);
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		snap = leadTendersFromLead(lead) || snap;
	});
</script>

<div class="space-y-4" data-testid="lead-tenders-panel">
	<div class="flex flex-wrap items-center gap-2">
		<button
			type="button"
			class="px-3 py-1.5 text-xs rounded-lg bg-amber-800 text-white hover:bg-amber-700 disabled:opacity-50"
			onclick={runSearch}
			disabled={loading}
			data-testid="lead-tenders-search"
		>
			{loading ? 'Ищу…' : 'Искать тендеры'}
		</button>
		<button type="button" class="px-3 py-1.5 text-xs rounded-lg bg-gray-900 text-gray-400 hover:text-white" onclick={loadCached}>
			Кэш
		</button>
		{#if lead.inn}
			<span class="text-[11px] text-gray-500">ИНН {lead.inn}</span>
		{:else}
			<span class="text-[11px] text-amber-400">ИНН пуст — поиск по названию и вебу</span>
		{/if}
	</div>

	{#if error}
		<p class="text-xs text-red-400" data-testid="lead-tenders-error">{error}</p>
	{/if}

	<p class="text-[11px] text-gray-400" data-testid="lead-tenders-usage">
		{formatTendersUsage(snap?.usage?.providers, snap?.usage?.llm_tokens ?? 0)}
	</p>

	{#if snap?.summary}
		<div class="flex flex-wrap gap-2 text-xs" data-testid="lead-tenders-kpi">
			<span class="px-2 py-1 rounded-full border border-gray-800">Текущие: {snap.summary.current_count ?? 0}</span>
			<span class="px-2 py-1 rounded-full border border-gray-800">Прошлые: {snap.summary.past_count ?? 0}</span>
			<span class="px-2 py-1 rounded-full border border-gray-800">Веб: {snap.summary.web_count ?? 0}</span>
			{#if snap.summary.as_customer_total}
				<span class="px-2 py-1 rounded-full border border-emerald-900/40 text-emerald-300">Заказчик: {snap.summary.as_customer_total}</span>
			{/if}
		</div>
	{/if}

	{#each [
		{ key: 'current', title: 'Текущие / планы' },
		{ key: 'past', title: 'Прошлые контракты' },
		{ key: 'web', title: 'Поисковик (веб)' },
	] as sec}
		{@const rows = Array.isArray(snap?.[sec.key]) ? snap[sec.key] : []}
		<section data-testid="lead-tenders-section-{sec.key}">
			<h3 class="text-xs uppercase tracking-wider text-gray-500 mb-2">{sec.title}</h3>
			{#if !rows.length}
				<p class="text-sm text-gray-600">Пусто. Нажми «Искать тендеры».</p>
			{:else}
				<ul class="space-y-2">
					{#each rows as item, i (sec.key + '-' + (item.id || i))}
						<li class="rounded-lg border border-gray-800 bg-gray-900/60 px-3 py-2" data-testid="lead-tender-row">
							<div class="text-sm text-gray-100">{item.title || '—'}</div>
							<div class="text-[11px] text-gray-500 mt-0.5">
								{[item.source, item.role, item.date, item.customer].filter(Boolean).join(' · ')}
							</div>
							{#if item.url}
								<a class="text-[11px] text-blue-400 hover:underline" href={item.url} target="_blank" rel="noopener">открыть</a>
							{/if}
						</li>
					{/each}
				</ul>
			{/if}
		</section>
	{/each}
</div>
