<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	const AGENT_META = {
		analyst: {
			name: 'Аналитик', icon: '📊',
			desc: 'BANT-анализ лидов, скоринг 0–100, следующие шаги, риски',
			color: 'indigo',
			intents: ['analyze_lead', 'create_lead', 'update_lead', 'list_leads'],
		},
		strategist: {
			name: 'Стратег', icon: '🧠',
			desc: 'Синтез решений, приоритет сделки, Challenger Sale, финальный ответ',
			color: 'purple',
			intents: ['analyze_lead', 'create_lead', 'update_lead'],
		},
		economist: {
			name: 'Экономист', icon: '💰',
			desc: 'ROI / LTV / CAC, оценка бюджета, вероятность сделки, ценообразование',
			color: 'emerald',
			intents: ['analyze_lead', 'create_lead', 'update_lead', 'list_leads'],
		},
		marketer: {
			name: 'Маркетолог', icon: '📣',
			desc: 'ABM-стратегия, персональное письмо, план 20 касаний, психология клиента',
			color: 'pink',
			intents: ['create_lead', 'write_email', 'analyze_lead'],
		},
		tech_specialist: {
			name: 'Тех. спец', icon: '⚙️',
			desc: 'IT-стек клиента, зрелость, интеграционные риски, пресейл-вопросы',
			color: 'cyan',
			intents: ['analyze_lead', 'create_lead', 'update_lead'],
		},
	};

	let agents = $state([]);
	let loading = $state(true);
	let err = $state('');

	let activeAgent = $state(null);
	let taskIntent = $state('analyze_lead');
	let taskSlots = $state('{"company":"ООО Ромашка","contact":"Иван Петров","city":"Москва","industry":"строительство","budget":"800000"}');
	let taskRunning = $state(false);
	let taskResult = $state(null);
	let taskErr = $state('');
	let showTask = $state(false);

	/** Список лидов для выбора в модалке */
	let leadsForTask = $state([]);
	let taskLeadId = $state('');
	let taskInstruction = $state('');
	let taskAdvanced = $state(false);

	async function loadAgents() {
		err = '';
		loading = true;
		try {
			const r = await fetch(`${API}/api/ops/agents`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			agents = (d.agents || []).map(a => ({
				...a,
				...AGENT_META[a.id],
			}));
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	async function loadLeadsForTask() {
		try {
			const r = await fetch(`${API}/api/leads`);
			if (!r.ok) throw new Error(await r.text());
			leadsForTask = await r.json();
		} catch {
			leadsForTask = [];
		}
	}

	function openTask(agent) {
		activeAgent = agent;
		taskIntent = agent.intents?.includes('analyze_lead')
			? 'analyze_lead'
			: agent.intents?.[0] || 'create_lead';
		taskResult = null;
		taskErr = '';
		taskLeadId = '';
		taskInstruction = '';
		taskAdvanced = false;
		showTask = true;
		loadLeadsForTask();
	}

	function closeTask() {
		showTask = false;
		activeAgent = null;
		taskResult = null;
		taskErr = '';
	}

	async function runTask() {
		if (!activeAgent || taskRunning) return;
		taskRunning = true;
		taskResult = null;
		taskErr = '';

		let payload;

		if (!taskAdvanced && taskLeadId) {
			const id = Number(taskLeadId);
			if (!Number.isFinite(id)) {
				taskErr = 'Некорректный лид';
				taskRunning = false;
				return;
			}
			const instr = taskInstruction.trim();
			payload = {
				lead_id: id,
				instruction: instr,
				transcript: instr,
				slots: {},
				intent: 'analyze_lead',
			};
		} else if (taskAdvanced) {
			let slots = {};
			try {
				slots = JSON.parse(taskSlots || '{}');
			} catch {
				taskErr = 'Неверный JSON в полях задачи';
				taskRunning = false;
				return;
			}
			payload = { intent: taskIntent, slots, transcript: taskInstruction.trim() };
		} else {
			taskErr = 'Выберите лид из списка или включите расширенный режим';
			taskRunning = false;
			return;
		}

		try {
			const r = await fetch(`${API}/api/ops/agents/${activeAgent.id}/run`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload),
			});
			if (!r.ok) throw new Error(await r.text());
			taskResult = await r.json();
		} catch (e) {
			taskErr = e instanceof Error ? e.message : String(e);
		} finally {
			taskRunning = false;
		}
	}

	function agentColorBg(color) {
		const map = {
			indigo: 'bg-indigo-600',
			purple: 'bg-purple-600',
			emerald: 'bg-emerald-600',
			pink: 'bg-pink-600',
			cyan: 'bg-cyan-600',
		};
		return map[color] || 'bg-gray-600';
	}

	function agentColorBorder(color) {
		const map = {
			indigo: 'border-indigo-600',
			purple: 'border-purple-600',
			emerald: 'border-emerald-600',
			pink: 'border-pink-600',
			cyan: 'border-cyan-600',
		};
		return map[color] || 'border-gray-600';
	}

	onMount(loadAgents);
</script>

<div class="flex flex-col h-full overflow-hidden">

	<!-- Header -->
	<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900 shrink-0">
		<div>
			<h1 class="text-lg font-semibold text-white">Агенты</h1>
			<p class="text-xs text-gray-500">5 AI-агентов · LangGraph · параллельная оркестрация</p>
		</div>
		<a href="/ops/agents" class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">
			⚙️ Редактировать промпты
		</a>
	</div>

	<!-- Список агентов -->
	<div class="flex-1 overflow-y-auto p-6">
		{#if err}
			<div class="mb-4 rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-2 text-sm text-red-200">{err}</div>
		{/if}

		{#if loading}
			<div class="space-y-3">
				{#each Array(5) as _}
					<div class="bg-gray-900 border border-gray-800 rounded-xl p-5 animate-pulse h-28"></div>
				{/each}
			</div>
		{:else}
			<div class="grid grid-cols-1 gap-4 max-w-3xl">
				{#each agents as agent}
					<div class="bg-gray-900 border {agentColorBorder(agent.color)}/30 hover:border-{agent.color}-500/60 rounded-xl p-5 transition-all duration-200 border">
						<div class="flex items-start justify-between mb-3">
							<div class="flex items-center gap-3">
								<div class="w-10 h-10 rounded-xl {agentColorBg(agent.color)} flex items-center justify-center text-lg shrink-0">
									{agent.icon || '🤖'}
								</div>
								<div>
									<div class="font-semibold text-white">{agent.name}</div>
									<div class="text-xs text-gray-500 mt-0.5 max-w-sm">{agent.desc}</div>
								</div>
							</div>
							<div class="flex items-center gap-1.5 shrink-0 ml-4">
								{#if agent.implemented}
									<div class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
									<span class="text-xs text-green-400">активен</span>
								{:else}
									<div class="w-2 h-2 rounded-full bg-gray-600"></div>
									<span class="text-xs text-gray-500">не реализован</span>
								{/if}
							</div>
						</div>

						<div class="flex items-center gap-3 mb-3 text-xs text-gray-600">
							<span>Промпт:
								<span class="{agent.source === 'override' ? 'text-indigo-400' : 'text-gray-400'}">
									{agent.source === 'override' ? '✏️ кастомный' : '📦 встроенный'}
								</span>
							</span>
							<span>{agent.prompt_chars} симв.</span>
							{#if agent.intents?.length}
								<span class="text-gray-700">·</span>
								<span>интенты: {agent.intents.join(', ')}</span>
							{/if}
						</div>

						<div class="flex gap-2">
							{#if agent.implemented}
								<button
									type="button"
									onclick={() => openTask(agent)}
									class="px-3 py-1.5 {agentColorBg(agent.color)} hover:opacity-90 text-xs text-white rounded-lg transition-colors"
								>
									▶ Поставить задачу
								</button>
							{/if}
							<a
								href="/ops/agents"
								class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-xs text-gray-300 rounded-lg transition-colors"
							>
								Промпт
							</a>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>

</div>

<!-- Модальное окно задачи -->
{#if showTask && activeAgent}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
		role="dialog"
		aria-modal="true"
	>
		<div class="w-full max-w-2xl mx-4 bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl">

			<!-- Шапка -->
			<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
				<div class="flex items-center gap-3">
					<div class="w-9 h-9 rounded-xl {agentColorBg(activeAgent.color)} flex items-center justify-center text-base">
						{activeAgent.icon}
					</div>
					<div>
						<div class="font-semibold text-white">Задача для агента: {activeAgent.name}</div>
						<div class="text-xs text-gray-500">
							{#if taskAdvanced}
								Ручной интент и JSON — для отладки
							{:else}
								Данные лида из CRM; аналитик может обновить скор в БД
							{/if}
						</div>
					</div>
				</div>
				<button onclick={closeTask} class="text-gray-500 hover:text-white text-xl leading-none">✕</button>
			</div>

			<div class="px-6 py-5 space-y-4">
				<label class="flex items-center gap-2 cursor-pointer text-sm text-gray-400 hover:text-gray-300">
					<input type="checkbox" bind:checked={taskAdvanced} class="rounded border-gray-600" />
					Расширенный режим (интент + JSON вручную)
				</label>

				{#if !taskAdvanced}
					<div>
						<label for="modal-lead" class="block text-xs text-gray-500 mb-1">Лид из CRM</label>
						<select
							id="modal-lead"
							bind:value={taskLeadId}
							class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
						>
							<option value="">— выберите компанию —</option>
							{#each leadsForTask as L}
								<option value={String(L.id)}>{L.company} · {L.stage || '—'} · скор {L.score ?? '—'}</option>
							{/each}
						</select>
						{#if leadsForTask.length === 0}
							<p class="text-xs text-amber-600/90 mt-1">Лидов нет — создайте в разделе «Лиды» или включите расширенный режим.</p>
						{/if}
					</div>

					<div>
						<label for="modal-instr" class="block text-xs text-gray-500 mb-1">Команда агенту (необязательно)</label>
						<textarea
							id="modal-instr"
							bind:value={taskInstruction}
							rows="2"
							placeholder="Например: сфокусируйся на сроках и ЛПР"
							class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-indigo-500"
						></textarea>
					</div>
				{:else}
					<div class="grid gap-4 sm:grid-cols-2">
						<div>
							<label for="modal-intent" class="block text-xs text-gray-500 mb-1">Интент</label>
							<select
								id="modal-intent"
								bind:value={taskIntent}
								class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
							>
								{#each (activeAgent.intents || ['create_lead']) as intent}
									<option value={intent}>{intent}</option>
								{/each}
							</select>
						</div>
						<div class="text-xs text-gray-500 pt-5">
							Как в ответе Hermes: интент и слоты вручную.
						</div>
					</div>

					<div>
						<label for="modal-slots" class="block text-xs text-gray-500 mb-1">Слоты (JSON)</label>
						<textarea
							id="modal-slots"
							bind:value={taskSlots}
							rows="4"
							spellcheck="false"
							class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-indigo-500"
						></textarea>
					</div>

					<div>
						<label for="modal-instr-adv" class="block text-xs text-gray-500 mb-1">Транскрипт / команда (необязательно)</label>
						<textarea
							id="modal-instr-adv"
							bind:value={taskInstruction}
							rows="2"
							class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
						></textarea>
					</div>
				{/if}

				<button
					type="button"
					onclick={runTask}
					disabled={taskRunning}
					class="w-full py-2.5 {agentColorBg(activeAgent.color)} hover:opacity-90 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
				>
					{taskRunning ? '⟳ Агент работает…' : `▶ Запустить ${activeAgent.name}`}
				</button>

				{#if taskErr}
					<div class="rounded-lg border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-200">{taskErr}</div>
				{/if}

				{#if taskResult}
					<div class="space-y-3">
						<div class="flex items-center gap-3 text-xs text-gray-500">
							<span class="text-emerald-400">✓ Выполнено за {taskResult.elapsed_ms} мс</span>
						</div>

						{#if taskResult.output}
							{@const out = taskResult.output}

							<!-- Ключевые результаты -->
							<div class="space-y-2">
								{#if out.summary}
									<div class="rounded-lg bg-gray-800 px-4 py-3 text-sm text-gray-100 border border-gray-700">
										<span class="text-xs text-gray-500 block mb-1">Резюме</span>
										{out.summary}
									</div>
								{/if}
								{#if out.final_reply}
									<div class="rounded-lg bg-indigo-950/50 border border-indigo-800/50 px-4 py-3 text-sm text-indigo-100">
										<span class="text-xs text-indigo-400 block mb-1">Финальный ответ</span>
										{out.final_reply}
									</div>
								{/if}
								{#if out.decision}
									<div class="rounded-lg bg-amber-950/30 border border-amber-800/30 px-4 py-3 text-sm text-amber-100">
										<span class="text-xs text-amber-400 block mb-1">Решение</span>
										{out.decision}
									</div>
								{/if}
								{#if out.next_action}
									<div class="rounded-lg bg-emerald-950/30 border border-emerald-800/30 px-4 py-3 text-sm text-emerald-100">
										<span class="text-xs text-emerald-400 block mb-1">Следующий шаг</span>
										{out.next_action}
									</div>
								{/if}
								{#if out.coach_tip}
									<div class="rounded-lg bg-gray-800/60 px-4 py-2 text-xs text-gray-400 italic">
										💡 {out.coach_tip}
									</div>
								{/if}

								<!-- BANT (аналитик) -->
								{#if out.bant}
									<div class="grid grid-cols-2 gap-2 text-xs">
										{#each Object.entries(out.bant) as [k, v]}
											<div class="bg-gray-800 rounded-lg px-3 py-2">
												<span class="text-gray-500 uppercase">{k}</span>
												<div class="text-gray-200 mt-0.5">{v}</div>
											</div>
										{/each}
									</div>
								{/if}

								<!-- Скор -->
								{#if out.score != null}
									<div class="flex items-center gap-3">
										<span class="text-xs text-gray-500">Скор лида:</span>
										<span class="text-2xl font-bold {out.score >= 70 ? 'text-green-400' : out.score >= 50 ? 'text-yellow-400' : 'text-red-400'}">
											{out.score}/100
										</span>
									</div>
								{/if}

								<!-- Письмо (маркетолог) -->
								{#if out.first_email}
									<div class="rounded-lg border border-pink-800/40 bg-pink-950/20 px-4 py-3 space-y-1">
										<div class="text-xs text-pink-400">Первое письмо</div>
										<div class="text-xs text-gray-300 font-medium">Тема: {out.first_email.subject}</div>
										<div class="text-xs text-gray-400 whitespace-pre-wrap">{out.first_email.body}</div>
									</div>
								{/if}

								<!-- Финансы (экономист) -->
								{#if out.budget_estimate || out.deal_probability_pct != null}
									<div class="grid grid-cols-3 gap-2 text-xs">
										{#if out.budget_estimate}
											<div class="bg-gray-800 rounded-lg px-3 py-2 text-center">
												<div class="text-gray-500">Бюджет</div>
												<div class="text-emerald-300 font-medium mt-0.5">{out.budget_estimate}</div>
											</div>
										{/if}
										{#if out.deal_segment}
											<div class="bg-gray-800 rounded-lg px-3 py-2 text-center">
												<div class="text-gray-500">Сегмент</div>
												<div class="text-white font-medium mt-0.5">{out.deal_segment}</div>
											</div>
										{/if}
										{#if out.deal_probability_pct != null}
											<div class="bg-gray-800 rounded-lg px-3 py-2 text-center">
												<div class="text-gray-500">Вероятность</div>
												<div class="text-white font-medium mt-0.5">{out.deal_probability_pct}%</div>
											</div>
										{/if}
									</div>
								{/if}

								<!-- Тех стек -->
								{#if out.likely_stack?.length}
									<div class="text-xs">
										<span class="text-gray-500">Вероятный стек: </span>
										{#each out.likely_stack as tech}
											<span class="mr-1 px-1.5 py-0.5 bg-cyan-900/50 text-cyan-300 rounded">{tech}</span>
										{/each}
									</div>
								{/if}
								{#if out.presale_questions?.length}
									<div class="space-y-1">
										<div class="text-xs text-gray-500">Вопросы для пресейл-звонка:</div>
										{#each out.presale_questions as q}
											<div class="text-xs text-gray-300 pl-2 border-l border-cyan-800">• {q}</div>
										{/each}
									</div>
								{/if}
							</div>
						{/if}

						<!-- Полный JSON -->
						<details class="text-xs text-gray-600">
							<summary class="cursor-pointer hover:text-gray-400">Полный JSON вывода</summary>
							<pre class="mt-2 overflow-x-auto rounded-lg bg-gray-950 px-3 py-2 text-gray-400 text-xs">{JSON.stringify(taskResult.output, null, 2)}</pre>
						</details>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
