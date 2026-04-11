<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	import { severityBadge, severityLabel } from '$lib/opsCommon.js';

	const API = getApiUrl();

	let data = $state({ items: [], open: [] });
	let loading = $state(true);
	let note = $state({});

	async function load() {
		try {
			const r = await fetch(`${API}/api/ops/queue`);
			data = await r.json();
		} catch (e) {
			console.error(e);
		} finally {
			loading = false;
		}
	}

	async function resolve(id, status) {
		const n = note[id] || '';
		await fetch(`${API}/api/ops/queue/${id}/resolve`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ status, note: n })
		});
		note[id] = '';
		await load();
	}

	async function recompute() {
		await fetch(`${API}/api/ops/recompute`, { method: 'POST' });
		await load();
	}

	function fmtTs(ts) {
		if (!ts) return '—';
		return new Date(ts * 1000).toLocaleString('ru-RU');
	}

	onMount(load);
</script>

<div class="px-6 py-6 max-w-4xl">
	<p class="text-sm text-gray-400 mb-4">
		Задачи с приоритетом: <strong class="text-red-300">критично</strong> — смотрите в первую очередь. Авто-задачи создаются эвристиками по
		трейсам; после действия отметьте «Готово» или «Отклонить».
	</p>

	<div class="mb-4">
		<button
			type="button"
			onclick={recompute}
			class="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white text-sm rounded-lg"
		>
			Обновить очередь из трейсов
		</button>
	</div>

	{#if loading}
		<p class="text-gray-500">Загрузка…</p>
	{:else if data.open.length === 0}
		<p class="text-gray-500 py-12">Открытых задач нет.</p>
	{:else}
		<div class="space-y-4">
			{#each data.open as item}
				<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
					<div class="flex flex-wrap items-start justify-between gap-3">
						<div>
							<span class="text-xs px-2 py-0.5 rounded {severityBadge(item.severity)}">{severityLabel(item.severity)}</span>
							<h3 class="text-white font-medium mt-2">{item.title}</h3>
							<p class="text-sm text-gray-400 mt-1">{item.detail}</p>
							<p class="text-xs text-gray-600 mt-2">{item.id} · {fmtTs(item.created_ts)}</p>
						</div>
						<div class="flex flex-col gap-2 w-full sm:w-64">
							<input
								type="text"
								placeholder="Комментарий (необязательно)"
								value={note[item.id] ?? ''}
								oninput={(e) => {
									note = { ...note, [item.id]: e.target.value };
								}}
								class="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-sm text-gray-100"
							/>
							<div class="flex gap-2">
								<button
									type="button"
									onclick={() => resolve(item.id, 'done')}
									class="flex-1 px-3 py-1.5 bg-emerald-800 hover:bg-emerald-700 text-white text-sm rounded-lg"
								>Готово</button>
								<button
									type="button"
									onclick={() => resolve(item.id, 'dismissed')}
									class="flex-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm rounded-lg"
								>Отклонить</button>
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}

	{#if !loading && (data.items || []).some((x) => x.status === 'done' || x.status === 'dismissed')}
		<details class="mt-10 border-t border-gray-800 pt-6">
			<summary class="text-sm text-gray-500 cursor-pointer">Завершённые записи</summary>
			<ul class="mt-3 space-y-2 text-xs text-gray-500">
				{#each data.items.filter((x) => x.status === 'done' || x.status === 'dismissed') as item}
					<li>
						{item.title} — {item.status}
						{#if item.resolve_note}
							({item.resolve_note}){/if}
					</li>
				{/each}
			</ul>
		</details>
	{/if}
</div>
