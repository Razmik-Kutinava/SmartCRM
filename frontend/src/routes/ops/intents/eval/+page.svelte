<script>
	import { getApiUrl } from '$lib/websocket.js';
	import { intentColor, modelLabel } from '$lib/opsCommon.js';

	const API = getApiUrl();

	let evalResults = $state(null);
	let evalRunning = $state(false);
	/** По умолчанию только локальный Hermes3 — без расхода токенов Groq */
	let includeGroq = $state(false);
	/** @type {'builtin' | 'db_approved' | 'builtin_and_db'} */
	let scenarioSource = $state('builtin');

	let preview = $state(null);
	let previewLoading = $state(false);

	function modelsForRun() {
		const m = ['hermes3'];
		if (includeGroq) m.push('groq');
		return m;
	}

	async function loadPreview() {
		previewLoading = true;
		try {
			const r = await fetch(`${API}/api/ops/eval/preview?scenario_source=${scenarioSource}`);
			preview = await r.json();
		} catch (e) {
			console.error('preview', e);
			preview = { count: 0, cases: [], warning: String(e) };
		} finally {
			previewLoading = false;
		}
	}

	async function runEval() {
		evalRunning = true;
		evalResults = null;
		try {
			const r = await fetch(`${API}/api/ops/eval`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ models: modelsForRun(), scenario_source: scenarioSource })
			});
			evalResults = await r.json();
		} catch (e) {
			console.error('eval error', e);
		} finally {
			evalRunning = false;
		}
	}

	$effect(() => {
		scenarioSource;
		loadPreview();
	});
</script>

