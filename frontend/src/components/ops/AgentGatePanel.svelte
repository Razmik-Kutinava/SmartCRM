<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	import {
		DEFAULT_GATE_DATASET,
		GATE_AGENTS,
		GATE_RUN_MODES,
		agentDelta,
		agentSummaryCards,
		deltaColor,
		failedRowsForTab,
		formatDeltaLine,
		gateDownloadUrl,
		gateEmoji,
		gateRowsForAgent,
		rateColor,
		runModeToBody
	} from '$lib/ops/agentEvalGate.js';

	const API = getApiUrl();

	let { datasets = [], onDatasetsChange = () => {} } = $props();

	let gateData = $state(null);
	let ollamaStatus = $state(null);
	let loading = $state(true);
	let gateRunning = $state(false);
	let bulkRunning = $state(false);
	let agentTab = $state('all');
	let datasetId = $state(null);
	let toast = $state('');
	let runMode = $state('all');
	let hermesLimit = $state(0);
	let agentLimit = $state(0);

	async function loadGate() {
		loading = true;
		try {
			const [st, lat] = await Promise.all([
				fetch(`${API}/api/ops/eval/agents-gate/status`),
				fetch(`${API}/api/ops/eval/agents-gate/latest`)
			]);
			ollamaStatus = await st.json();
			gateData = await lat.json();
		} catch (e) {
			console.error(e);
			gateData = { found: false };
		} finally {
			loading = false;
		}
	}

	async function ensureDefaultDataset() {
		try {
			const r = await fetch(`${API}/api/ops/eval/agents-gate/ensure-dataset`, { method: 'POST' });
			if (!r.ok) return;
			const ds = await r.json();
			datasetId = ds.id;
			const exists = datasets.some((d) => d.id === ds.id);
			if (!exists) {
				onDatasetsChange([{ ...ds, record_count: ds.record_count ?? 0 }, ...datasets]);
			}
		} catch (e) {
			console.error('ensure-dataset', e);
		}
	}

	async function runGate() {
		gateRunning = true;
		toast = '';
		try {
			const body = runModeToBody(runMode, hermesLimit, agentLimit);
			const r = await fetch(`${API}/api/ops/eval/agents-gate/run`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(body)
			});
			if (!r.ok) {
				const err = await r.json();
				toast = err.detail || 'Ошибка gate';
				return;
			}
			const rep = await r.json();
			gateData = {
				found: true,
				artifact_name: rep.artifact_name,
				artifact_path: rep.artifact_path,
				generated_at: rep.generated_at,
				overall_gate: rep.overall_gate,
				gaps: rep.gaps,
				agents: rep.agents,
				delta_vs_previous: rep.delta_vs_previous
			};
			toast = `Готово: ${rep.overall_gate}`;
		} catch (e) {
			toast = String(e);
		} finally {
			gateRunning = false;
		}
	}

	async function addToDataset(row) {
		if (!datasetId) {
			toast = 'Датасет не выбран';
			return;
		}
		try {
			const r = await fetch(`${API}/api/ops/eval/agents-gate/failed-to-dataset`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ dataset_id: datasetId, agent: row.agent, case_id: row.id })
			});
			if (!r.ok) {
				const err = await r.json();
				toast = err.detail || 'Не удалось добавить';
				return;
			}
			toast = `Добавлено: ${row.agent}/${row.id}`;
		} catch (e) {
			toast = String(e);
		}
	}

	async function bulkFailedToDataset() {
		bulkRunning = true;
		toast = '';
		try {
			const r = await fetch(`${API}/api/ops/eval/agents-gate/failed-to-dataset/bulk`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ dataset_id: datasetId, agent: agentTab })
			});
			if (!r.ok) {
				const err = await r.json();
				toast = err.detail || 'Bulk не удался';
				return;
			}
			const rep = await r.json();
			toast = `Bulk: +${rep.added} в датасет #${rep.dataset_id}`;
		} catch (e) {
			toast = String(e);
		} finally {
			bulkRunning = false;
		}
	}

	onMount(async () => {
		await Promise.all([loadGate(), ensureDefaultDataset()]);
	});

	$effect(() => {
		if (!datasetId && datasets.length) {
			const def = datasets.find((d) => d.name === DEFAULT_GATE_DATASET);
			if (def) datasetId = def.id;
		}
	});

	let rows = $derived(gateRowsForAgent(gateData, agentTab));
	let failedCount = $derived(failedRowsForTab(gateData, agentTab).length);
	let cards = $derived(agentSummaryCards(gateData));
	let downloadUrl = $derived(gateDownloadUrl(API));
