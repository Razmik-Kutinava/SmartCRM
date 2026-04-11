<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	// ── Провайдеры ───────────────────────────────────────────────────────────────
	let providers = $state({});
	onMount(async () => {
		try {
			const r = await fetch(`${API}/api/search/providers`);
			if (r.ok) providers = await r.json();
		} catch {}
	});

	// ── Табы ─────────────────────────────────────────────────────────────────────
	const TABS = [
		{ id: 'company',   label: 'Поиск по компании', icon: '🏢' },
		{ id: 'free',      label: 'Свободный запрос',  icon: '🔍' },
		{ id: 'prospect',  label: 'Проспектинг',       icon: '🎯' },
		{ id: 'enrich',    label: 'Обогащение лида',   icon: '✨' },
		{ id: 'rag',       label: 'Поиск для RAG',     icon: '📚' },
		{ id: 'agent',     label: 'Задача агенту',     icon: '🤖' },
	];
	let activeTab = $state('company');

	const AGENTS = [
		{ id: 'default',         label: 'Общий' },
		{ id: 'analyst',         label: 'Аналитик' },
		{ id: 'economist',       label: 'Экономист' },
		{ id: 'marketer',        label: 'Маркетолог' },
		{ id: 'tech_specialist', label: 'Тех. спец' },
		{ id: 'strategist',      label: 'Стратег' },
	];

	// ── Общий хелпер ─────────────────────────────────────────────────────────────
	async function post(endpoint, body) {
		const r = await fetch(`${API}${endpoint}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(body),
		});
		if (!r.ok) throw new Error(await r.text());
		return r.json();
	}

	// ── Поиск по компании ─────────────────────────────────────────────────────────
	let cs_company    = $state('');
	let cs_industry   = $state('');
	let cs_agent      = $state('default');
	let cs_force      = $state(false);
	let cs_running    = $state(false);
	let cs_result     = $state(null);
	let cs_err        = $state('');

	async function runCompanySearch() {
		if (!cs_company.trim() || cs_running) return;
		cs_running = true; cs_result = null; cs_err = '';
		try {
			cs_result = await post('/api/search/run', {
				company: cs_company.trim(), industry: cs_industry.trim(),
				agent: cs_agent, force: cs_force,
			});
		} catch (e) { cs_err = e.message; }
		finally { cs_running = false; }
	}

	// ── Свободный запрос ──────────────────────────────────────────────────────────
	let fq_query      = $state('');
	let fq_summarize  = $state(true);
	let fq_running    = $state(false);
	let fq_result     = $state(null);
	let fq_err        = $state('');

	async function runFreeSearch() {
		if (!fq_query.trim() || fq_running) return;
		fq_running = true; fq_result = null; fq_err = '';
		try {
			fq_result = await post('/api/search/ask', {
				query: fq_query.trim(), summarize: fq_summarize,
			});
		} catch (e) { fq_err = e.message; }
		finally { fq_running = false; }
	}

	// ── Проспектинг ───────────────────────────────────────────────────────────────
	let pr_icp        = $state('');
	let pr_industry   = $state('');
	let pr_city       = $state('');
	let pr_count      = $state(10);
	let pr_running    = $state(false);
	let pr_result     = $state(null);
	let pr_err        = $state('');
	let pr_adding     = $state(new Set());

	async function runProspect() {
		if (!pr_icp.trim() || pr_running) return;
		pr_running = true; pr_result = null; pr_err = '';
		try {
			pr_result = await post('/api/search/prospect', {
				icp: pr_icp.trim(), industry: pr_industry.trim(),
				city: pr_city.trim(), count: pr_count,
			});
		} catch (e) { pr_err = e.message; }
		finally { pr_running = false; }
	}

	async function addToCRM(company) {
		const idx = pr_result.companies.indexOf(company);
		pr_adding = new Set([...pr_adding, idx]);
		try {
			const r = await fetch(`${API}/api/leads`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					company: company.name,
					description: company.snippet || '',
					website: company.url || '',
					score: company.fit_score || 50,
				}),
			});
			if (r.ok) {
				const updated = [...pr_result.companies];
				updated[idx] = { ...company, _added: true };
				pr_result = { ...pr_result, companies: updated };
			}
		} catch {}
		pr_adding = new Set([...pr_adding].filter(i => i !== idx));
	}

	// ── Обогащение лида ───────────────────────────────────────────────────────────
	let en_company    = $state('');
	let en_industry   = $state('');
	let en_running    = $state(false);
	let en_result     = $state(null);
	let en_err        = $state('');

	async function runEnrich() {
		if (!en_company.trim() || en_running) return;
		en_running = true; en_result = null; en_err = '';
		try {
			en_result = await post('/api/search/enrich-lead', {
				lead: { company: en_company.trim(), industry: en_industry.trim() },
			});
		} catch (e) { en_err = e.message; }
		finally { en_running = false; }
	}

	// ── Поиск для RAG ─────────────────────────────────────────────────────────────
	let rg_query       = $state('');
	let rg_type        = $state('any');
	let rg_agent       = $state('all');
	let rg_running     = $state(false);
	let rg_result      = $state(null);
	let rg_err         = $state('');
	let rg_approved    = $state(new Set());

	// Шаги: 'select' → 'preview' → 'done'
	let rg_step        = $state('select');
	let rg_previewing  = $state(false);
	let rg_preview     = $state(null);   // данные dry_run ответа
	let rg_ingesting   = $state(false);
	let rg_ingest_msg  = $state('');
	let rg_ingest_ok   = $state(false);

	const RAG_AGENTS = [
		{ id: 'all',             label: 'Все агенты' },
		{ id: 'analyst',         label: 'Аналитик' },
		{ id: 'economist',       label: 'Экономист' },
		{ id: 'marketer',        label: 'Маркетолог' },
		{ id: 'tech_specialist', label: 'Тех. спец' },
		{ id: 'strategist',      label: 'Стратег' },
	];

	async function runRagSearch() {
		if (!rg_query.trim() || rg_running) return;
		rg_running = true; rg_result = null; rg_err = '';
		rg_approved = new Set();
		rg_step = 'select'; rg_preview = null; rg_ingest_msg = '';
		try {
			rg_result = await post('/api/search/find-for-rag', {
				query: rg_query.trim(), content_type: rg_type,
			});
		} catch (e) { rg_err = e.message; }
		finally { rg_running = false; }
	}

	function toggleApprove(i) {
		const next = new Set(rg_approved);
		if (next.has(i)) next.delete(i); else next.add(i);
		rg_approved = next;
	}

	function selectAllRag() {
		rg_approved = new Set((rg_result?.results || []).map((_, i) => i));
	}

	function ragDocs() {
		const items = (rg_result?.results || []).filter((_, i) => rg_approved.has(i));
		return items.map(r => ({
			text: [r.title, r.snippet].filter(Boolean).join('\n\n'),
			metadata: { source: r.url || r.source || '', title: r.title || '' },
		}));
	}

	// Шаг 1 → показать превью чанков (dry_run)
	async function previewChunks() {
		if (!rg_approved.size || rg_previewing) return;
		rg_previewing = true; rg_preview = null; rg_err = '';
		try {
			const resp = await fetch(`${API}/api/rag/ingest-batch`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ documents: ragDocs(), for_agent: rg_agent, tags: 'search', dry_run: true }),
			});
			const data = await resp.json();
			if (resp.ok && data.ok) {
				rg_preview = data;
				rg_step = 'preview';
			} else {
				rg_err = data.detail || 'Ошибка превью';
			}
		} catch (e) { rg_err = e.message; }
		finally { rg_previewing = false; }
	}

	// Шаг 2 → реальный ингест после апрува
	async function ingestApproved() {
		if (rg_ingesting) return;
		rg_ingesting = true; rg_ingest_msg = ''; rg_ingest_ok = false;
		try {
			const resp = await fetch(`${API}/api/rag/ingest-batch`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ documents: ragDocs(), for_agent: rg_agent, tags: 'search', dry_run: false }),
			});
			const data = await resp.json();
			if (resp.ok && data.ok) {
				rg_ingest_ok = true;
				const total_chunks = rg_preview?.total_chunks ?? '?';
				rg_ingest_msg = `Загружено ${data.ingested} документов · ~${total_chunks} чанков → RAG (агент: ${rg_agent})`;
				if (data.errors?.length) rg_ingest_msg += `. Ошибки: ${data.errors.join('; ')}`;
				rg_step = 'done';
				rg_approved = new Set();
			} else {
				rg_ingest_msg = data.detail || 'Ошибка загрузки';
				rg_ingest_ok = false;
			}
		} catch (e) {
			rg_ingest_msg = e.message; rg_ingest_ok = false;
		} finally {
			rg_ingesting = false;
		}
	}

	function ragReset() {
		rg_step = 'select'; rg_preview = null;
		rg_ingest_msg = ''; rg_ingest_ok = false;
	}

	// ── Задача агенту ──────────────────────────────────────────────────────────────
	let at_task       = $state('');
	let at_agent      = $state('analyst');
	let at_context    = $state('');
	let at_running    = $state(false);
	let at_result     = $state(null);
	let at_err        = $state('');

	async function runAgentTask() {
		if (!at_task.trim() || at_running) return;
		at_running = true; at_result = null; at_err = '';
		try {
			at_result = await post('/api/search/agent-task', {
				task: at_task.trim(), agent_id: at_agent, context: at_context.trim(),
			});
		} catch (e) { at_err = e.message; }
		finally { at_running = false; }
	}

	function scoreColor(s) {
		if (s >= 70) return 'text-green-400';
		if (s >= 40) return 'text-yellow-400';
		return 'text-red-400';
	}
</script>

<div class="flex flex-col h-full overflow-hidden">

	<!-- Header -->
	<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900 shrink-0">
		<div>
			<h1 class="text-lg font-semibold text-white">Поиск и разведка</h1>
			<p class="text-xs text-gray-500">Serper · Brave · Tavily — 6 режимов поиска</p>
		</div>
		<div class="flex gap-3 text-xs">
			{#each Object.entries(providers) as [key, p]}
				<span class="{p.key_set ? 'text-green-400' : 'text-red-400'}">
					{p.label} {p.key_set ? '✓' : '✗'}
				</span>
			{/each}
		</div>
	</div>

	<!-- Tabs -->
	<div class="flex border-b border-gray-800 bg-gray-900 shrink-0 px-4 overflow-x-auto">
		{#each TABS as tab}
			<button
				onclick={() => activeTab = tab.id}
				class="flex items-center gap-1.5 px-4 py-3 text-xs font-medium whitespace-nowrap border-b-2 transition-colors
					{activeTab === tab.id
						? 'border-indigo-500 text-white'
						: 'border-transparent text-gray-400 hover:text-gray-200'}"
			>
				<span>{tab.icon}</span>
				{tab.label}
			</button>
		{/each}
	</div>

	<!-- Content -->
	<div class="flex-1 overflow-y-auto p-6">
	<div class="max-w-3xl space-y-5">

	<!-- ═══ Поиск по компании ═══ -->
	{#if activeTab === 'company'}
		<div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
			<p class="text-xs text-gray-500">Найди всё о конкретной компании — новости, финансы, технологии, контакты</p>
			<div class="grid sm:grid-cols-2 gap-4">
				<div>
					<label class="block text-xs text-gray-500 mb-1">Название компании *</label>
					<input bind:value={cs_company} placeholder="ООО РетейлМаркет"
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500" />
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">Отрасль</label>
					<input bind:value={cs_industry} placeholder="ритейл, IT, строительство..."
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500" />
				</div>
			</div>
			<div class="flex items-center gap-4">
				<div class="flex-1">
					<label class="block text-xs text-gray-500 mb-1">Агент (тип запросов)</label>
					<select bind:value={cs_agent}
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white">
						{#each AGENTS as a}<option value={a.id}>{a.label}</option>{/each}
					</select>
				</div>
				<label class="flex items-center gap-2 text-sm text-gray-400 mt-5 cursor-pointer">
					<input type="checkbox" bind:checked={cs_force} class="accent-indigo-500" />
					Без кэша
				</label>
			</div>
			<button onclick={runCompanySearch} disabled={cs_running || !cs_company.trim()}
				class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-lg text-sm">
				{cs_running ? '⟳ Поиск...' : '🔍 Найти'}
			</button>
		</div>

		{#if cs_err}<div class="rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">{cs_err}</div>{/if}

		{#if cs_result}
			<!-- Шапка статусов -->
			<div class="flex flex-wrap items-center gap-2 text-xs">
				{#if cs_result.cached}
					<span class="px-2 py-0.5 bg-yellow-900/30 text-yellow-400 rounded-full">из кэша</span>
				{:else}
					<span class="px-2 py-0.5 bg-green-900/30 text-green-400 rounded-full">свежий</span>
				{/if}
				{#if cs_result.providers_used?.length}
					{#each cs_result.providers_used as p}
						<span class="px-2 py-0.5 bg-gray-800 text-gray-400 rounded-full">{p}</span>
					{/each}
				{/if}
				<span class="text-gray-600">Результатов: <span class="text-white">{cs_result.raw_results?.length ?? 0}</span></span>
			</div>

			<!-- Debug / pipeline stats (раскрывается) -->
			{#if !cs_result.cached && (cs_result.queries_used?.length || cs_result.total_raw)}
				<details class="group">
					<summary class="flex items-center gap-2 text-xs text-gray-600 cursor-pointer hover:text-gray-400 select-none list-none">
						<span class="group-open:rotate-90 transition-transform inline-block">▶</span>
						Детали пайплайна
					</summary>
					<div class="mt-2 bg-gray-950 border border-gray-800 rounded-xl p-4 space-y-3 text-xs">
						<!-- Запросы к провайдерам -->
						{#if cs_result.queries_used?.length}
							<div>
								<div class="text-gray-500 font-medium mb-1.5">Запросы к поисковикам</div>
								<div class="space-y-1">
									{#each cs_result.queries_used as q, i}
										<div class="flex items-start gap-2">
											<span class="text-gray-700 font-mono shrink-0">{i+1}.</span>
											<span class="text-gray-300 font-mono">{q}</span>
										</div>
									{/each}
								</div>
							</div>
						{/if}
						<!-- Воронка -->
						<div>
							<div class="text-gray-500 font-medium mb-1.5">Воронка обработки</div>
							<div class="flex items-center gap-2 flex-wrap">
								{#if cs_result.total_raw}
									<span class="px-2 py-1 bg-gray-800 rounded text-gray-300">Собрано: {cs_result.total_raw}</span>
									<span class="text-gray-700">→</span>
								{/if}
								{#if cs_result.total_after_dedup}
									<span class="px-2 py-1 bg-gray-800 rounded text-gray-300">После дедупл.: {cs_result.total_after_dedup}</span>
									<span class="text-gray-700">→</span>
								{/if}
								<span class="px-2 py-1 bg-indigo-900/40 rounded text-indigo-300 font-medium">Финал: {cs_result.raw_results?.length ?? 0}</span>
							</div>
						</div>
					</div>
				</details>
			{/if}

			<!-- Результаты -->
			<div class="space-y-3">
				{#each (cs_result.raw_results || []) as r, i}
					<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700">
						<div class="flex items-start justify-between gap-2 mb-1">
							<span class="text-xs font-mono text-gray-600">[{i+1}]</span>
							<span class="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400">{r.source}</span>
						</div>
						{#if r.title}<div class="text-sm font-medium text-white mb-1">{r.title}</div>{/if}
						{#if r.snippet}<div class="text-sm text-gray-300 leading-relaxed">{r.snippet}</div>{/if}
						<div class="flex items-center gap-3 mt-2 text-xs text-gray-600">
							{#if r.date}<span>{r.date}</span>{/if}
							{#if r.url}<a href={r.url} target="_blank" rel="noopener"
								class="text-indigo-400 hover:text-indigo-300 truncate max-w-xs">{r.url}</a>{/if}
						</div>
					</div>
				{/each}
			</div>

			<!-- Блок для промпта -->
			<details class="text-xs text-gray-600">
				<summary class="cursor-pointer hover:text-gray-400 list-none flex items-center gap-1">
					<span>▶</span> Блок для промпта агента
				</summary>
				<pre class="mt-2 overflow-x-auto rounded-lg bg-gray-950 px-4 py-3 text-gray-400 text-xs whitespace-pre-wrap">{cs_result.formatted_block}</pre>
			</details>
		{/if}

	<!-- ═══ Свободный запрос ═══ -->
	{:else if activeTab === 'free'}
		<div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
			<p class="text-xs text-gray-500">Задай любой вопрос — поиск по всем провайдерам, AI-ответ с источниками</p>
			<div>
				<label class="block text-xs text-gray-500 mb-1">Запрос *</label>
				<textarea bind:value={fq_query} rows="3" placeholder="Какие CRM-системы чаще всего используют в ритейле России?"
					class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 resize-none"></textarea>
			</div>
			<label class="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
				<input type="checkbox" bind:checked={fq_summarize} class="accent-indigo-500" />
				Сформировать AI-ответ на основе результатов
			</label>
			<button onclick={runFreeSearch} disabled={fq_running || !fq_query.trim()}
				class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-lg text-sm">
				{fq_running ? '⟳ Поиск...' : '🔍 Найти и ответить'}
			</button>
		</div>

		{#if fq_err}<div class="rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">{fq_err}</div>{/if}

		{#if fq_result}
			{#if fq_result.answer}
				<div class="bg-gray-900 border border-indigo-800/50 rounded-xl p-5">
					<div class="text-xs text-indigo-400 font-medium mb-3">AI-ответ</div>
					<div class="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">{fq_result.answer}</div>
				</div>
			{/if}
			<div class="text-xs text-gray-500">
				Провайдеры: {fq_result.providers_used?.join(', ') || '—'} · Результатов: {fq_result.raw_results?.length ?? 0}
			</div>
			<div class="space-y-3">
				{#each (fq_result.raw_results || []) as r, i}
					<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700">
						<div class="flex items-start justify-between gap-2 mb-1">
							<span class="text-xs font-mono text-gray-600">[{i+1}]</span>
							<span class="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400">{r.source}</span>
						</div>
						{#if r.title}<div class="text-sm font-medium text-white mb-1">{r.title}</div>{/if}
						{#if r.snippet}<div class="text-sm text-gray-300 leading-relaxed">{r.snippet}</div>{/if}
						<div class="flex gap-3 mt-2 text-xs text-gray-600">
							{#if r.date}<span>{r.date}</span>{/if}
							{#if r.url}<a href={r.url} target="_blank" rel="noopener"
								class="text-indigo-400 hover:text-indigo-300 truncate max-w-xs">{r.url}</a>{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}

	<!-- ═══ Проспектинг ═══ -->
	{:else if activeTab === 'prospect'}
		<div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
			<p class="text-xs text-gray-500">Опиши идеального клиента — AI найдёт подходящие компании и оценит их</p>
			<div>
				<label class="block text-xs text-gray-500 mb-1">Описание ICP (идеального клиента) *</label>
				<textarea bind:value={pr_icp} rows="3"
					placeholder="Торговые компании с оборотом от 100 млн руб, 20-200 сотрудников, отдел продаж 5+ человек, без CRM или с устаревшей системой"
					class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 resize-none"></textarea>
			</div>
			<div class="grid sm:grid-cols-3 gap-3">
				<div>
					<label class="block text-xs text-gray-500 mb-1">Отрасль</label>
					<input bind:value={pr_industry} placeholder="ритейл, производство..."
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white" />
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">Город</label>
					<input bind:value={pr_city} placeholder="Москва, СПб..."
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white" />
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">Количество</label>
					<input type="number" bind:value={pr_count} min="3" max="20"
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white" />
				</div>
			</div>
			<button onclick={runProspect} disabled={pr_running || !pr_icp.trim()}
				class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-lg text-sm">
				{pr_running ? '⟳ Ищу компании...' : '🎯 Найти потенциальных клиентов'}
			</button>
		</div>

		{#if pr_err}<div class="rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">{pr_err}</div>{/if}

		{#if pr_result}
			<div class="text-xs text-gray-500 mb-2">
				Запросы: {pr_result.queries_used?.join(' · ') || '—'} · Провайдеры: {pr_result.providers_used?.join(', ') || '—'}
			</div>
			{#if pr_result.companies?.length}
				<div class="space-y-3">
					{#each pr_result.companies as company, i}
						<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700">
							<div class="flex items-start justify-between gap-3 mb-2">
								<div class="flex-1">
									<div class="flex items-center gap-2 mb-1">
										<span class="text-sm font-semibold text-white">{company.name}</span>
										<span class="text-xs font-mono {scoreColor(company.fit_score || 0)}">
											{company.fit_score ?? '?'}%
										</span>
									</div>
									{#if company.fit_reason}
										<div class="text-xs text-indigo-300 mb-1">{company.fit_reason}</div>
									{/if}
									{#if company.snippet}
										<div class="text-xs text-gray-400">{company.snippet?.slice(0, 200)}</div>
									{/if}
									{#if company.url}
										<a href={company.url} target="_blank" rel="noopener"
											class="text-xs text-indigo-400 hover:text-indigo-300 mt-1 block">{company.url}</a>
									{/if}
								</div>
								<button
									onclick={() => addToCRM(company)}
									disabled={pr_adding.has(i) || company._added}
									class="shrink-0 px-3 py-1.5 text-xs rounded-lg font-medium transition-colors
										{company._added
											? 'bg-green-900/30 text-green-400 cursor-default'
											: 'bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white'}"
								>
									{company._added ? '✓ Добавлен' : pr_adding.has(i) ? '...' : '+ В CRM'}
								</button>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="text-sm text-gray-500 text-center py-8">Компании не найдены. Уточни ICP или отрасль.</div>
			{/if}
		{/if}

	<!-- ═══ Обогащение лида ═══ -->
	{:else if activeTab === 'enrich'}
		<div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
			<p class="text-xs text-gray-500">Введи компанию — AI найдёт телефоны, email, сайт, выручку, ЛПР и другие данные</p>
			<div class="grid sm:grid-cols-2 gap-4">
				<div>
					<label class="block text-xs text-gray-500 mb-1">Название компании *</label>
					<input bind:value={en_company} placeholder="ООО РетейлМаркет"
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500" />
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">Отрасль</label>
					<input bind:value={en_industry} placeholder="ритейл, IT..."
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white" />
				</div>
			</div>
			<button onclick={runEnrich} disabled={en_running || !en_company.trim()}
				class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-lg text-sm">
				{en_running ? '⟳ Ищу данные...' : '✨ Обогатить данные о компании'}
			</button>
		</div>

		{#if en_err}<div class="rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">{en_err}</div>{/if}

		{#if en_result}
			{@const enriched = en_result.enriched || {}}
			{@const keys = Object.keys(enriched)}
			{#if keys.length}
				<div class="bg-gray-900 border border-indigo-800/50 rounded-xl p-5">
					<div class="text-xs text-indigo-400 font-medium mb-3">Найденные данные</div>
					<div class="space-y-2">
						{#each keys as k}
							<div class="flex items-start gap-3 text-sm">
								<span class="text-gray-500 w-32 shrink-0">{k}</span>
								<span class="text-white">{enriched[k]}</span>
							</div>
						{/each}
					</div>
				</div>
			{:else}
				<div class="text-sm text-gray-500 text-center py-4">Данных не найдено. Попробуй уточнить название.</div>
			{/if}

			{#if en_result.missing_fields?.length}
				<div class="text-xs text-gray-600">
					Искали поля: {en_result.missing_fields.join(', ')}
				</div>
			{/if}

			{#if en_result.raw_results?.length}
				<details class="text-xs text-gray-600">
					<summary class="cursor-pointer hover:text-gray-400">{en_result.raw_results.length} источников</summary>
					<div class="mt-2 space-y-2">
						{#each (en_result.raw_results || []) as r, i}
							<div class="bg-gray-900 border border-gray-800 rounded-lg p-3">
								<div class="text-xs font-medium text-gray-300 mb-1">[{i+1}] {r.title}</div>
								<div class="text-xs text-gray-500">{r.snippet?.slice(0, 150)}</div>
								{#if r.url}<a href={r.url} target="_blank" rel="noopener" class="text-xs text-indigo-400">{r.url}</a>{/if}
							</div>
						{/each}
					</div>
				</details>
			{/if}
		{/if}

	<!-- ═══ Поиск для RAG ═══ -->
	{:else if activeTab === 'rag'}

		<!-- Форма поиска -->
		<div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
			<p class="text-xs text-gray-500">Найди статьи и документы → посмотри как разобьются на чанки → загрузи в базу знаний агента</p>
			<div>
				<label class="block text-xs text-gray-500 mb-1">Запрос *</label>
				<textarea bind:value={rg_query} rows="2" placeholder="лучшие практики B2B продаж в SaaS"
					class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 resize-none"></textarea>
			</div>
			<div class="grid sm:grid-cols-2 gap-3">
				<div>
					<label class="block text-xs text-gray-500 mb-1">Тип контента</label>
					<select bind:value={rg_type}
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white">
						<option value="any">Любой</option>
						<option value="article">Статьи</option>
						<option value="pdf">PDF-документы</option>
						<option value="docs">Документация</option>
					</select>
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">Агент-получатель</label>
					<select bind:value={rg_agent}
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white">
						{#each RAG_AGENTS as a}<option value={a.id}>{a.label}</option>{/each}
					</select>
				</div>
			</div>
			<button onclick={runRagSearch} disabled={rg_running || !rg_query.trim()}
				class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-lg text-sm">
				{rg_running ? '⟳ Поиск...' : '📚 Найти материалы'}
			</button>
		</div>

		{#if rg_err}<div class="rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">{rg_err}</div>{/if}

		<!-- ШАГ 1: список результатов, выбор документов -->
		{#if rg_result?.results?.length && rg_step === 'select'}

			<!-- Шаги-индикатор -->
			<div class="flex items-center gap-2 text-xs">
				<span class="px-2 py-0.5 rounded-full bg-indigo-600 text-white font-medium">1 Выбор</span>
				<span class="text-gray-700">──</span>
				<span class="px-2 py-0.5 rounded-full bg-gray-800 text-gray-500">2 Превью чанков</span>
				<span class="text-gray-700">──</span>
				<span class="px-2 py-0.5 rounded-full bg-gray-800 text-gray-500">3 Загрузка в RAG</span>
			</div>

			<div class="flex flex-wrap items-center justify-between gap-2">
				<div class="flex items-center gap-3 text-xs text-gray-500">
					<span>Найдено: {rg_result.results.length} · Выбрано: <span class="text-white font-medium">{rg_approved.size}</span></span>
					<button onclick={selectAllRag} class="text-indigo-400 hover:text-indigo-300">Выбрать все</button>
					{#if rg_approved.size > 0}
						<button onclick={() => rg_approved = new Set()} class="text-gray-500 hover:text-gray-300">Сбросить</button>
					{/if}
				</div>
				<button
					onclick={previewChunks}
					disabled={!rg_approved.size || rg_previewing}
					class="px-4 py-1.5 text-xs bg-indigo-700 hover:bg-indigo-600 disabled:opacity-40 text-white rounded-lg font-medium"
				>
					{rg_previewing ? '⟳ Анализирую...' : `Посмотреть чанки (${rg_approved.size} доков) →`}
				</button>
			</div>

			<div class="space-y-2">
				{#each rg_result.results as r, i}
					<div
						class="bg-gray-900 border rounded-xl p-4 cursor-pointer transition-colors
							{rg_approved.has(i) ? 'border-indigo-600 bg-indigo-950/20' : 'border-gray-800 hover:border-gray-700'}"
						onclick={() => toggleApprove(i)}
					>
						<div class="flex items-start gap-3">
							<div class="mt-0.5 shrink-0">
								<div class="w-4 h-4 rounded border-2 transition-colors flex items-center justify-center
									{rg_approved.has(i) ? 'border-indigo-500 bg-indigo-600' : 'border-gray-600'}">
									{#if rg_approved.has(i)}<span class="text-white text-xs leading-none">✓</span>{/if}
								</div>
							</div>
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2 mb-1">
									<span class="text-sm font-medium text-white">{r.title}</span>
									{#if r.is_pdf}<span class="text-xs px-1.5 py-0.5 bg-red-900/40 text-red-400 rounded">PDF</span>{/if}
									<span class="text-xs text-gray-600">{r.source}</span>
								</div>
								{#if r.snippet}<div class="text-xs text-gray-400 leading-relaxed">{r.snippet?.slice(0, 220)}</div>{/if}
								{#if r.url}
									<a href={r.url} target="_blank" rel="noopener"
										onclick={(e) => e.stopPropagation()}
										class="text-xs text-indigo-400 hover:text-indigo-300 mt-1 block truncate">{r.url}</a>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}

		<!-- ШАГ 2: превью чанков -->
		{#if rg_step === 'preview' && rg_preview}

			<!-- Шаги-индикатор -->
			<div class="flex items-center gap-2 text-xs">
				<span class="px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">1 Выбор</span>
				<span class="text-gray-700">──</span>
				<span class="px-2 py-0.5 rounded-full bg-indigo-600 text-white font-medium">2 Превью чанков</span>
				<span class="text-gray-700">──</span>
				<span class="px-2 py-0.5 rounded-full bg-gray-800 text-gray-500">3 Загрузка в RAG</span>
			</div>

			<!-- Сводка -->
			<div class="bg-gray-900 border border-indigo-800/40 rounded-xl p-4">
				<div class="flex items-center justify-between mb-3">
					<div>
						<div class="text-sm font-medium text-white">
							{rg_preview.ingested} документов · {rg_preview.total_chunks} чанков
						</div>
						<div class="text-xs text-gray-500 mt-0.5">Агент-получатель: <span class="text-indigo-400">{rg_agent}</span></div>
					</div>
					<div class="flex gap-2">
						<button onclick={ragReset}
							class="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg">
							← Назад
						</button>
						<button
							onclick={ingestApproved}
							disabled={rg_ingesting}
							class="px-4 py-1.5 text-xs bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white rounded-lg font-medium"
						>
							{rg_ingesting ? '⟳ Загружаю...' : `✓ Загрузить в RAG`}
						</button>
					</div>
				</div>
				{#if rg_preview.errors?.length}
					<div class="text-xs text-red-400 mt-1">Ошибки: {rg_preview.errors.join('; ')}</div>
				{/if}
			</div>

			<!-- Превью каждого документа -->
			<div class="space-y-3">
				{#each (rg_preview.previews || []) as doc}
					<div class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
						<div class="flex items-center justify-between px-4 py-3 border-b border-gray-800">
							<span class="text-sm font-medium text-white truncate">{doc.title}</span>
							<span class="shrink-0 ml-3 text-xs px-2 py-0.5 rounded-full bg-indigo-900/50 text-indigo-300">
								{doc.chunks} чанков
							</span>
						</div>
						<div class="divide-y divide-gray-800/60">
							{#each (doc.previews || []) as chunk, ci}
								<div class="px-4 py-2.5">
									<div class="flex items-center gap-2 mb-1">
										<span class="text-xs text-gray-600 font-mono">#{chunk.chunk_index ?? ci}</span>
										<span class="text-xs text-gray-600">{chunk.chars} символов</span>
									</div>
									<div class="text-xs text-gray-400 leading-relaxed">{chunk.snippet}</div>
								</div>
							{/each}
							{#if doc.chunks > (doc.previews?.length ?? 0)}
								<div class="px-4 py-2 text-xs text-gray-600 italic">
									... ещё {doc.chunks - (doc.previews?.length ?? 0)} чанков
								</div>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}

		<!-- ШАГ 3: результат загрузки -->
		{#if rg_step === 'done'}
			<div class="flex items-center gap-2 text-xs">
				<span class="px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">1 Выбор</span>
				<span class="text-gray-700">──</span>
				<span class="px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">2 Превью чанков</span>
				<span class="text-gray-700">──</span>
				<span class="px-2 py-0.5 rounded-full bg-emerald-700 text-white font-medium">3 Загружено</span>
			</div>
			<div class="bg-emerald-950/30 border border-emerald-800/40 rounded-xl p-5 space-y-3">
				<div class="text-sm font-medium text-emerald-400">✓ {rg_ingest_msg}</div>
				<button onclick={ragReset}
					class="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg">
					Загрузить ещё
				</button>
			</div>
		{/if}

	<!-- ═══ Задача агенту ═══ -->
	{:else if activeTab === 'agent'}
		<div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
			<p class="text-xs text-gray-500">Дай агенту задачу — он сам сформулирует запросы, найдёт данные и подготовит аналитику</p>
			<div>
				<label class="block text-xs text-gray-500 mb-1">Задача *</label>
				<textarea bind:value={at_task} rows="3"
					placeholder="Найди топ-5 конкурентов Сбербанка в сфере B2B кредитования и сравни их условия для малого бизнеса"
					class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 resize-none"></textarea>
			</div>
			<div class="grid sm:grid-cols-2 gap-4">
				<div>
					<label class="block text-xs text-gray-500 mb-1">Агент</label>
					<select bind:value={at_agent}
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white">
						{#each AGENTS as a}<option value={a.id}>{a.label}</option>{/each}
					</select>
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">Дополнительный контекст</label>
					<input bind:value={at_context} placeholder="регион Москва, сектор SMB..."
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white" />
				</div>
			</div>
			<button onclick={runAgentTask} disabled={at_running || !at_task.trim()}
				class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-lg text-sm">
				{at_running ? '⟳ Агент работает...' : '🤖 Поставить задачу агенту'}
			</button>
		</div>

		{#if at_err}<div class="rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">{at_err}</div>{/if}

		{#if at_result}
			{#if at_result.queries_used?.length}
				<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
					<div class="text-xs text-gray-500 font-medium mb-2">Поисковые запросы агента</div>
					<div class="space-y-1">
						{#each at_result.queries_used as q, i}
							<div class="text-xs text-gray-400 font-mono">
								<span class="text-gray-600">{i+1}.</span> {q}
							</div>
						{/each}
					</div>
					<div class="text-xs text-gray-600 mt-2">
						Провайдеры: {at_result.providers_used?.join(', ')} · Источников: {at_result.raw_results?.length ?? 0}
					</div>
				</div>
			{/if}

			{#if at_result.answer}
				<div class="bg-gray-900 border border-indigo-800/50 rounded-xl p-5">
					<div class="text-xs text-indigo-400 font-medium mb-3">Ответ агента «{at_agent}»</div>
					<div class="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">{at_result.answer}</div>
				</div>
			{/if}

			{#if at_result.raw_results?.length}
				<details class="text-xs text-gray-600">
					<summary class="cursor-pointer hover:text-gray-400">{at_result.raw_results.length} источников использовано</summary>
					<div class="mt-2 space-y-2">
						{#each (at_result.raw_results || []) as r, i}
							<div class="bg-gray-900 border border-gray-800 rounded-lg p-3">
								<div class="text-xs font-medium text-gray-300 mb-1">[{i+1}] {r.title}</div>
								<div class="text-xs text-gray-500">{r.snippet?.slice(0, 200)}</div>
								{#if r.url}<a href={r.url} target="_blank" rel="noopener" class="text-xs text-indigo-400">{r.url}</a>{/if}
							</div>
						{/each}
					</div>
				</details>
			{/if}
		{/if}

	{/if}

	</div>
	</div>
</div>