<div class="px-6 py-6">
	<p class="text-sm text-gray-400 mb-4 max-w-2xl">
		Сначала смотрите список фраз ниже — именно они пойдут в прогон. По умолчанию вызывается только <strong class="text-gray-300"
			>Hermes3 (Ollama)</strong
		>, без Groq API. Включите Groq для сравнения с облаком (расход токенов × число фраз).
	</p>

	<div class="mb-4 flex flex-wrap items-center gap-3">
		<span class="text-sm text-gray-400">Набор:</span>
		<select
			bind:value={scenarioSource}
			class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-100"
		>
			<option value="builtin">Только встроенные фразы</option>
			<option value="db_approved">Только утверждённые в БД</option>
			<option value="builtin_and_db">Встроенные + БД</option>
		</select>
		{#if previewLoading}
			<span class="text-xs text-gray-500">Обновление списка…</span>
		{/if}
	</div>

	<!-- Превью: что будет протестировано -->
	<div class="mb-6 bg-gray-900/80 border border-gray-800 rounded-xl p-4 max-h-64 overflow-y-auto">
		<h3 class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Что уйдёт в eval ({preview?.count ?? 0} фраз)</h3>
		{#if preview?.warning}
			<p class="text-sm text-amber-400 mb-2">{preview.warning}</p>
		{/if}
		{#if preview?.cases?.length}
			<ul class="text-sm text-gray-300 space-y-1.5 font-mono text-xs">
				{#each preview.cases as c, i}
					<li class="border-b border-gray-800/80 pb-1">
						<span class="text-gray-600">{i + 1}.</span>
						{c.scenario_id != null ? `#${c.scenario_id} ` : ''}"{c.text?.slice(0, 120)}{c.text?.length > 120 ? '…' : ''}"
						<span class="text-indigo-400">→ {c.expected}</span>
					</li>
				{/each}
			</ul>
		{:else if !previewLoading}
			<p class="text-sm text-gray-500">Нет кейсов для выбранного источника.</p>
		{/if}
	</div>

	<div class="mb-4 flex flex-wrap items-center gap-4">
		<label class="flex items-center gap-2 cursor-pointer">
			<input type="checkbox" bind:checked={includeGroq} class="accent-indigo-500" />
			<span class="text-sm text-gray-300">Добавить Groq (облако, токены API)</span>
		</label>
		<span class="text-xs text-gray-600">Модели прогона: {modelsForRun().join(', ')}</span>
	</div>

	<div class="mb-4 flex flex-wrap items-center gap-4">
		<button
			type="button"
			onclick={runEval}
			disabled={evalRunning || !preview?.count}
			class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm rounded-lg"
		>
			{evalRunning ? 'Тестируем…' : 'Запустить eval'}
		</button>
		{#if evalResults}
			<span class="text-sm text-gray-400">{evalResults.cases_count} кейсов</span>
			{#if evalResults.scenario_source}
				<span class="text-xs text-gray-500">· источник: {evalResults.scenario_source}</span>
			{/if}
		{/if}
	</div>

	{#if evalResults}
		{@const evalModels = modelsForRun()}
		<div class="grid grid-cols-2 gap-3 mb-4 max-w-2xl">
			{#each Object.entries(evalResults.summary) as [model, s]}
				<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
					<div class="font-medium text-white mb-2">{modelLabel(model)}</div>
					<div
						class="text-3xl font-bold {s.accuracy_pct >= 80
							? 'text-emerald-400'
							: s.accuracy_pct >= 60
								? 'text-amber-400'
								: 'text-red-400'}"
					>
						{s.accuracy_pct}%
					</div>
					<div class="text-xs text-gray-500 mt-1">
						{s.correct}/{s.total} верно · {s.avg_ms}ms среднее
					</div>
				</div>
			{/each}
		</div>

		<div class="bg-gray-900 rounded-xl border border-gray-800 overflow-x-auto">
			<table class="w-full text-sm min-w-[640px]">
				<thead class="bg-gray-800 text-gray-400 text-xs">
					<tr>
						<th class="px-4 py-2 text-left w-16">#</th>
						<th class="px-4 py-2 text-left">Команда</th>
						<th class="px-4 py-2 text-left">Ожидалось</th>
						{#each evalModels as model}
							<th class="px-4 py-2 text-left">{modelLabel(model)}</th>
						{/each}
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-800">
					{#each evalResults.results as row}
						<tr class="hover:bg-gray-800/50">
							<td class="px-4 py-3 text-gray-500 text-xs font-mono">
								{row.scenario_id ?? '—'}
							</td>
							<td class="px-4 py-3 text-gray-200 max-w-xs">
								<div class="truncate" title={row.text}>"{row.text}"</div>
							</td>
							<td class="px-4 py-3">
								{#if row.expected}
									<span class="text-xs px-1.5 py-0.5 rounded {intentColor(row.expected)}">{row.expected}</span>
								{:else}
									<span class="text-gray-600">—</span>
								{/if}
							</td>
							{#each evalModels as model}
								{@const m = row.models[model]}
								<td class="px-4 py-3">
									{#if m?.error}
										<span class="text-xs text-red-400 truncate">{m.error.slice(0, 60)}</span>
									{:else if m}
										<div class="flex items-center gap-1.5 flex-wrap">
											{#if m.correct === true}
												<span class="text-emerald-400 text-xs">✓</span>
											{:else if m.correct === false}
												<span class="text-red-400 text-xs">✗</span>
											{/if}
											<span class="text-xs px-1.5 py-0.5 rounded {intentColor(m.intent)}">{m.intent || '?'}</span>
											<span class="text-xs text-gray-600">{m.duration_ms}ms</span>
										</div>
									{:else}
										<span class="text-gray-600">—</span>
									{/if}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else if !evalRunning}
		<div class="text-center text-gray-500 py-8">Выберите набор и нажмите «Запустить eval».</div>
	{/if}

	{#if evalRunning}
		<div class="text-center py-8 text-gray-400 border border-gray-800 rounded-xl">
			Идёт прогон {preview?.count ?? '…'} фраз через {modelsForRun().join(' + ')}…
		</div>
	{/if}
</div>
