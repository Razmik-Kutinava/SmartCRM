<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	let datasets = $state([]);
	let loading = $state(true);
	let err = $state('');

	let selectedId = $state(null);
	let selected = $state(null);
	let records = $state([]);
	let recTotal = $state(0);
	let recOffset = $state(0);
	const recLimit = 50;

	let newName = $state('');
	let newDesc = $state('');

	let uploadMsg = $state('');
	let importMsg = $state('');

	// редактирование строки
	let editingRecord = $state(null);
	let editInput = $state('');
	let editOutput = $state('{}');
	let editNotes = $state('');

	async function loadDatasets() {
		loading = true;
		try {
			const r = await fetch(`${API}/api/ops/training-datasets`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			datasets = d.items || [];
			err = '';
		} catch (e) {
			err = String(e?.message || e);
		} finally {
			loading = false;
		}
	}

	async function selectDataset(id) {
		selectedId = id;
		recOffset = 0;
		editingRecord = null;
		await loadDatasetMeta(id);
		await loadRecords();
	}

	async function loadDatasetMeta(id) {
		try {
			const r = await fetch(`${API}/api/ops/training-datasets/${id}`);
			if (!r.ok) throw new Error(await r.text());
			selected = await r.json();
		} catch (e) {
			err = String(e?.message || e);
		}
	}

	async function loadRecords() {
		if (!selectedId) return;
		try {
			const r = await fetch(
				`${API}/api/ops/training-datasets/${selectedId}/records?limit=${recLimit}&offset=${recOffset}`
			);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			records = d.items || [];
			recTotal = d.total ?? 0;
		} catch (e) {
			err = String(e?.message || e);
		}
	}

	async function createDataset() {
		if (!newName.trim()) {
			err = 'Введите название';
			return;
		}
		err = '';
		try {
			const r = await fetch(`${API}/api/ops/training-datasets`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ name: newName.trim(), description: newDesc })
			});
			if (!r.ok) throw new Error(await r.text());
			newName = '';
			newDesc = '';
			await loadDatasets();
		} catch (e) {
			err = String(e?.message || e);
		}
	}

	async function uploadFile(ev) {
		const f = ev.target?.files?.[0];
		if (!f || !selectedId) return;
		uploadMsg = 'Загрузка…';
		const fd = new FormData();
		fd.append('file', f);
		try {
			const r = await fetch(`${API}/api/ops/training-datasets/${selectedId}/upload`, {
				method: 'POST',
				body: fd
			});
			const d = await r.json();
			if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
			uploadMsg = `Импортировано: ${d.imported}. Ошибок разбора: ${d.error_count || 0}`;
			if (d.errors?.length) uploadMsg += ` (первые: ${d.errors.slice(0, 3).join('; ')})`;
			ev.target.value = '';
			await loadDatasets();
			await selectDataset(selectedId);
		} catch (e) {
			uploadMsg = '';
			err = String(e?.message || e);
		}
	}

	async function importBadTraces() {
		if (!selectedId) return;
		importMsg = '…';
		try {
			const r = await fetch(
				`${API}/api/ops/training-datasets/${selectedId}/import-bad-traces?limit=300`,
				{ method: 'POST' }
			);
			const d = await r.json();
			if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
			importMsg = `Добавлено из трейсов 👎: ${d.imported}. ${d.message || ''}`;
			await loadDatasets();
			await selectDataset(selectedId);
		} catch (e) {
			importMsg = '';
			err = String(e?.message || e);
		}
	}

	function exportDs(fmt) {
		if (!selectedId) return;
		window.open(
			`${API}/api/ops/training-datasets/${selectedId}/export?format=${fmt}&only_pairs=true`,
			'_blank'
		);
	}

	async function clearDs() {
		if (!selectedId || !confirm('Удалить все записи этого датасета?')) return;
		try {
			const r = await fetch(`${API}/api/ops/training-datasets/${selectedId}/clear`, {
				method: 'POST'
			});
			if (!r.ok) throw new Error(await r.text());
			await selectDataset(selectedId);
		} catch (e) {
			err = String(e?.message || e);
		}
	}

	async function deleteDataset() {
		if (!selectedId || !confirm('Удалить датасет полностью?')) return;
		try {
			const r = await fetch(`${API}/api/ops/training-datasets/${selectedId}`, { method: 'DELETE' });
			if (!r.ok) throw new Error(await r.text());
			selectedId = null;
			selected = null;
			records = [];
			await loadDatasets();
		} catch (e) {
			err = String(e?.message || e);
		}
	}

	function openEdit(rec) {
		editingRecord = rec.id;
		editInput = rec.input_text || '';
		editOutput = JSON.stringify(rec.output_json || {}, null, 2);
		editNotes = rec.notes || '';
	}

	async function saveEdit() {
		if (!selectedId || !editingRecord) return;
		let out = {};
		try {
			out = JSON.parse(editOutput || '{}');
		} catch {
			err = 'Output — невалидный JSON';
			return;
		}
		try {
			const r = await fetch(
				`${API}/api/ops/training-datasets/${selectedId}/records/${editingRecord}`,
				{
					method: 'PATCH',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						input_text: editInput,
						output_json: out,
						notes: editNotes
					})
				}
			);
			if (!r.ok) throw new Error(await r.text());
			editingRecord = null;
			await loadRecords();
			await loadDatasetMeta(selectedId);
		} catch (e) {
			err = String(e?.message || e);
		}
	}

	async function deleteRecord(recId) {
		if (!selectedId || !confirm('Удалить запись?')) return;
		try {
			const r = await fetch(
				`${API}/api/ops/training-datasets/${selectedId}/records/${recId}`,
				{ method: 'DELETE' }
			);
			if (!r.ok) throw new Error(await r.text());
			editingRecord = null;
			await loadRecords();
			await loadDatasetMeta(selectedId);
		} catch (e) {
			err = String(e?.message || e);
		}
	}

	function nextPage() {
		if (recOffset + recLimit < recTotal) {
			recOffset += recLimit;
			loadRecords();
		}
	}
	function prevPage() {
		if (recOffset >= recLimit) {
			recOffset -= recLimit;
			loadRecords();
		}
	}

	onMount(loadDatasets);
