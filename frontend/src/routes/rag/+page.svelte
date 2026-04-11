<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	/** Извлечь читаемое сообщение об ошибке из ответа сервера */
	async function extractError(r) {
		const raw = await r.text();
		try {
			const j = JSON.parse(raw);
			return j.detail || j.error || JSON.stringify(j);
		} catch {
			return raw || `HTTP ${r.status}`;
		}
	}

	const AGENT_OPTIONS = [
		{ id: 'all', label: 'Все агенты (общая база)' },
		{ id: 'analyst', label: 'Аналитик' },
		{ id: 'strategist', label: 'Стратег' },
		{ id: 'economist', label: 'Экономист' },
		{ id: 'marketer', label: 'Маркетолог' },
		{ id: 'tech_specialist', label: 'Тех. спец' },
	];

	let sources = $state([]);
	let totalChunks = $state(0);
	let loading = $state(true);
	let err = $state('');
	let msg = $state('');

	let queryText = $state('');
	let queryAgent = $state('all');
	let queryLoading = $state(false);
	let queryContext = $state('');
	let queryHits = $state([]);

	let ingestTitle = $state('Заметка');
	let ingestText = $state('');
	let tags = $state('');
	let forAgent = $state('all');
	let uploadBusy = $state(false);
	let uploadProgress = $state(0); // 0-100, только при загрузке файла
	let jsonTitle = $state('данные.json');
	let jsonBody = $state('{\n  "продукт": "SmartCRM",\n  "сегмент": "B2B SMB"\n}');

	/** Выбранный файл до загрузки / предпросмотра */
	let pendingFile = $state(null);
	let lastPipeline = $state(null);

	async function loadSources() {
		err = '';
		loading = true;
		try {
			const r = await fetch(`${API}/api/rag/sources`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			sources = d.sources || [];
			totalChunks = d.total_chunks ?? 0;
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
			sources = [];
		} finally {
			loading = false;
		}
	}

	function onFileSelected(ev) {
		const f = ev.target?.files?.[0];
		pendingFile = f || null;
		lastPipeline = null;
		msg = '';
	}

	async function previewFile() {
		if (!pendingFile) { err = 'Сначала выберите файл'; return; }
		uploadBusy = true; err = ''; msg = ''; lastPipeline = null;
		try {
			const fd = new FormData();
			fd.append('file', pendingFile);
			fd.append('tags', tags);
			fd.append('for_agent', forAgent);
			const r = await fetch(`${API}/api/rag/preview`, { method: 'POST', body: fd });
			if (!r.ok) throw new Error(await extractError(r));
			const d = await r.json();
			lastPipeline = d;
			msg = `Предпросмотр: ${d.chunks} чанков (в Chroma не записано)`;
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally { uploadBusy = false; }
	}

	function uploadPendingFile() {
		if (!pendingFile) { err = 'Сначала выберите файл'; return; }
		uploadBusy = true; uploadProgress = 0; err = ''; msg = ''; lastPipeline = null;

		const fd = new FormData();
		fd.append('file', pendingFile);
		fd.append('tags', tags);
		fd.append('for_agent', forAgent);

		const xhr = new XMLHttpRequest();

		xhr.upload.onprogress = (e) => {
			if (e.lengthComputable) uploadProgress = Math.round((e.loaded / e.total) * 100);
		};

		xhr.onload = async () => {
			uploadProgress = 100;
			try {
				if (xhr.status >= 400) {
					let detail = xhr.responseText;
					try { detail = JSON.parse(xhr.responseText)?.detail ?? detail; } catch { /* raw */ }
					throw new Error(detail);
				}
				const d = JSON.parse(xhr.responseText);
				lastPipeline = d;
				msg = `✓ Загружено: ${d.chunks} чанков · «${d.filename || pendingFile?.name}» → агент: ${d.for_agent || forAgent}`;
				await loadSources();
				pendingFile = null;
			} catch (e) {
				err = e instanceof Error ? e.message : String(e);
			} finally {
				uploadBusy = false;
				setTimeout(() => { uploadProgress = 0; }, 1500);
			}
		};

		xhr.onerror = () => {
			err = 'Ошибка сети при загрузке файла';
			uploadBusy = false;
			uploadProgress = 0;
		};

		xhr.open('POST', `${API}/api/rag/upload`);
		xhr.send(fd);
	}

	async function runQuery() {
		if (!queryText.trim()) return;
		queryLoading = true; queryContext = ''; queryHits = [];
		try {
			const q = encodeURIComponent(queryText.trim());
			const fa = encodeURIComponent(queryAgent);
			const r = await fetch(`${API}/api/rag/query?q=${q}&top_k=5&for_agent=${fa}`);
			if (!r.ok) throw new Error(await extractError(r));
			const d = await r.json();
			queryContext = d.context || '';
			queryHits = d.hits || [];
			totalChunks = d.total_chunks ?? totalChunks;
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally { queryLoading = false; }
	}

	async function submitText() {
		if (!ingestText.trim()) return;
		uploadBusy = true; err = ''; msg = ''; lastPipeline = null;
		try {
			const r = await fetch(`${API}/api/rag/ingest`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ title: ingestTitle, text: ingestText, tags, for_agent: forAgent, dry_run: false }),
			});
			if (!r.ok) throw new Error(await extractError(r));
			const d = await r.json();
			lastPipeline = d;
			msg = `✓ Текст добавлен: ${d.chunks} чанков · агент: ${d.for_agent || forAgent}`;
			ingestText = '';
			await loadSources();
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally { uploadBusy = false; }
	}

	async function submitJson() {
		let obj;
		try { obj = JSON.parse(jsonBody); }
		catch { err = 'Неверный JSON'; return; }
		uploadBusy = true;
		err = '';
		msg = '';
		lastPipeline = null;
		try {
			const r = await fetch(`${API}/api/rag/ingest-json`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ title: jsonTitle, json: obj, tags, for_agent: forAgent }),
			});
			if (!r.ok) throw new Error(await extractError(r));
			const d = await r.json();
			lastPipeline = d;
			msg = `✓ JSON добавлен: ${d.chunks} чанков · агент: ${d.for_agent || forAgent}`;
			await loadSources();
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally { uploadBusy = false; }
	}

	async function removeSource(sourceId) {
		if (!confirm('Удалить все чанки этого источника?')) return;
		try {
			const r = await fetch(`${API}/api/rag/sources/${encodeURIComponent(sourceId)}`, { method: 'DELETE' });
			if (!r.ok) throw new Error(await extractError(r));
			await loadSources();
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		}
	}

	onMount(loadSources);
