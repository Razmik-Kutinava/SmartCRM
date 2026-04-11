<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	const AGENT_LABELS = {
		analyst: { label: 'Аналитик', icon: '📊', desc: 'Скоринг лидов, BANT-анализ, следующие шаги' },
		strategist: { label: 'Стратег', icon: '🧠', desc: 'Синтез решений, приоритет, финальный ответ' },
		economist: { label: 'Экономист', icon: '💰', desc: 'ROI, бюджетный анализ, финансовые прогнозы' },
		marketer: { label: 'Маркетолог', icon: '📣', desc: 'Персонализация, письма, 20 касаний' },
		tech_specialist: { label: 'Тех. спец', icon: '⚙️', desc: 'Технический стек, интеграции' },
	};

	let agents = $state([]);
	let loading = $state(true);
	let err = $state('');

	let selectedAgent = $state(null);
	let promptText = $state('');
	let promptSource = $state('builtin');
	let promptSaving = $state(false);
	let promptMsg = $state('');

	let testIntent = $state('analyze_lead');
	let testSlots = $state('{"company":"ООО Ромашка","contact":"Иван","city":"Москва","budget":"500000"}');
	let testRunning = $state(false);
	let testResult = $state(null);
	let testErr = $state('');

	const INTENTS = [
		'analyze_lead', 'create_lead', 'update_lead', 'delete_lead', 'list_leads',
		'create_task', 'list_tasks',
	];

	let leadsForTest = $state([]);
	let testLeadId = $state('');
	let testInstruction = $state('');
	let testAdvanced = $state(false);

	async function loadAgents() {
		err = '';
		loading = true;
		try {
			const r = await fetch(`${API}/api/ops/agents`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			agents = d.agents || [];
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	async function loadLeadsForTest() {
		try {
			const r = await fetch(`${API}/api/leads`);
			if (!r.ok) throw new Error();
			leadsForTest = await r.json();
		} catch {
			leadsForTest = [];
		}
	}

	async function selectAgent(agent) {
		selectedAgent = agent;
		promptMsg = '';
		testResult = null;
		testErr = '';
		testLeadId = '';
		testInstruction = '';
		testAdvanced = false;
		if (agent.implemented) loadLeadsForTest();
		try {
			const r = await fetch(`${API}/api/ops/agents/${agent.id}/prompt`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			promptText = d.prompt || '';
			promptSource = d.source || 'builtin';
		} catch (e) {
			promptText = '';
			promptMsg = `Ошибка загрузки: ${e instanceof Error ? e.message : e}`;
		}
	}

	async function savePrompt() {
		if (!selectedAgent) return;
		promptSaving = true;
		promptMsg = '';
		try {
			const r = await fetch(`${API}/api/ops/agents/${selectedAgent.id}/prompt`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ prompt: promptText }),
			});
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			promptSource = d.source;
			promptMsg = `✓ Сохранено (${d.chars} симв.)`;
			await loadAgents();
		} catch (e) {
			promptMsg = `Ошибка: ${e instanceof Error ? e.message : e}`;
		} finally {
			promptSaving = false;
		}
	}

	async function resetPrompt() {
		if (!selectedAgent) return;
		if (!confirm('Сбросить к встроенному промпту?')) return;
		promptSaving = true;
		promptMsg = '';
		try {
			const r = await fetch(`${API}/api/ops/agents/${selectedAgent.id}/prompt`, {
				method: 'DELETE',
			});
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			promptSource = d.source;
			promptMsg = 'Файл удалён, используется встроенный промпт.';
			await selectAgent(selectedAgent);
			await loadAgents();
		} catch (e) {
			promptMsg = `Ошибка: ${e instanceof Error ? e.message : e}`;
		} finally {
			promptSaving = false;
		}
	}

	async function runTest() {
		if (!selectedAgent) return;
		testRunning = true;
		testResult = null;
		testErr = '';

		let payload;
		if (!testAdvanced && testLeadId) {
			const id = Number(testLeadId);
			if (!Number.isFinite(id)) {
				testErr = 'Некорректный лид';
				testRunning = false;
				return;
			}
			const instr = testInstruction.trim();
			payload = {
				lead_id: id,
				instruction: instr,
				transcript: instr,
				slots: {},
				intent: 'analyze_lead',
			};
		} else if (testAdvanced) {
			let slots = {};
			try {
				slots = JSON.parse(testSlots || '{}');
			} catch {
				testErr = 'Неверный JSON в слотах';
				testRunning = false;
				return;
			}
			payload = { intent: testIntent, slots, transcript: testInstruction.trim() };
		} else {
			testErr = 'Выберите лид или включите расширенный режим';
			testRunning = false;
			return;
		}

		try {
			const r = await fetch(`${API}/api/ops/agents/${selectedAgent.id}/run`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload),
			});
			if (!r.ok) throw new Error(await r.text());
			testResult = await r.json();
		} catch (e) {
			testErr = e instanceof Error ? e.message : String(e);
		} finally {
			testRunning = false;
		}
	}

	function statusBadge(agent) {
		if (!agent.implemented) return 'bg-gray-800 text-gray-500';
		if (agent.source === 'override') return 'bg-indigo-900 text-indigo-300';
		return 'bg-emerald-900 text-emerald-300';
	}
	function statusLabel(agent) {
		if (!agent.implemented) return 'не реализован';
		return agent.source === 'override' ? 'override' : 'встроенный';
	}

	onMount(loadAgents);
