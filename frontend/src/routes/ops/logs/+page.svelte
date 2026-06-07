<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	let items = $state([]);
	let loading = $state(true);
	let err = $state('');
	let level = $state('');
	let q = $state('');
	let limit = $state(200);
	let auto = $state(true);
	let clearing = $state(false);

	async function load() {
		try {
			const params = new URLSearchParams({ limit: String(limit) });
			if (level) params.set('level', level);
			if (q.trim()) params.set('q', q.trim());
			const r = await fetch(`${API}/api/ops/logs?${params}`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			items = d.items || [];
			err = '';
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			loading = false;
		}
	}

	async function clearLogs() {
		if (!confirm('Очистить буфер логов в памяти?')) return;
		clearing = true;
		try {
			const r = await fetch(`${API}/api/ops/logs`, { method: 'DELETE' });
			if (!r.ok) throw new Error(await r.text());
			await load();
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			clearing = false;
		}
	}

	onMount(() => {
		load();
		const id = setInterval(
			() => {
				if (auto) load();
			},
			4000
		);
		return () => clearInterval(id);
	});

	function lvlClass(l) {
		const u = (l || '').toUpperCase();
		if (u === 'ERROR') return 'text-red-400';
		if (u === 'WARNING') return 'text-amber-400';
		if (u === 'INFO') return 'text-sky-400';
		return 'text-gray-400';
	}
</script>

<div class="p-6 max-w-6xl mx-auto space-y-4">
	<div>
		<h2 class="text-lg font-semibold text-white">Логи системы</h2>
		<p class="text-sm text-gray-500 mt-1">
			HTTP-запросы и сообщения приложения (WARNING+) — буфер в памяти процесса, после перезапуска бэкенда очищается.
		</p>
	</div>

	<div class="flex flex-wrap items-end gap-3">
		<div>
			<label class="block text-xs text-gray-500 mb-1">Уровень</label>
			<select
				bind:value={level}
				class="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white"
			>
				<option value="">Все</option>
				<option value="INFO">INFO</option>
				<option value="WARNING">WARNING</option>
				<option value="ERROR">ERROR</option>
			</select>
		</div>
		<div class="flex-1 min-w-[10rem]">
			<label class="block text-xs text-gray-500 mb-1">Поиск</label>
			<input
				bind:value={q}
				placeholder="path, текст…"
				class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white"
			/>
		</div>
		<div>
			<label class="block text-xs text-gray-500 mb-1">Лимит</label>
			<input
				type="number"
				bind:value={limit}
				min="50"
				max="500"
				step="50"
				class="w-24 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white"
			/>
		</div>
		<label class="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
			<input type="checkbox" bind:checked={auto} class="accent-indigo-500" />
			Авто-обновление 4 с
		</label>
		<button
			type="button"
			onclick={load}
			class="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-500"
		>
			Обновить
		</button>
		<button
			type="button"
			onclick={clearLogs}
			disabled={clearing}
			class="px-4 py-2 rounded-lg bg-gray-800 text-gray-300 text-sm hover:bg-gray-700 disabled:opacity-50"
		>
			Очистить буфер
		</button>
	</div>

	{#if err}
		<div class="text-red-400 text-sm">{err}</div>
	{/if}

	{#if loading && items.length === 0}
		<p class="text-gray-500 text-sm">Загрузка…</p>
	{:else}
		<div class="rounded-xl border border-gray-800 overflow-hidden bg-gray-950/60">
			<div class="max-h-[min(70vh,800px)] overflow-auto">
				<table class="w-full text-xs font-mono">
					<thead class="bg-gray-900 sticky top-0 text-gray-500 text-left">
						<tr>
							<th class="px-3 py-2 whitespace-nowrap">Время (UTC)</th>
							<th class="px-3 py-2">Уровень</th>
							<th class="px-3 py-2">Сообщение</th>
							<th class="px-3 py-2 whitespace-nowrap">path</th>
							<th class="px-3 py-2 whitespace-nowrap">ms</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-800/80">
						{#each items as row}
							<tr class="hover:bg-gray-900/50 align-top">
								<td class="px-3 py-1.5 text-gray-500 whitespace-nowrap">{row.ts?.slice(11, 23) ?? '—'}</td>
								<td class="px-3 py-1.5 {lvlClass(row.level)}">{row.level}</td>
								<td class="px-3 py-1.5 text-gray-300 break-all">{row.message}</td>
								<td class="px-3 py-1.5 text-indigo-400/90">{row.path ?? '—'}</td>
								<td class="px-3 py-1.5 text-gray-500">{row.duration_ms ?? '—'}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			{#if items.length === 0}
				<p class="p-6 text-center text-gray-600 text-sm">Пока нет записей — сделайте несколько запросов к API.</p>
			{/if}
		</div>
	{/if}
</div>
