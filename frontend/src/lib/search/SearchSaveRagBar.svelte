<script>
	import { ingestSearchDocuments } from '$lib/search/saveToRagFromHits.js';

	let {
		documents = [],
		defaultForAgent = 'all',
		tags = 'search',
		testIdPrefix = 'search-save-rag',
	} = $props();

	const RAG_AGENTS = [
		{ id: 'all', label: 'Все агенты' },
		{ id: 'analyst', label: 'Аналитик' },
		{ id: 'economist', label: 'Экономист' },
		{ id: 'marketer', label: 'Маркетолог' },
		{ id: 'tech_specialist', label: 'Тех. спец' },
		{ id: 'strategist', label: 'Стратег' },
	];

	let forAgent = $state('all');
	let approved = $state(new Set());
	let previewing = $state(false);
	let ingesting = $state(false);
	let preview = $state(null);
	let msg = $state('');
	let ok = $state(false);

	$effect(() => {
		const agent = defaultForAgent === 'default' ? 'all' : (defaultForAgent || 'all');
		forAgent = agent;
		approved = new Set((documents || []).map((_, i) => i));
		preview = null;
		msg = '';
		ok = false;
	});

	function selectedDocs() {
		return (documents || []).filter((_, i) => approved.has(i));
	}

	function toggle(i) {
		const next = new Set(approved);
		if (next.has(i)) next.delete(i);
		else next.add(i);
		approved = next;
	}

	async function previewChunks() {
		if (!approved.size || previewing) return;
		previewing = true;
		msg = '';
		try {
			preview = await ingestSearchDocuments({
				documents: selectedDocs(),
				forAgent,
				tags,
				dryRun: true,
			});
		} catch (e) {
			msg = e?.message || String(e);
			ok = false;
		} finally {
			previewing = false;
		}
	}

	async function saveToRag() {
		if (ingesting) return;
		ingesting = true;
		msg = '';
		ok = false;
		try {
			const data = await ingestSearchDocuments({
				documents: selectedDocs(),
				forAgent,
				tags,
				dryRun: false,
			});
			ok = true;
			msg = `Загружено ${data.ingested} док. · ${data.total_chunks ?? preview?.total_chunks ?? '?'} чанков → RAG (${forAgent})`;
			if (data.errors?.length) msg += `. Ошибки: ${data.errors.join('; ')}`;
		} catch (e) {
			msg = e?.message || String(e);
		} finally {
			ingesting = false;
		}
	}
</script>

{#if documents?.length}
	<div
		class="bg-gray-900 border border-cyan-900/35 rounded-xl p-4 space-y-3"
		data-testid={testIdPrefix}
	>
		<div class="flex flex-wrap items-center justify-between gap-2">
			<span class="text-xs text-cyan-400/90 font-medium">📚 Сохранить в базу знаний</span>
			<span class="text-xs text-gray-500">Документов: {documents.length} · выбрано: {approved.size}</span>
		</div>
		<div class="flex flex-wrap items-center gap-3">
			<select
				bind:value={forAgent}
				class="rounded-lg border border-gray-700 bg-gray-950 px-2 py-1.5 text-xs text-white"
			>
				{#each RAG_AGENTS as a}
					<option value={a.id}>{a.label}</option>
				{/each}
			</select>
			<button
				type="button"
				data-testid="{testIdPrefix}-preview"
				onclick={previewChunks}
				disabled={!approved.size || previewing}
				class="px-3 py-1.5 text-xs bg-indigo-800 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-lg"
			>
				{previewing ? '⟳...' : 'Посмотреть чанки'}
			</button>
			<button
				type="button"
				data-testid="{testIdPrefix}-save"
				onclick={saveToRag}
				disabled={!approved.size || ingesting}
				class="px-3 py-1.5 text-xs bg-emerald-800 hover:bg-emerald-700 disabled:opacity-40 text-white rounded-lg font-medium"
			>
				{ingesting ? '⟳...' : '✓ Сохранить в базу'}
			</button>
		</div>
		{#if documents.length <= 8}
			<div class="flex flex-wrap gap-2">
				{#each documents as doc, i}
					<label class="flex items-center gap-1.5 text-xs text-gray-400 cursor-pointer">
						<input
							type="checkbox"
							checked={approved.has(i)}
							onchange={() => toggle(i)}
							class="accent-cyan-500"
						/>
						<span class="truncate max-w-[12rem]">{doc.metadata?.title || `Док ${i + 1}`}</span>
					</label>
				{/each}
			</div>
		{:else}
			<button type="button" class="text-xs text-indigo-400" onclick={() => (approved = new Set(documents.map((_, i) => i)))}>
				Выбрать все {documents.length}
			</button>
		{/if}
		{#if preview?.total_chunks != null && !ok}
			<div class="text-xs text-gray-500">Превью: {preview.total_chunks} чанков</div>
		{/if}
		{#if msg}
			<div class="text-xs {ok ? 'text-emerald-400' : 'text-amber-400'}">{msg}</div>
		{/if}
	</div>
{/if}
