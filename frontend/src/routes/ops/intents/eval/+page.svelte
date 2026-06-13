<script>
	import { onMount } from 'svelte';
	import HermesEvalPanel from '../../../../components/ops/HermesEvalPanel.svelte';
	import AgentGatePanel from '../../../../components/ops/AgentGatePanel.svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();
	let datasets = $state([]);
	/** @type {'hermes' | 'gate'} */
	let pageTab = $state('hermes');

	async function loadDatasets() {
		try {
			const r = await fetch(`${API}/api/ops/training-datasets`);
			const d = await r.json();
			datasets = d.items || [];
		} catch (e) {
			console.error(e);
		}
	}

	onMount(loadDatasets);
</script>

<div class="px-6 py-6">
	<div class="flex gap-2 mb-6 border-b border-gray-800 pb-2" data-testid="eval-page-tabs">
		<button
			type="button"
			class="px-4 py-2 text-sm rounded-t-lg {pageTab === 'hermes'
				? 'bg-gray-800 text-white border border-gray-700 border-b-0'
				: 'text-gray-400 hover:text-gray-200'}"
			onclick={() => (pageTab = 'hermes')}
		>Hermes eval</button>
		<button
			type="button"
			class="px-4 py-2 text-sm rounded-t-lg {pageTab === 'gate'
				? 'bg-gray-800 text-white border border-gray-700 border-b-0'
				: 'text-gray-400 hover:text-gray-200'}"
			onclick={() => (pageTab = 'gate')}
		>Quality gate</button>
	</div>

	{#if pageTab === 'hermes'}
		<HermesEvalPanel />
	{:else}
		<AgentGatePanel {datasets} onDatasetsChange={(items) => (datasets = items)} />
	{/if}
</div>
