<script>
	import { onMount } from 'svelte';
	import { fetchNurtureChains, relinkOrphanEmails } from '$lib/emailStorage.js';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();
	let chains = $state([]);
	let loading = $state(true);
	let err = $state('');
	let msg = $state('');
	let relinkBusy = $state(false);

	async function load() {
		loading = true;
		err = '';
		try {
			chains = await fetchNurtureChains();
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			loading = false;
		}
	}

	async function doRelink() {
		relinkBusy = true;
		msg = '';
		try {
			const r = await relinkOrphanEmails();
			msg = `Привязано тредов: ${r.threads_linked ?? 0}`;
			await load();
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			relinkBusy = false;
		}
	}

	onMount(load);
</script>

<div class="px-6 py-8 max-w-4xl">
	<h2 class="text-lg font-semibold text-white mb-2">Email · Ф3 автономия</h2>
	<p class="text-sm text-gray-400 mb-6">
		Цепочки 20 касаний, автолинк по домену. FAQ-правила — в
		<a href="/ops/email-agents" class="text-indigo-400 hover:underline">Агентах почты</a>.
	</p>

	{#if err}<div class="mb-4 rounded border border-red-900/50 bg-red-950/40 px-4 py-2 text-sm text-red-200">{err}</div>{/if}
	{#if msg}<div class="mb-4 rounded border border-emerald-900/50 bg-emerald-950/30 px-4 py-2 text-sm text-emerald-200">{msg}</div>{/if}

	<div class="mb-8 rounded-xl border border-gray-800 bg-gray-900/50 p-5">
		<h3 class="text-sm font-medium text-white mb-2">Автолинк письмо → лид</h3>
		<p class="text-xs text-gray-500 mb-3">Перепривязка сиротских тредов по домену email / website лида.</p>
		<button
			type="button"
			data-testid="email-relink-orphans"
			onclick={doRelink}
			disabled={relinkBusy}
			class="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500 disabled:opacity-50"
		>
			{relinkBusy ? '…' : 'Relink сирот'}
		</button>
	</div>

	<div class="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
		<h3 class="text-sm font-medium text-white mb-3">Цепочки nurture</h3>
		{#if loading}
			<p class="text-sm text-gray-500">Загрузка…</p>
		{:else if !chains.length}
			<p class="text-sm text-gray-500" data-testid="nurture-empty">Нет цепочек. Старт с карточки лида или API POST /api/email/nurture/start</p>
		{:else}
			<table class="w-full text-left text-xs text-gray-300" data-testid="nurture-chains-table">
				<thead class="text-gray-500 uppercase">
					<tr>
						<th class="pb-2">ID</th>
						<th class="pb-2">Лид</th>
						<th class="pb-2">Статус</th>
						<th class="pb-2">Шаги</th>
					</tr>
				</thead>
				<tbody>
					{#each chains as c}
						<tr class="border-t border-gray-800">
							<td class="py-2">{c.id}</td>
							<td class="py-2"><a href="/leads/{c.leadId}" class="text-indigo-400">{c.leadId}</a></td>
							<td class="py-2">{c.status}</td>
							<td class="py-2">{c.stepsSent}/{c.stepsTotal}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}
	</div>
</div>
