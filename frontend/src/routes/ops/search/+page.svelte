<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	let cfg         = $state(null);
	let loading     = $state(true);
	let saving      = $state(false);
	let saveMsg     = $state('');
	let providers   = $state({});
	let cacheList   = $state([]);
	let clearingCache = $state(false);

	// Тест-поиск
	let testCompany  = $state('Сбербанк');
	let testAgent    = $state('analyst');
	let testIndustry = $state('финансы');
	let testRunning  = $state(false);
	let testResult   = $state(null);
	let testErr      = $state('');

	onMount(async () => {
		await Promise.all([loadConfig(), loadProviders(), loadCache()]);
	});

	async function loadConfig() {
		loading = true;
		try {
			const r = await fetch(`${API}/api/search/config`);
			if (r.ok) {
				const d = await r.json();
				cfg = d.config;
			}
		} catch {}
		loading = false;
	}

	async function loadProviders() {
		try {
			const r = await fetch(`${API}/api/search/providers`);
			if (r.ok) providers = await r.json();
		} catch {}
	}

	async function loadCache() {
		try {
			const r = await fetch(`${API}/api/search/cache`);
			if (r.ok) {
				const d = await r.json();
				cacheList = d.entries || [];
			}
		} catch {}
	}

	async function saveConfig() {
		saving = true;
		saveMsg = '';
		try {
			const r = await fetch(`${API}/api/search/config`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ config: cfg }),
			});
			saveMsg = r.ok ? 'Сохранено' : 'Ошибка сохранения';
		} catch {
			saveMsg = 'Ошибка сети';
		} finally {
			saving = false;
			setTimeout(() => saveMsg = '', 3000);
		}
	}

	async function clearCache() {
		clearingCache = true;
		try {
			const r = await fetch(`${API}/api/search/cache`, { method: 'DELETE' });
			if (r.ok) { cacheList = []; }
		} catch {}
		clearingCache = false;
	}

	async function runTest() {
		if (!testCompany.trim() || testRunning) return;
		testRunning = true;
		testResult  = null;
		testErr     = '';
		try {
			const r = await fetch(`${API}/api/search/run`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					company: testCompany.trim(),
					agent: testAgent,
					industry: testIndustry.trim(),
					force: true,
				}),
			});
			if (!r.ok) throw new Error(await r.text());
			testResult = await r.json();
			await loadCache();
		} catch (e) {
			testErr = e instanceof Error ? e.message : String(e);
		} finally {
			testRunning = false;
		}
	}

	const AGENTS = ['default','analyst','economist','marketer','tech_specialist'];
</script>

