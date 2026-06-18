<script>
	import { onMount } from 'svelte';
	import {
		fetchTenderNotifications,
		markTenderNotificationsRead,
		scanTenderDeadlines
	} from '$lib/tenders/tenderCalendarOps.js';

	let data = $state({ items: [], unread: 0 });
	let loading = $state(true);
	let err = $state('');
	let scanning = $state(false);

	async function reload() {
		loading = true;
		err = '';
		try {
			data = await fetchTenderNotifications(false);
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			loading = false;
		}
	}

	onMount(() => reload());

	async function markRead(id) {
		await markTenderNotificationsRead({ notificationId: id });
		await reload();
	}

	async function markAll() {
		await markTenderNotificationsRead({ all: true });
		await reload();
	}

	async function doScan() {
		scanning = true;
		try {
			await scanTenderDeadlines();
			await reload();
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			scanning = false;
		}
	}

	function kindLabel(k) {
		if (k === 'tender_new') return 'Новый';
		if (k?.startsWith('deadline')) return 'Дедлайн';
		return k || '';
	}
</script>

<div class="max-w-2xl mx-auto p-6 space-y-4 text-white">
	<div class="flex justify-between items-start gap-4">
		<div>
			<h1 class="text-xl font-bold">Уведомления по тендерам</h1>
			<p class="text-sm text-gray-500">Новые закупки и напоминания о дедлайнах</p>
		</div>
		<div class="flex gap-2 text-sm">
			<a href="/tenders" class="text-blue-400 hover:underline">Тендеры</a>
			<a href="/tenders/calendar" class="text-blue-400 hover:underline">Календарь</a>
		</div>
	</div>

	{#if err}<p class="text-red-400 text-sm">{err}</p>{/if}

	<div class="flex gap-2">
		<button
			type="button"
			class="text-sm border border-gray-700 px-3 py-1 rounded disabled:opacity-50"
			disabled={!data.unread}
			onclick={markAll}>Прочитать все ({data.unread})</button
		>
		<button
			type="button"
			class="text-sm border border-gray-700 px-3 py-1 rounded disabled:opacity-50"
			disabled={scanning}
			onclick={doScan}>{scanning ? '…' : 'Проверить дедлайны'}</button
		>
	</div>

	{#if loading}
		<p class="text-gray-500">Загрузка…</p>
	{:else if !data.items?.length}
		<p class="text-gray-500 text-sm">Пока пусто. Включите мониторинг в Ops → Тендеры 24/7.</p>
	{:else}
		<ul class="space-y-2">
			{#each data.items as n}
				<li
					class="border rounded-lg p-3 {n.read
						? 'border-gray-800 bg-gray-900/50 opacity-70'
						: 'border-blue-900/50 bg-gray-900'}"
				>
					<div class="flex justify-between gap-2">
						<span class="text-[10px] uppercase text-gray-500">{kindLabel(n.kind)}</span>
						{#if !n.read}
							<button
								type="button"
								class="text-[10px] text-blue-400"
								onclick={() => markRead(n.id)}>прочитано</button
							>
						{/if}
					</div>
					<div class="font-medium text-sm mt-1">{n.title}</div>
					<p class="text-xs text-gray-400 mt-1">{n.detail}</p>
					{#if n.tender?.url && n.tender.url !== '#'}
						<a href={n.tender.url} class="text-xs text-blue-400 mt-1 inline-block">Открыть →</a
						>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}
</div>