</script>

<div class="flex flex-col h-full overflow-hidden bg-gray-950">
	<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900 shrink-0">
		<div>
			<h1 class="text-lg font-semibold text-white">База знаний</h1>
			<p class="text-xs text-gray-500">
				RAG · Chroma · {totalChunks} чанков · отдельные документы на агента
			</p>
		</div>
	</div>

	<div class="flex-1 overflow-y-auto p-6 space-y-6 max-w-4xl mx-auto w-full pb-24">
		{#if err}
			<div class="rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-2 text-sm text-red-200 whitespace-pre-wrap">{err}</div>
		{/if}
		{#if msg}
			<div class="rounded-lg border border-emerald-900/50 bg-emerald-950/30 px-4 py-2 text-sm text-emerald-200">{msg}</div>
		{/if}

		<div class="grid gap-4 sm:grid-cols-2">
			<div>
				<label for="rag-agent" class="block text-xs text-gray-500 mb-1">Документ для какого агента</label>
				<select
					id="rag-agent"
					bind:value={forAgent}
					class="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
				>
					{#each AGENT_OPTIONS as o}
						<option value={o.id}>{o.label}</option>
					{/each}
				</select>
				<p class="text-xs text-gray-600 mt-1">
					«Все агенты» — общие материалы. Иначе чанки видит только выбранный агент (+ общие).
				</p>
			</div>
			<div>
				<label for="rag-tags" class="block text-xs text-gray-500 mb-1">Теги</label>
				<input
					id="rag-tags"
					bind:value={tags}
					placeholder="продажи, Котлер, налоги…"
					class="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white placeholder:text-gray-600"
				/>
			</div>
		</div>

		<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
			<div class="flex items-center justify-between">
				<div class="text-xs text-gray-500 uppercase tracking-wide">Загрузка файла</div>
				<div class="text-xs text-gray-600">PDF · DOCX · XLSX · CSV · JSON · TXT · MD</div>
			</div>
			<input
				type="file"
				accept=".pdf,.docx,.xlsx,.xlsm,.csv,.json,.txt,.md"
				onchange={onFileSelected}
				class="block w-full text-sm text-gray-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-gray-800 file:text-gray-200 file:cursor-pointer cursor-pointer"
			/>
			{#if pendingFile}
				<p class="text-xs text-gray-400">
					📄 <span class="font-medium">{pendingFile.name}</span>
					<span class="text-gray-600 ml-2">{(pendingFile.size / 1024).toFixed(0)} KB</span>
				</p>
			{/if}
			<div class="flex flex-wrap gap-2 items-center">
				<button
					type="button"
					onclick={previewFile}
					disabled={uploadBusy || !pendingFile}
					class="px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm text-white disabled:opacity-40"
				>
					Предпросмотр пайплайна
				</button>
				<button
					type="button"
					onclick={uploadPendingFile}
					disabled={uploadBusy || !pendingFile}
					class="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm text-white disabled:opacity-40"
				>
					Загрузить в Chroma
				</button>
				{#if uploadBusy && uploadProgress > 0}
					<span class="text-xs font-mono text-indigo-300">{uploadProgress}%</span>
				{/if}
			</div>

			{#if uploadBusy && uploadProgress > 0}
				<div class="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
					<div
						class="h-full rounded-full transition-all duration-200"
						class:bg-indigo-500={uploadProgress < 100}
						class:bg-emerald-500={uploadProgress === 100}
						style="width: {uploadProgress}%"
					></div>
				</div>
			{/if}
			<p class="text-xs text-gray-600">
				Сначала извлекается текст, затем смысловой чанкинг (абзацы и предложения). PDF требует пакет
				<code class="text-gray-400">pypdf</code> в venv:
				<code class="text-gray-400">pip install pypdf</code>
			</p>
		</div>

		{#if lastPipeline?.steps?.length}
			<div class="bg-gray-900 border border-indigo-900/40 rounded-xl p-4 space-y-2">
				<div class="text-xs text-indigo-400 uppercase tracking-wide">Пайплайн (последняя операция)</div>
				<ol class="list-decimal list-inside text-sm text-gray-300 space-y-1">
					{#each lastPipeline.steps as st}
						<li>
							<span class="text-white font-medium">{st.stage}</span>
							{#if st.detail}
								<span class="text-gray-500"> — {st.detail}</span>
							{/if}
							{#if st.chars_extracted != null}
								<span class="text-gray-500"> · символов: {st.chars_extracted}</span>
							{/if}
							{#if st.chunks_total != null}
								<span class="text-gray-500"> · чанков: {st.chunks_total}</span>
							{/if}
							{#if st.for_agent}
								<span class="text-gray-500"> · агент: {st.for_agent}</span>
							{/if}
						</li>
					{/each}
				</ol>
			</div>
		{/if}

		{#if lastPipeline?.chunk_previews?.length}
			<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-2 max-h-96 overflow-y-auto">
				<div class="text-xs text-gray-500 uppercase tracking-wide">Чанки (фрагменты)</div>
				<div class="space-y-2">
					{#each lastPipeline.chunk_previews as ch}
						<div class="rounded-lg bg-gray-800/60 border border-gray-700/80 px-3 py-2 text-xs">
							<div class="text-gray-500 mb-1">
								# {ch.chunk_index}
								{#if ch.paragraph_index != null}
									· абз. {ch.paragraph_index}
								{/if}
								· {ch.chars} симв.
								{#if ch.sheet}
									· лист: {ch.sheet}
								{/if}
								{#if ch.json_path}
									· {ch.json_path}
								{/if}
							</div>
							<div class="text-gray-200 leading-snug">{ch.snippet}</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
			<div class="text-xs text-gray-500 uppercase tracking-wide">Поиск</div>
			<div class="flex flex-col sm:flex-row gap-2">
				<input
					bind:value={queryText}
					placeholder="Запрос к базе…"
					class="flex-1 bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-4 py-2.5 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
					onkeydown={(e) => e.key === 'Enter' && runQuery()}
				/>
				<select
					bind:value={queryAgent}
					class="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white sm:w-52"
				>
					{#each AGENT_OPTIONS as o}
						<option value={o.id}>{o.label}</option>
					{/each}
				</select>
				<button
					type="button"
					onclick={runQuery}
					disabled={queryLoading}
					class="px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm text-white disabled:opacity-50"
				>
					{queryLoading ? '…' : 'Найти'}
				</button>
			</div>
			{#if queryContext}
				<div class="rounded-lg bg-gray-800/80 border border-gray-700 px-3 py-2 text-sm text-gray-200 whitespace-pre-wrap max-h-64 overflow-y-auto">
					{queryContext}
				</div>
			{/if}
			{#if queryHits.length}
				<details class="text-xs text-gray-500">
					<summary class="cursor-pointer hover:text-gray-400">Попадания (JSON)</summary>
					<pre class="mt-2 overflow-x-auto rounded-lg bg-gray-950 px-3 py-2 text-gray-400">{JSON.stringify(queryHits, null, 2)}</pre>
				</details>
			{/if}
		</div>

		<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
			<div class="text-xs text-gray-500 uppercase tracking-wide">Текст вручную</div>
			<input
				bind:value={ingestTitle}
				class="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white"
				placeholder="Заголовок"
			/>
			<textarea
				bind:value={ingestText}
				rows="5"
				placeholder="Абзацы — сохранятся границы смысла"
				class="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder:text-gray-600"
			></textarea>
			<button
				type="button"
				onclick={submitText}
				disabled={uploadBusy}
				class="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm text-white disabled:opacity-50"
			>
				В базу
			</button>
		</div>

		<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
			<div class="text-xs text-gray-500 uppercase tracking-wide">JSON</div>
			<input bind:value={jsonTitle} class="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white" />
			<textarea
				bind:value={jsonBody}
				rows="6"
				spellcheck="false"
				class="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm font-mono text-gray-200"
			></textarea>
			<button
				type="button"
				onclick={submitJson}
				disabled={uploadBusy}
				class="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-sm text-white disabled:opacity-50"
			>
				Загрузить JSON
			</button>
		</div>

		<div class="space-y-2">
			<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Источники</div>
			{#if loading}
				<p class="text-sm text-gray-500">Загрузка…</p>
			{:else if sources.length === 0}
				<p class="text-sm text-gray-500">Пусто. Загрузите файл или текст.</p>
			{:else}
				{#each sources as s}
					<div class="flex items-center gap-4 p-4 bg-gray-900 border border-gray-800 rounded-xl">
						<span class="text-xl shrink-0">📄</span>
						<div class="flex-1 min-w-0">
							<div class="text-sm font-medium text-white truncate">{s.filename || s.source_id}</div>
							<div class="text-xs text-gray-500 mt-0.5">
								{s.source_type} · агент: {s.for_agent || 'all'} · {s.chunk_count} чанков · {s.uploaded_at || '—'}
							</div>
						</div>
						<button
							type="button"
							onclick={() => removeSource(s.source_id)}
							class="p-2 text-gray-600 hover:text-red-400 text-sm shrink-0"
							aria-label="Удалить"
						>
							✕
						</button>
					</div>
				{/each}
			{/if}
		</div>
	</div>
</div>