<div class="space-y-6">

	<div>
		<h2 class="text-lg font-semibold text-white mb-1">Настройка поиска</h2>
		<p class="text-xs text-gray-500">Провайдеры, реранкинг, кэш, шаблоны запросов под каждого агента</p>
	</div>

	{#if loading}
		<div class="text-sm text-gray-500">Загрузка...</div>
	{:else if cfg}

	<!-- Провайдеры -->
	<div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
		<h3 class="text-sm font-medium text-white mb-4">Провайдеры поиска</h3>
		<div class="space-y-4">
			{#each Object.entries(cfg.providers) as [pname, pcfg]}
				<div class="border border-gray-800 rounded-lg p-4">
					<div class="flex items-center justify-between mb-3">
						<div class="flex items-center gap-3">
							<label class="flex items-center gap-2 cursor-pointer">
								<input type="checkbox" bind:checked={pcfg.enabled} class="accent-indigo-500" />
								<span class="text-sm font-medium text-white capitalize">{pname}</span>
							</label>
							{#if providers[pname]}
								<span class="text-xs {providers[pname].key_set ? 'text-green-400' : 'text-red-400'}">
									{providers[pname].key_set ? '✓ ключ есть' : '✗ нет ключа'}
								</span>
							{/if}
						</div>
						<span class="text-xs text-gray-500">{providers[pname]?.label ?? pname}</span>
					</div>
					<div class="grid grid-cols-2 gap-3 text-xs">
						<div>
							<label class="block text-gray-500 mb-1">Вес (0.1–2.0)</label>
							<input
								type="number" min="0.1" max="2" step="0.1"
								bind:value={pcfg.weight}
								class="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1 text-white"
							/>
						</div>
						<div>
							<label class="block text-gray-500 mb-1">Макс. результатов</label>
							<input
								type="number" min="1" max="20"
								bind:value={pcfg.max_results}
								class="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1 text-white"
							/>
						</div>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- Общие настройки -->
	<div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
		<h3 class="text-sm font-medium text-white mb-4">Общие параметры</h3>
		<div class="grid sm:grid-cols-3 gap-4 text-xs">
			<div>
				<label class="block text-gray-500 mb-1">Фильтр даты (месяцев)</label>
				<input
					type="number" min="0" max="120"
					bind:value={cfg.date_filter_months}
					class="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1.5 text-white text-sm"
				/>
				<p class="text-gray-600 mt-1">0 = без фильтра</p>
			</div>
			<div>
				<label class="block text-gray-500 mb-1">Кэш (часов)</label>
				<input
					type="number" min="0" max="168"
					bind:value={cfg.cache_ttl_hours}
					class="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1.5 text-white text-sm"
				/>
			</div>
			<div>
				<label class="flex items-center gap-2 text-gray-400 cursor-pointer mt-5">
					<input type="checkbox" bind:checked={cfg.reranking.enabled} class="accent-indigo-500" />
					LLM-реранкинг
				</label>
				{#if cfg.reranking.enabled}
					<div class="mt-2">
						<label class="block text-gray-500 mb-1">Top-K после реранкинга</label>
						<input
							type="number" min="1" max="20"
							bind:value={cfg.reranking.top_k}
							class="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1 text-white"
						/>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- Шаблоны запросов -->
	<div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
		<h3 class="text-sm font-medium text-white mb-1">Шаблоны запросов</h3>
		<p class="text-xs text-gray-500 mb-4">
			Используй <code class="bg-gray-800 px-1 rounded">{'{company}'}</code> — будет подставлено название компании.
			Каждый агент получает свои целевые запросы.
		</p>
		<div class="space-y-4">
			{#each AGENTS as agentId}
				{@const templates = cfg.query_templates[agentId] || []}
				<div class="border border-gray-800 rounded-lg p-4">
					<div class="text-xs font-medium text-gray-300 mb-2 capitalize">{agentId}</div>
					<div class="space-y-2">
						{#each templates as tpl, ti}
							<div class="flex gap-2">
								<input
									bind:value={cfg.query_templates[agentId][ti]}
									class="flex-1 rounded border border-gray-700 bg-gray-950 px-2 py-1 text-xs text-white font-mono"
								/>
								<button
									onclick={() => cfg.query_templates[agentId] = templates.filter((_, i) => i !== ti)}
									class="px-2 py-1 text-xs text-red-400 hover:text-red-300"
								>✕</button>
							</div>
						{/each}
						<button
							onclick={() => cfg.query_templates[agentId] = [...templates, '{company} ']}
							class="text-xs text-indigo-400 hover:text-indigo-300"
						>+ добавить шаблон</button>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- Кнопка сохранить -->
	<div class="flex items-center gap-4">
		<button
			onclick={saveConfig}
			disabled={saving}
			class="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg"
		>
			{saving ? 'Сохранение...' : 'Сохранить конфиг'}
		</button>
		{#if saveMsg}
			<span class="text-sm {saveMsg === 'Сохранено' ? 'text-green-400' : 'text-red-400'}">{saveMsg}</span>
		{/if}
	</div>

	<!-- Кэш -->
	<div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
		<div class="flex items-center justify-between mb-3">
			<h3 class="text-sm font-medium text-white">Кэш поиска ({cacheList.length} записей)</h3>
			<button
				onclick={clearCache}
				disabled={clearingCache || !cacheList.length}
				class="px-3 py-1 text-xs bg-red-900/40 hover:bg-red-900/60 text-red-300 rounded disabled:opacity-50"
			>
				{clearingCache ? 'Очищаю...' : 'Очистить всё'}
			</button>
		</div>
		{#if cacheList.length}
			<div class="space-y-1">
				{#each cacheList as entry}
					<div class="flex items-center justify-between text-xs text-gray-500 py-1 border-b border-gray-800">
						<span class="font-mono text-gray-600">{entry.key}</span>
						<span>{entry.count} рез. · {entry.age_min} мин назад</span>
					</div>
				{/each}
			</div>
		{:else}
			<p class="text-xs text-gray-600">Кэш пуст</p>
		{/if}
	</div>

	<!-- Тест-поиск -->
	<div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
		<h3 class="text-sm font-medium text-white mb-1">Тест-поиск</h3>
		<p class="text-xs text-gray-500 mb-4">
			Полноценный тест вынесен в раздел «Поиск» — там показываются запросы к провайдерам,
			воронка (raw → dedup → rerank) и блок для промпта агента.
		</p>
		<div class="grid sm:grid-cols-3 gap-3 mb-3">
			<div>
				<label class="block text-xs text-gray-500 mb-1">Компания</label>
				<input
					bind:value={testCompany}
					class="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1.5 text-sm text-white"
				/>
			</div>
			<div>
				<label class="block text-xs text-gray-500 mb-1">Отрасль</label>
				<input
					bind:value={testIndustry}
					class="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1.5 text-sm text-white"
				/>
			</div>
			<div>
				<label class="block text-xs text-gray-500 mb-1">Агент</label>
				<select bind:value={testAgent}
					class="w-full rounded border border-gray-700 bg-gray-950 px-2 py-1.5 text-sm text-white">
					{#each AGENTS as a}
						<option value={a}>{a}</option>
					{/each}
				</select>
			</div>
		</div>
		<div class="flex gap-2">
			<button
				onclick={runTest}
				disabled={testRunning}
				class="flex-1 py-2 bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white text-sm rounded-lg"
			>
				{testRunning ? '⟳ Поиск...' : '▶ Быстрый тест (force=true)'}
			</button>
			<a
				href="/search"
				class="px-4 py-2 bg-indigo-700 hover:bg-indigo-600 text-white text-sm rounded-lg whitespace-nowrap"
			>
				→ Полный поиск
			</a>
		</div>

		{#if testErr}
			<div class="text-sm text-red-300 bg-red-950/30 border border-red-900/40 rounded px-3 py-2 mt-3">{testErr}</div>
		{/if}

		{#if testResult}
			<div class="mt-3 space-y-2 text-xs">
				<!-- Запросы к провайдерам -->
				{#if testResult.queries_used?.length}
					<div class="bg-gray-950 border border-gray-800 rounded-lg p-3">
						<div class="text-gray-500 font-medium mb-1.5">Запросы к поисковикам</div>
						{#each testResult.queries_used as q, i}
							<div class="text-gray-400 font-mono">{i+1}. {q}</div>
						{/each}
					</div>
				{/if}
				<!-- Воронка -->
				<div class="flex items-center gap-2 flex-wrap text-gray-500">
					{#if testResult.total_raw}
						<span>Собрано: <span class="text-gray-300">{testResult.total_raw}</span></span>
						<span>→</span>
					{/if}
					{#if testResult.total_after_dedup}
						<span>Дедупл.: <span class="text-gray-300">{testResult.total_after_dedup}</span></span>
						<span>→</span>
					{/if}
					<span>Финал: <span class="text-white font-medium">{testResult.raw_results?.length ?? 0}</span></span>
					<span>· Провайдеры: <span class="text-gray-300">{testResult.providers_used?.join(', ') || '—'}</span></span>
				</div>
				<!-- Результаты -->
				{#each (testResult.raw_results || []) as r, i}
					<div class="border border-gray-800 rounded-lg p-3">
						<div class="flex justify-between mb-1">
							<span class="text-gray-400 font-medium">[{i+1}] {r.title}</span>
							<span class="text-gray-600">{r.source}</span>
						</div>
						<p class="text-gray-400">{r.snippet?.slice(0, 200)}</p>
						{#if r.date}<span class="text-gray-600">{r.date}</span>{/if}
					</div>
				{/each}
			</div>
		{/if}
	</div>

	{/if}
</div>
