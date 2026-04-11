<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	let hist = $state(null);
	let loading = $state(true);
	let snapshotting = $state(false);
	let err = $state('');

	async function load() {
		loading = true;
		try {
			const r = await fetch(`${API}/api/ops/history`);
			if (!r.ok) throw new Error(await r.text());
			hist = await r.json();
			err = '';
		} catch (e) {
			err = String(e?.message || e);
		} finally {
			loading = false;
		}
	}

	async function takeSnapshot() {
		snapshotting = true;
		try {
			await fetch(`${API}/api/ops/snapshot`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ label: '' })
			});
			await load();
		} finally {
			snapshotting = false;
		}
	}

	async function setBaseline(id) {
		await fetch(`${API}/api/ops/baseline`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ snapshot_id: id })
		});
		await load();
	}

	function fmtTs(ts) {
		if (!ts) return '—';
		return new Date(ts * 1000).toLocaleString('ru-RU');
	}

	function fmtPct(v) {
		if (v === null || v === undefined) return '—';
		const sign = v > 0 ? '+' : '';
		return `${sign}${v}%`;
	}

	onMount(load);
</script>

<div class="px-6 py-6 max-w-4xl">
	<p class="text-sm text-gray-400 mb-4">
		Снимки фиксируют агрегаты трейсов в момент времени. «База» — с чем сравниваем текущие значения в буфере (проценты — относительно
		базы и предыдущего снимка).
	</p>

	<div class="flex flex-wrap gap-3 mb-8">
		<button
			type="button"
			onclick={takeSnapshot}
			disabled={snapshotting}
			class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg disabled:opacity-50"
		>
			{snapshotting ? 'Сохраняем…' : 'Новый снимок'}
		</button>
		<button type="button" onclick={load} class="px-4 py-2 border border-gray-700 text-gray-300 text-sm rounded-lg hover:bg-gray-800">
			Обновить
		</button>
	</div>

	{#if loading}
		<p class="text-gray-500">Загрузка…</p>
	{:else if err}
		<p class="text-red-400">{err}</p>
	{:else if hist}
		<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-8">
			<p class="text-sm text-gray-300">
				Базовая линия: <strong class="text-white">{hist.baseline_set ? 'задана' : 'не задана'}</strong>
				{#if hist.baseline_ts}
					· {fmtTs(hist.baseline_ts)}
				{/if}
			</p>
			<p class="text-xs text-gray-500 mt-1">Снимков в БД: {hist.snapshots_count}</p>
		</div>

		<h2 class="text-sm font-medium text-gray-300 mb-3">Сравнение с базой и с прошлым снимком</h2>
		<div class="overflow-x-auto mb-10">
			<table class="w-full text-sm border border-gray-800 rounded-xl overflow-hidden">
				<thead class="bg-gray-800 text-gray-400 text-xs">
					<tr>
						<th class="px-3 py-2 text-left">Метрика</th>
						<th class="px-3 py-2 text-right">Сейчас (live)</th>
						<th class="px-3 py-2 text-right">К базе</th>
						<th class="px-3 py-2 text-right">К прошлому снимку</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-800 bg-gray-900/50">
					{#each hist.metrics as m}
						<tr>
							<td class="px-3 py-2 text-gray-300">{m.label}</td>
							<td class="px-3 py-2 text-right text-white font-mono">{m.live}</td>
							<td class="px-3 py-2 text-right font-mono {m.vs_baseline_pct > 0 ? 'text-emerald-400' : m.vs_baseline_pct < 0 ? 'text-red-400' : 'text-gray-400'}">
								{fmtPct(m.vs_baseline_pct)}
							</td>
							<td class="px-3 py-2 text-right font-mono {m.vs_previous_snapshot_pct > 0 ? 'text-emerald-400' : m.vs_previous_snapshot_pct < 0 ? 'text-red-400' : 'text-gray-400'}">
								{fmtPct(m.vs_previous_snapshot_pct)}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<h2 class="text-sm font-medium text-gray-300 mb-3">Последние снимки</h2>
		<div class="space-y-2">
			{#each [...(hist.snapshots || [])].reverse() as s}
				<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm">
					<div class="flex flex-wrap items-start justify-between gap-2">
						<div class="flex-1 min-w-0">
							<div class="flex flex-wrap items-center gap-2 mb-1">
								<span class="text-gray-500 font-mono text-xs">{s.id}</span>
								<span class="text-gray-300">{fmtTs(s.ts)}</span>
								{#if s.label}
									<span class="text-indigo-300 text-xs">{s.label}</span>
								{/if}
								<!-- Версия промпта -->
								{#if s.prompt_source}
									<span class="text-xs px-1.5 py-0.5 rounded {s.prompt_source === 'override' ? 'bg-amber-900/40 text-amber-300' : 'bg-gray-800 text-gray-500'}">
										промпт: {s.prompt_source === 'override' ? 'override' : 'встроенный'} · {s.prompt_chars ?? '?'} симв.
									</span>
								{/if}
							</div>
							<!-- Превью промпта -->
							{#if s.prompt_preview}
								<div class="text-xs text-gray-600 font-mono truncate max-w-xl" title={s.prompt_preview}>
									{s.prompt_preview.slice(0, 100)}…
								</div>
							{/if}
							<!-- Ключевые метрики снимка -->
							{#if s.stats}
								<div class="flex flex-wrap gap-3 mt-1.5 text-xs text-gray-500">
									<span>👍 {s.stats.good ?? 0}</span>
									<span>👎 {s.stats.bad ?? 0}</span>
									<span>Команд {s.stats.total ?? 0}</span>
									<span>Ошибок {s.stats.errors ?? 0}</span>
									{#if s.stats.avg_ms}
										<span>{s.stats.avg_ms}ms avg</span>
									{/if}
								</div>
							{/if}
						</div>
						<button
							type="button"
							onclick={() => setBaseline(s.id)}
							class="shrink-0 text-xs px-2 py-1 rounded border border-indigo-700 text-indigo-300 hover:bg-indigo-950"
						>
							Сделать базой
						</button>
					</div>
				</div>
			{/each}
		</div>
		{#if !hist.snapshots?.length}
			<p class="text-gray-500 text-sm">Снимков ещё нет — нажмите «Новый снимок».</p>
		{/if}
	{/if}
</div>
