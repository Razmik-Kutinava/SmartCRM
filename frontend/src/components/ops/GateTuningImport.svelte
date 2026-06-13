<script>
	import { getApiUrl } from '$lib/websocket.js';
	import {
		DEFAULT_GATE_DATASET,
		bulkGateFailedToDataset,
		ensureGateDataset
	} from '$lib/ops/agentEvalGate.js';

	const API = getApiUrl();

	let { onImported = () => {} } = $props();

	let gateMsg = $state('');
	let importing = $state(false);
	let gateFound = $state(false);

	async function checkGate() {
		try {
			const r = await fetch(`${API}/api/ops/eval/agents-gate/latest`);
			const d = await r.json();
			gateFound = d.found === true;
		} catch {
			gateFound = false;
		}
	}

	async function importGateFailed() {
		importing = true;
		gateMsg = '';
		try {
			const ds = await ensureGateDataset(API);
			const rep = await bulkGateFailedToDataset(API, 'all', ds.id);
			gateMsg = `Импорт gate failed: +${rep.added} в «${DEFAULT_GATE_DATASET}» (#${rep.dataset_id})`;
			onImported(ds.id);
		} catch (e) {
			gateMsg = String(e?.message || e);
		} finally {
			importing = false;
		}
	}

	import { onMount } from 'svelte';
	onMount(checkGate);
</script>

<div class="bg-gray-900 border border-violet-900/40 rounded-xl p-4 mb-4">
	<h2 class="text-sm font-medium text-violet-300 mb-2">Петля обучения — шаг 2</h2>
	<p class="text-xs text-gray-400 mb-3">
		Failed из последнего quality gate → датасет
		<code class="text-gray-500">{DEFAULT_GATE_DATASET}</code>. Дальше правьте промпты и гоняйте gate снова.
	</p>
	<div class="flex flex-wrap gap-2 items-center">
		<button
			type="button"
			disabled={importing || !gateFound}
			class="text-xs px-3 py-2 bg-violet-700 hover:bg-violet-600 disabled:opacity-40 text-white rounded-lg"
			data-testid="tuning-gate-import"
			onclick={importGateFailed}
		>
			{importing ? 'Импорт…' : 'Импорт failed из gate'}
		</button>
		<a href="/ops/intents/eval" class="text-xs text-indigo-400 hover:underline">→ Quality gate eval</a>
	</div>
	{#if !gateFound}
		<p class="text-xs text-amber-500/90 mt-2">Артефакт gate не найден — сначала прогон на /ops/intents/eval.</p>
	{/if}
	{#if gateMsg}
		<p class="text-xs text-gray-400 mt-2">{gateMsg}</p>
	{/if}
</div>