</script>

<div class="px-6 py-6 max-w-6xl">
	<div class="flex items-center gap-3 mb-2">
		<span class="text-2xl">🤖</span>
		<h2 class="text-lg font-semibold text-white">Агенты и роли</h2>
	</div>
	<p class="text-sm text-gray-400 mb-6">
		Промпты PhD-уровня, тест-запуск и редактирование каждого агента.
		Изменения применяются без перезапуска сервера.
	</p>

	{#if err}
		<div class="mb-4 rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-2 text-sm text-red-200">{err}</div>
	{/if}

	<div class="grid gap-6 lg:grid-cols-[280px,1fr]">
		<!-- Список агентов -->
		<div class="space-y-2">
			{#if loading}
				<p class="text-sm text-gray-500">Загрузка…</p>
			{:else}
				{#each agents as agent}
					{@const meta = AGENT_LABELS[agent.id] || { label: agent.id, icon: '🤖', desc: '' }}
					<button
						type="button"
						onclick={() => selectAgent(agent)}
						class="w-full text-left rounded-xl border transition-colors px-4 py-3
							{selectedAgent?.id === agent.id
								? 'border-indigo-600 bg-indigo-950/40'
								: 'border-gray-800 bg-gray-900/50 hover:border-gray-600'}"
					>
						<div class="flex items-center justify-between mb-1">
							<span class="font-medium text-sm text-white">{meta.icon} {meta.label}</span>
							<span class="text-xs px-1.5 py-0.5 rounded {statusBadge(agent)}">{statusLabel(agent)}</span>
						</div>
						<p class="text-xs text-gray-500 leading-snug">{meta.desc}</p>
						{#if agent.implemented}
							<p class="text-xs text-gray-600 mt-1">{agent.prompt_chars} симв.</p>
						{/if}
					</button>
				{/each}
			{/if}
		</div>

		<!-- Редактор -->
		{#if selectedAgent}
			{@const meta = AGENT_LABELS[selectedAgent.id] || { label: selectedAgent.id, icon: '🤖' }}
			<div class="space-y-5">
				<div class="flex items-center justify-between">
					<h3 class="text-base font-semibold text-white">{meta.icon} {meta.label}</h3>
					<span class="text-xs px-2 py-0.5 rounded {promptSource === 'override' ? 'bg-indigo-900 text-indigo-300' : 'bg-gray-800 text-gray-400'}">
						{promptSource === 'override' ? '✏️ override' : '📦 встроенный'}
					</span>
				</div>

				{#if !selectedAgent.implemented}
					<div class="rounded-xl border border-gray-800 bg-gray-900/50 px-4 py-6 text-center text-sm text-gray-500">
						Агент ещё не реализован — промпт можно написать и сохранить заранее
					</div>
				{/if}

			<!-- Промпт редактор -->
			<div>
				<label for="agent-prompt" class="block text-xs font-medium uppercase tracking-wider text-gray-500 mb-1">
					Системный промпт
				</label>
				<textarea
					id="agent-prompt"
					bind:value={promptText}
					rows="18"
					spellcheck="false"
					class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-xs text-gray-100 font-mono focus:outline-none focus:border-indigo-500 resize-y"
				></textarea>
			</div>

				<div class="flex flex-wrap gap-2 items-center">
					<button
						type="button"
						onclick={savePrompt}
						disabled={promptSaving}
						class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
					>
						{promptSaving ? 'Сохранение…' : 'Сохранить промпт'}
					</button>
					<button
						type="button"
						onclick={resetPrompt}
						disabled={promptSaving || promptSource === 'builtin'}
						class="rounded-lg border border-gray-600 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 disabled:opacity-40"
					>
						Сбросить к встроенному
					</button>
					{#if promptMsg}
						<span class="text-sm {promptMsg.startsWith('✓') ? 'text-emerald-400' : 'text-red-400'}">{promptMsg}</span>
					{/if}
				</div>

				<!-- Тест-запуск -->
				{#if selectedAgent.implemented}
					<div class="rounded-xl border border-gray-800 bg-gray-900/50 p-4 space-y-3 mt-2">
						<h4 class="text-sm font-medium text-white">Тест-запуск агента</h4>
						<p class="text-xs text-gray-500">
							По умолчанию — лид из CRM и intent analyze_lead; аналитик может обновить скор в БД.
						</p>

						<label class="flex items-center gap-2 cursor-pointer text-xs text-gray-400">
							<input type="checkbox" bind:checked={testAdvanced} class="rounded border-gray-600" />
							Расширенный режим (интент + JSON)
						</label>

						{#if !testAdvanced}
							<div>
								<label class="block text-xs text-gray-500 mb-1">Лид</label>
								<select
									bind:value={testLeadId}
									class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-1.5 text-sm text-white"
								>
									<option value="">— выберите —</option>
									{#each leadsForTest as L}
										<option value={String(L.id)}>{L.company} · {L.stage || '—'}</option>
									{/each}
								</select>
							</div>
							<div>
								<label class="block text-xs text-gray-500 mb-1">Команда агенту (необязательно)</label>
								<input
									bind:value={testInstruction}
									class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-1.5 text-sm text-white"
									placeholder="Доп. указания…"
								/>
							</div>
						{:else}
							<div class="grid gap-3 sm:grid-cols-2">
								<div>
									<label class="block text-xs text-gray-500 mb-1">Интент</label>
									<select
										bind:value={testIntent}
										class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-1.5 text-sm text-white"
									>
										{#each INTENTS as i}
											<option value={i}>{i}</option>
										{/each}
									</select>
								</div>
								<div>
									<label for="test-slots" class="block text-xs text-gray-500 mb-1">Слоты (JSON)</label>
									<input
										id="test-slots"
										bind:value={testSlots}
										class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-1.5 text-sm text-white font-mono"
										placeholder={`{"company":"ООО Ромашка"}`}
									/>
								</div>
							</div>
						{/if}

						<button
							type="button"
							onclick={runTest}
							disabled={testRunning}
							class="rounded-lg bg-cyan-800 hover:bg-cyan-700 disabled:opacity-50 px-4 py-1.5 text-sm text-white"
						>
							{testRunning ? '⟳ Запуск…' : '▶ Запустить'}
						</button>

						{#if testErr}
							<div class="rounded-lg border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-200">{testErr}</div>
						{/if}

						{#if testResult}
							<div class="space-y-2">
								<div class="flex items-center gap-2 text-xs text-gray-500">
									<span>Время: {testResult.elapsed_ms} мс</span>
								</div>
								{#if testResult.output?.summary}
									<div class="rounded-lg border border-emerald-900/50 bg-emerald-950/20 px-3 py-2 text-sm text-emerald-200">
										{testResult.output.summary}
									</div>
								{/if}
								{#if testResult.output?.final_reply}
									<div class="rounded-lg border border-indigo-900/50 bg-indigo-950/20 px-3 py-2 text-sm text-indigo-200">
										{testResult.output.final_reply}
									</div>
								{/if}
								{#if testResult.output?.decision}
									<div class="rounded-lg border border-amber-900/50 bg-amber-950/20 px-3 py-2 text-xs text-amber-200">
										Решение: {testResult.output.decision}
									</div>
								{/if}
								<details class="text-xs text-gray-500">
									<summary class="cursor-pointer hover:text-gray-300">Полный вывод JSON</summary>
									<pre class="mt-2 overflow-x-auto rounded-lg bg-gray-950 px-3 py-2 text-gray-400">{JSON.stringify(testResult.output, null, 2)}</pre>
								</details>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{:else}
			<div class="flex items-center justify-center rounded-xl border border-gray-800 bg-gray-900/20 text-sm text-gray-600 min-h-[200px]">
				← Выберите агента слева
			</div>
		{/if}
	</div>
</div>