</script>

<div class="px-6 py-6 max-w-6xl">
	<p class="text-sm text-gray-400 mb-4 max-w-3xl">
		Датасеты для <strong class="text-gray-200">fine-tune на отдельной машине</strong>: загрузите CSV / JSON / JSONL с парами
		или PDF (текст нарежется на чанки). Экспортируйте JSONL и передайте в обучение (LoRA и т.д.). Импорт 👎 трейсов —
		черновик: проверьте и поправьте ответы вручную.
	</p>

	{#if err}
		<div class="mb-4 text-sm text-red-400 whitespace-pre-wrap">{err}</div>
	{/if}

	<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
		<div class="lg:col-span-1 space-y-4">
			<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
				<h2 class="text-sm font-medium text-white mb-3">Новый датасет</h2>
				<input
					bind:value={newName}
					placeholder="Название"
					class="w-full mb-2 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
				/>
				<textarea
					bind:value={newDesc}
					placeholder="Описание (опционально)"
					rows="2"
					class="w-full mb-2 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
				></textarea>
				<button
					type="button"
					onclick={createDataset}
					class="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg"
				>
					Создать
				</button>
			</div>

			<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
				<h2 class="text-sm font-medium text-white mb-2">Список</h2>
				{#if loading}
					<p class="text-gray-500 text-sm">Загрузка…</p>
				{:else if datasets.length === 0}
					<p class="text-gray-500 text-sm">Пока пусто</p>
				{:else}
					<ul class="space-y-1">
						{#each datasets as ds}
							<li>
								<button
									type="button"
									onclick={() => selectDataset(ds.id)}
									class="w-full text-left px-3 py-2 rounded-lg text-sm transition-colors
										{selectedId === ds.id ? 'bg-indigo-900/50 text-white' : 'text-gray-400 hover:bg-gray-800'}"
								>
									<span class="font-medium">{ds.name}</span>
									<span class="text-gray-600 ml-1">({ds.record_count ?? 0})</span>
								</button>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		</div>

		<div class="lg:col-span-2 space-y-4">
			{#if selected && selectedId}
				<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
					<div class="flex flex-wrap justify-between gap-2 mb-3">
						<div>
							<h2 class="text-lg font-medium text-white">{selected.name}</h2>
							<p class="text-xs text-gray-500">{selected.description || '—'}</p>
							<p class="text-xs text-gray-600 mt-1">
								Записей: {selected.record_count ?? 0} · статус: {selected.status}
							</p>
						</div>
						<button
							type="button"
							onclick={deleteDataset}
							class="text-xs text-red-400 hover:text-red-300 px-2 py-1"
						>
							Удалить датасет
						</button>
					</div>

					<div class="flex flex-wrap gap-2 items-center mb-3">
						<label class="text-xs text-gray-400 cursor-pointer px-3 py-2 bg-gray-800 rounded-lg hover:bg-gray-700">
							Загрузить файл (.csv / .json / .jsonl / .pdf)
							<input type="file" accept=".csv,.json,.jsonl,.pdf,.ndjson" class="hidden" onchange={uploadFile} />
						</label>
						<button
							type="button"
							onclick={importBadTraces}
							class="text-xs px-3 py-2 bg-amber-900/40 text-amber-200 rounded-lg hover:bg-amber-900/60"
						>
							Импорт трейсов 👎
						</button>
						<button
							type="button"
							onclick={() => exportDs('jsonl')}
							class="text-xs px-3 py-2 bg-emerald-900/40 text-emerald-200 rounded-lg"
						>
							Скачать JSONL
						</button>
						<button
							type="button"
							onclick={() => exportDs('chat')}
							class="text-xs px-3 py-2 bg-emerald-900/40 text-emerald-200 rounded-lg"
						>
							Скачать chat-формат
						</button>
						<button
							type="button"
							onclick={clearDs}
							class="text-xs px-3 py-2 bg-gray-800 text-gray-400 rounded-lg"
						>
							Очистить записи
						</button>
					</div>
					{#if uploadMsg}
						<p class="text-xs text-gray-500 mb-2">{uploadMsg}</p>
					{/if}
					{#if importMsg}
						<p class="text-xs text-amber-600/90 mb-2">{importMsg}</p>
					{/if}

					<p class="text-xs text-gray-600 border-t border-gray-800 pt-3 mt-2">
						<strong class="text-gray-500">Форматы:</strong> JSONL — по строке объект с полями
						<code class="text-gray-400">input</code> и
						<code class="text-gray-400">output</code> (JSON с intent/slots/reply). CSV — колонки
						<code class="text-gray-400">input</code>,
						<code class="text-gray-400">output</code> (JSON-строка) или
						<code class="text-gray-400">intent</code>,
						<code class="text-gray-400">reply</code>,
						<code class="text-gray-400">slots_json</code>. PDF — только извлечение текста (чанки без разметки).
					</p>
				</div>

				<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 overflow-x-auto">
					<div class="flex justify-between items-center mb-2">
						<h3 class="text-sm font-medium text-white">Записи</h3>
						<div class="flex gap-2 text-xs text-gray-500">
							<button type="button" class="hover:text-white" onclick={prevPage} disabled={recOffset === 0}>
								←
							</button>
							<span>{recOffset + 1}–{Math.min(recOffset + recLimit, recTotal)} / {recTotal}</span>
							<button
								type="button"
								class="hover:text-white"
								onclick={nextPage}
								disabled={recOffset + recLimit >= recTotal}
							>
								→
							</button>
						</div>
					</div>

					<table class="w-full text-xs text-left">
						<thead>
							<tr class="text-gray-500 border-b border-gray-800">
								<th class="py-2 pr-2 w-10">#</th>
								<th class="py-2 pr-2">Тип</th>
								<th class="py-2 pr-2">Ввод</th>
								<th class="py-2">Действия</th>
							</tr>
						</thead>
						<tbody>
							{#each records as rec}
								<tr class="border-b border-gray-800/60 align-top">
									<td class="py-2 text-gray-600">{rec.sort_idx}</td>
									<td class="py-2 text-gray-500">{rec.record_type}</td>
									<td class="py-2 text-gray-300 max-w-md">
										<div class="line-clamp-3" title={rec.input_text}>{rec.input_text}</div>
										{#if rec.record_type === 'pair' && rec.output_json}
											<pre class="text-gray-600 mt-1 text-[10px] overflow-x-auto max-h-24">{JSON.stringify(
													rec.output_json,
													null,
													0
												)}</pre>
										{/if}
									</td>
									<td class="py-2 whitespace-nowrap">
										<button
											type="button"
											class="text-indigo-400 hover:text-indigo-300 mr-2"
											onclick={() => openEdit(rec)}
										>
											Правка
										</button>
										<button
											type="button"
											class="text-red-500/80 hover:text-red-400"
											onclick={() => deleteRecord(rec.id)}
										>
											Удал.
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				{#if editingRecord}
					<div class="bg-gray-950 border border-indigo-800/50 rounded-xl p-4 space-y-2">
						<h3 class="text-sm text-white">Редактирование записи #{editingRecord}</h3>
						<label for="tune-edit-in" class="block text-xs text-gray-500">Фраза (input)</label>
						<textarea
							id="tune-edit-in"
							bind:value={editInput}
							rows="3"
							class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
						></textarea>
						<label for="tune-edit-out" class="block text-xs text-gray-500">Output (JSON Hermes)</label>
						<textarea
							id="tune-edit-out"
							bind:value={editOutput}
							rows="8"
							class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono text-gray-100"
						></textarea>
						<label for="tune-edit-notes" class="block text-xs text-gray-500">Заметки</label>
						<input
							id="tune-edit-notes"
							bind:value={editNotes}
							class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
						/>
						<div class="flex gap-2 pt-2">
							<button
								type="button"
								onclick={saveEdit}
								class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg"
							>
								Сохранить
							</button>
							<button
								type="button"
								onclick={() => (editingRecord = null)}
								class="px-4 py-2 border border-gray-700 text-gray-400 text-sm rounded-lg"
							>
								Отмена
							</button>
						</div>
					</div>
				{/if}
			{:else}
				<div class="text-center text-gray-500 py-16 border border-dashed border-gray-800 rounded-xl">
					Выберите датасет слева или создайте новый
				</div>
			{/if}
		</div>
	</div>
</div>
