<script>
	import { getApiUrl } from '$lib/websocket.js';
	import {
		GATE_AGENTS,
		agentSummaryCards,
		gateEmoji,
		gateRowsForAgent,
		rateColor
	} from '$lib/ops/agentEvalGate.js';

	const API = getApiUrl();

	let { datasets = [] } = $props();

	let gateData = $state(null);
	let ollamaStatus = $state(null);
	let loading = $state(true);
	let gateRunning = $state(false);
	let agentTab = $state('all');
	let datasetId = $state(null);
	let toast = $state('');

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

	async function runGate() {
		gateRunning = true;
		toast = '';
		try {
			const r = await fetch(`${API}/api/ops/eval/agents-gate/run`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ save_artifact: true, write_acceptance: false })
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
				agents: rep.agents
			};
		} catch (e) {
			toast = String(e);
		} finally {
			gateRunning = false;
		}
	}

	async function addToDataset(row) {
		if (!datasetId) {
			toast = 'Выберите датасет';
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
			toast = `Добавлено: ${row.id}`;
		} catch (e) {
			toast = String(e);
		}
	}

	$effect(() => {
		loadGate();
	});

	let rows = $derived(gateRowsForAgent(gateData, agentTab));
	let cards = $derived(agentSummaryCards(gateData));
</script>

<section class="mt-10 border-t border-gray-800 pt-8">
	<h2 class="text-lg font-semibold text-white mb-2">Quality gate — 6 агентов (Ollama)</h2>
	<p class="text-sm text-gray-400 mb-4 max-w-2xl">
		Pass rate по порогам Hermes 85% / агенты 75%. Последний JSON в
		<code class="text-gray-500">backend/data/artifacts/eval/</code>.
	</p>

	{#if ollamaStatus}
		<p class="text-xs mb-3 {ollamaStatus.ready ? 'text-emerald-500' : 'text-red-400'}">
			Ollama: {ollamaStatus.ready ? `готов (${ollamaStatus.model})` : ollamaStatus.error}
		</p>
	{/if}

	{#if gateData?.found}
		<p class="text-xs text-gray-500 mb-3">
			{gateEmoji(gateData.overall_gate)} overall: {gateData.overall_gate}
			· {gateData.artifact_name}
			· {gateData.generated_at?.slice(0, 19) || '—'}
		</p>
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
					</button>
				{/if}
			{/each}
		</div>
	{:else if !loading}
		<p class="text-sm text-gray-500 mb-4">Артефакт gate ещё не найден — запустите прогон.</p>
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

	<div class="flex flex-wrap items-center gap-3 mb-4">
		<button
			type="button"
			disabled={gateRunning || !ollamaStatus?.ready}
			class="px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-sm rounded-lg"
			onclick={runGate}
		>{gateRunning ? 'Прогон Ollama…' : 'Запустить gate'}</button>
		<select
			bind:value={datasetId}
			class="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-sm text-gray-200"
		>
			<option value={null}>Датасет для failed…</option>
			{#each datasets as ds}
				<option value={ds.id}>{ds.name} ({ds.record_count})</option>
			{/each}
		</select>
		{#if toast}<span class="text-xs text-amber-400">{toast}</span>{/if}
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
</section>