</script>

<p class="text-sm text-gray-400 mb-4 max-w-2xl">
	Pass rate: Hermes ≥85% / агенты ≥75%. Ollama hermes3:latest. Лимиты 0 = все кейсы.
</p>

{#if ollamaStatus}
	<p class="text-xs mb-3 {ollamaStatus.ready ? 'text-emerald-500' : 'text-red-400'}">
		Ollama: {ollamaStatus.ready ? `готов (${ollamaStatus.model})` : ollamaStatus.error}
	</p>
{/if}

{#if gateData?.found}
	<div class="flex flex-wrap items-center gap-3 mb-3 text-xs text-gray-500">
		<span>{gateEmoji(gateData.overall_gate)} overall: {gateData.overall_gate}</span>
		<span>· {gateData.generated_at?.slice(0, 19) || '—'}</span>
		<a
			href={downloadUrl}
			download={gateData.artifact_name || 'agents_gate.json'}
			class="text-indigo-400 hover:underline"
			data-testid="gate-artifact-download"
		>⬇ {gateData.artifact_name}</a>
		{#if gateData.delta_vs_previous?.has_previous}
			<span class="text-gray-600">
				· Δ vs {gateData.delta_vs_previous.previous_artifact_name || 'prev'}
			</span>
		{/if}
	</div>
	{#if gateData.delta_vs_previous?.has_previous}
		<p class="text-xs text-gray-500 mb-2">
			Overall: {gateData.delta_vs_previous.overall_was} → {gateData.delta_vs_previous.overall_became}
		</p>
	{/if}
	<div class="grid grid-cols-2 md:grid-cols-3 gap-2 mb-4 max-w-4xl">
		{#each cards as c}
			{#if !c.missing}
				<button
					type="button"
					class="text-left bg-gray-900 border border-gray-800 rounded-lg p-3 hover:border-indigo-700"
					onclick={() => (agentTab = c.id)}
				>
					<div class="text-xs text-gray-500">{c.label}</div>
					<div class="text-xl font-bold {rateColor(c.pass_rate, c.threshold)}">{c.pass_rate}%</div>
					<div class="text-xs text-gray-600">{gateEmoji(c.gate)} {c.passed}/{c.total}</div>
					{@const d = agentDelta(gateData.delta_vs_previous, c.id)}
					{#if d}
						<div class="text-[10px] mt-1 {deltaColor(d.delta_pct)}">{formatDeltaLine(d)}</div>
					{/if}
				</button>
			{/if}
		{/each}
	</div>
{:else if !loading}
	<p class="text-sm text-amber-400/90 mb-4">Артефакт gate не найден — запустите прогон ниже.</p>
{/if}

<div class="flex flex-wrap gap-2 mb-4">
	{#each [{ id: 'all', label: 'Все' }, ...GATE_AGENTS] as t}
		<button
			type="button"
			class="px-3 py-1 text-xs rounded-lg border {agentTab === t.id
				? 'bg-indigo-600 border-indigo-500 text-white'
				: 'border-gray-700 text-gray-400'}"
			onclick={() => (agentTab = t.id)}
		>{t.label}</button>
	{/each}
</div>

<div class="bg-gray-900/60 border border-gray-800 rounded-xl p-4 mb-4 max-w-3xl">
	<h3 class="text-xs text-gray-500 uppercase mb-3">Параметры прогона</h3>
	<div class="flex flex-wrap gap-3 mb-3">
		{#each GATE_RUN_MODES as m}
			<label class="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
				<input type="radio" bind:group={runMode} value={m.id} class="accent-violet-500" />
				{m.label}
			</label>
		{/each}
	</div>
	<div class="flex flex-wrap gap-4 text-sm">
		<label class="text-gray-400">
			Hermes limit
			<input
				type="number"
				min="0"
				bind:value={hermesLimit}
				class="ml-2 w-20 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-100"
			/>
		</label>
		<label class="text-gray-400">
			Agent limit
			<input
				type="number"
				min="0"
				bind:value={agentLimit}
				class="ml-2 w-20 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-100"
			/>
		</label>
	</div>
</div>

<div class="flex flex-wrap items-center gap-3 mb-4">
	<button
		type="button"
		disabled={gateRunning || !ollamaStatus?.ready}
		class="px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-sm rounded-lg"
		data-testid="gate-run-btn"
		onclick={runGate}
	>{gateRunning ? 'Прогон Ollama…' : 'Запустить gate'}</button>
	<button type="button" class="text-xs text-gray-400 hover:text-gray-200" onclick={loadGate}>↻ Обновить</button>
	<select
		bind:value={datasetId}
		class="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-sm text-gray-200"
		data-testid="gate-dataset-select"
	>
		<option value={null}>Датасет…</option>
		{#each datasets as ds}
			<option value={ds.id}>{ds.name} ({ds.record_count ?? 0})</option>
		{/each}
	</select>
	<button
		type="button"
		disabled={bulkRunning || !gateData?.found || failedCount === 0}
		class="px-3 py-1.5 text-sm rounded-lg border border-indigo-700 text-indigo-300 disabled:opacity-40"
		data-testid="gate-bulk-btn"
		onclick={bulkFailedToDataset}
	>
		{bulkRunning ? 'Импорт…' : `Все failed (${failedCount}) → датасет`}
	</button>
	{#if toast}<span class="text-xs text-amber-400">{toast}</span>{/if}
</div>

<div class="bg-gray-900/40 border border-gray-800 rounded-xl p-4 mb-6 max-w-3xl">
	<h3 class="text-xs text-violet-400 uppercase mb-2">Обучение после gate</h3>
	<ol class="text-sm text-gray-400 space-y-1 list-decimal list-inside">
		<li>
			Failed → датасет на
			<a href="/ops/tuning?dataset={DEFAULT_GATE_DATASET}" class="text-indigo-400 hover:underline">/ops/tuning</a>
			(кнопки выше или «Импорт failed из gate»)
		</li>
		<li>
			Тюнинг промптов —
			<a href="/ops/agents" class="text-indigo-400 hover:underline">/ops/agents</a>,
			<a href="/ops/intents/improve" class="text-indigo-400 hover:underline">/ops/intents/improve</a>
		</li>
		<li>Повторный gate — смотрите дельту «было % → стало %» на карточках</li>
	</ol>
</div>

{#if rows.length}
	<div class="bg-gray-900 rounded-xl border border-gray-800 overflow-x-auto">
		<table class="w-full text-sm min-w-[520px]">
			<thead class="bg-gray-800 text-gray-400 text-xs">
				<tr>
					<th class="px-3 py-2 text-left">Агент</th>
					<th class="px-3 py-2 text-left">Кейс</th>
					<th class="px-3 py-2 text-left">Статус</th>
					<th class="px-3 py-2 text-left"></th>
				</tr>
			</thead>
			<tbody class="divide-y divide-gray-800">
				{#each rows as row}
					<tr class="hover:bg-gray-800/40">
						<td class="px-3 py-2 text-gray-400 text-xs">{row.agent}</td>
						<td class="px-3 py-2 font-mono text-xs text-gray-200">{row.id}</td>
						<td class="px-3 py-2 text-xs">
							{#if row.passed}<span class="text-emerald-400">pass</span>
							{:else}<span class="text-red-400">{row.reason || row.error || 'fail'}</span>{/if}
						</td>
						<td class="px-3 py-2">
							{#if !row.passed}
								<button
									type="button"
									class="text-xs text-indigo-400 hover:underline"
									onclick={() => addToDataset(row)}
								>В датасет</button>
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{:else if !loading && gateData?.found}
	<p class="text-sm text-gray-500">Нет строк для вкладки.</p>
{/if}
