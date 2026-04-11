<script>
	import { onMount, onDestroy } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	import { fmtTime, intentColor, modelLabel } from '$lib/opsCommon.js';

	const API = getApiUrl();

	const INTENTS = [
		'create_lead','update_lead','delete_lead','list_leads',
		'create_task','list_tasks','update_task','delete_task',
		'write_email','run_analysis','ask_strategist','search_web','noop'
	];

	let traces = $state([]);
	let customCmd = $state('');
	let pollInterval = null;

	// Какой трейс открыт для правки
	let editingId = $state(null);

	// Форма правки — состояние на один открытый трейс
	let editPhrase  = $state('');   // что пользователь ХОТЕЛ сказать
	let editIntent  = $state('noop');
	let editSlotsJson = $state('{}');
	let editReply   = $state('');

	// eval-состояние формы: null | 'running' | 'pass' | 'fail' | 'error'
	let evalState   = $state(null);
	let evalMsg     = $state('');

	// сохранение в промпт
	let saving      = $state(false);
	let saveMsg     = $state('');
	let formErr     = $state('');

	/** Трейс → id сценария eval (после добавления в сценарии) */
	let toScenarioId = $state(/** @type {Record<string, number>} */ ({}));
	/** Трейс → статус сценария (draft / pending_review / approved / …) */
	let traceScenarioStatus = $state(/** @type {Record<string, string>} */ ({}));

	async function loadTraces() {
		try {
			const r = await fetch(`${API}/api/ops/traces?limit=60`);
			traces = await r.json();
		} catch (e) { console.error(e); }
	}

	async function sendFeedback(traceId, feedback) {
		await fetch(`${API}/api/ops/feedback`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ trace_id: traceId, feedback })
		});
		traces = traces.map((t) => (t.id === traceId ? { ...t, feedback } : t));
	}

	function openEdit(t) {
		editingId    = t.id;
		editPhrase   = t.text || '';
		editIntent   = t.intent || 'noop';
		editSlotsJson = JSON.stringify(t.slots || {}, null, 2);
		editReply    = t.reply || '';
		evalState    = null;
		evalMsg      = '';
		saveMsg      = '';
		formErr      = '';
	}

	function closeEdit() {
		editingId = null;
		evalState = null;
		evalMsg   = '';
		saveMsg   = '';
		formErr   = '';
	}

	/** Шаг 1: прогнать eval на откорректированной фразе */
	async function runEval() {
		formErr  = '';
		evalMsg  = '';
		saveMsg  = '';

		// Валидация слотов
		let slots = {};
		try { slots = JSON.parse(editSlotsJson || '{}'); }
		catch { formErr = 'Слоты — невалидный JSON'; return; }

		if (!editPhrase.trim()) { formErr = 'Введи фразу'; return; }

		evalState = 'running';
		try {
			const r = await fetch(`${API}/api/ops/eval`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					models: ['groq'],
					cases: [{ text: editPhrase.trim(), expected_intent: editIntent }]
				})
			});
			const d = await r.json();
			const s = Object.values(d.summary || {})[0];
			if (!s) { evalState = 'error'; evalMsg = 'Нет данных от eval'; return; }

			if (s.accuracy_pct === 100) {
				evalState = 'pass';
				evalMsg = `✓ Groq вернул правильный интент (${s.accuracy_pct}%)`;
			} else {
				// Покажем что вернула модель
				const got = d.results?.[0]?.models?.groq?.intent ?? '?';
				evalState = 'fail';
				evalMsg = `✗ Groq вернул «${got}», ожидалось «${editIntent}» — поправь и прогони снова`;
			}
		} catch (e) {
			evalState = 'error';
			evalMsg = String(e?.message || e);
		}
	}

	/** Шаг 2: добавить в промпт (только если eval прошёл) */
	async function addToPrompt() {
		formErr = '';
		saveMsg = '';
		let slots = {};
		try { slots = JSON.parse(editSlotsJson || '{}'); }
		catch { formErr = 'Слоты — невалидный JSON'; return; }

		saving = true;
		try {
			const r = await fetch(`${API}/api/ops/hermes/add-example`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					phrase: editPhrase.trim(),
					intent: editIntent,
					slots,
					reply: editReply
				})
			});
			const j = await r.json();
			if (!r.ok) { formErr = j.detail || JSON.stringify(j); return; }
			saveMsg = `✓ Добавлено в промпт (${j.prompt_chars} симв.)`;
			setTimeout(closeEdit, 2500);
		} catch (e) {
			formErr = String(e?.message || e);
		} finally {
			saving = false;
		}
	}

	async function sendTestCommand() {
		if (!customCmd.trim()) return;
		await fetch(`${API}/api/voice/command`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ text: customCmd })
		});
		customCmd = '';
		setTimeout(loadTraces, 400);
	}

	// Превью few-shot примера
	function previewExample() {
		let slots = {};
		try { slots = JSON.parse(editSlotsJson || '{}'); } catch {}
		return JSON.stringify({
			intent: editIntent,
			agents: ['analyst'],
			slots,
			parallel: false,
			reply: editReply || `Выполняю: ${editIntent}.`
		});
	}

	onMount(() => { loadTraces(); pollInterval = setInterval(loadTraces, 5000); });
	onDestroy(() => clearInterval(pollInterval));
</script>

<div class="px-6 py-6">
	<!-- Шапка -->
	<div class="flex flex-col sm:flex-row gap-3 justify-between mb-5">
		<p class="text-sm text-gray-400">
			Ставь 👎 → <span class="text-amber-300">✎ Исправить</span> → поправь фразу и интент →
			<span class="text-cyan-300">▶ Прогнать eval</span> → если ✓ →
			<span class="text-emerald-300">Добавить в промпт</span>
		</p>
		<div class="flex gap-2">
			<input
				bind:value={customCmd}
				onkeydown={(e) => e.key === 'Enter' && sendTestCommand()}
				placeholder="Команда для теста…"
				class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-100 placeholder-gray-500 w-60 focus:outline-none focus:border-indigo-500"
			/>
			<button type="button" onclick={sendTestCommand}
				class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg">
				Отправить
			</button>
		</div>
	</div>

	{#if traces.length === 0}
		<div class="text-center text-gray-500 py-20">Трейсов пока нет.</div>
	{:else}
		<div class="space-y-2 max-w-5xl">
			{#each traces as t}
				{@const isEditing = editingId === t.id}
				{@const sc = traceScenarioStatus[t.id]}

				<div class="bg-gray-900 border rounded-xl transition-colors
					{t.error ? 'border-red-800' : isEditing ? 'border-indigo-600' : t.feedback === 'bad' ? 'border-amber-800/60' : 'border-gray-800'}">

					<!-- Основная строка трейса -->
					<div class="p-4 flex gap-4 items-start">
						<!-- Время -->
						<div class="shrink-0 text-xs text-gray-500 w-14 text-right">
							<div>{fmtTime(t.ts)}</div>
							<div class="opacity-50">{t.source}</div>
						</div>

						<!-- Контент -->
						<div class="flex-1 min-w-0">
							<div class="flex items-center gap-2 flex-wrap mb-1">
								{#if t.intent}
									<span class="text-xs px-2 py-0.5 rounded-full font-medium {intentColor(t.intent)}">{t.intent}</span>
								{/if}
								{#if t.duration_ms}<span class="text-xs text-gray-500">{t.duration_ms}ms</span>{/if}
								{#if t.model}<span class="text-xs text-gray-600">{modelLabel(t.model)}</span>{/if}
								{#if t.error}<span class="text-xs text-red-400">Ошибка</span>{/if}
							</div>
							<div class="text-sm text-gray-200">"{t.text}"</div>
							{#if t.reply}
								<div class="text-xs text-gray-500 italic mt-0.5">→ {t.reply}</div>
							{/if}
							{#if t.slots && Object.keys(t.slots).length}
								<div class="text-xs text-gray-600 mt-0.5 font-mono">slots: {JSON.stringify(t.slots)}</div>
							{/if}
						</div>

						<!-- Кнопки справа -->
						<div class="shrink-0 flex flex-col gap-1.5 items-end">
							{#if sc === 'done' && toScenarioId[t.id]}
								<div class="flex flex-col gap-1 items-end">
									<a
										href="/ops/scenarios"
										class="text-xs text-indigo-400 hover:text-indigo-300 underline"
										title="Открыть сценарии eval"
									>
										Сценарий #{toScenarioId[t.id]}
									</a>
								</div>
							{/if}
							<div class="flex gap-1 items-center">
								<span class="text-xs text-gray-600">#{t.id}</span>
								<button type="button" onclick={() => sendFeedback(t.id, 'good')}
									class="text-sm px-2 py-1 rounded-lg {t.feedback === 'good' ? 'bg-emerald-700 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}">👍</button>
								<button type="button" onclick={() => sendFeedback(t.id, 'bad')}
									class="text-sm px-2 py-1 rounded-lg {t.feedback === 'bad' ? 'bg-red-800 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}">👎</button>
							</div>
							<button type="button"
								onclick={() => isEditing ? closeEdit() : openEdit(t)}
								class="text-xs px-2 py-1 rounded-lg transition-colors
									{isEditing ? 'bg-indigo-700 text-white' : t.feedback === 'bad' ? 'bg-amber-900/60 text-amber-300 hover:bg-amber-800' : 'bg-gray-800 text-gray-500 hover:bg-gray-700'}">
								{isEditing ? '✕ закрыть' : '✎ Исправить'}
							</button>
						</div>
					</div>

					<!-- ── Форма правки ── -->
					{#if isEditing}
						<div class="border-t border-indigo-800/60 bg-gray-950/60 px-4 py-4 rounded-b-xl space-y-4">

							<!-- Шаги-подсказка -->
							<div class="flex items-center gap-2 text-xs text-gray-500">
								<span class="px-2 py-0.5 rounded bg-gray-800 text-gray-400">1. Поправь</span>
								<span class="text-gray-700">→</span>
								<span class="px-2 py-0.5 rounded bg-gray-800 text-cyan-400">2. Прогони eval</span>
								<span class="text-gray-700">→</span>
								<span class="px-2 py-0.5 rounded bg-gray-800 {evalState === 'pass' ? 'text-emerald-400' : 'text-gray-600'}">3. Добавь в промпт</span>
							</div>

							<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">

								<!-- Фраза (редактируемая) -->
								<label class="block sm:col-span-2">
									<span class="text-xs text-gray-400">Что ты хотел сказать <span class="text-gray-600">(можно исправить)</span></span>
									<input bind:value={editPhrase}
										class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500"
										placeholder="Введи правильную фразу…"
										onchange={() => { evalState = null; evalMsg = ''; }}
									/>
									{#if t.text !== editPhrase && editPhrase}
										<p class="text-xs text-gray-600 mt-0.5">оригинал: «{t.text}»</p>
									{/if}
								</label>

								<!-- Правильный интент -->
								<label class="block">
									<span class="text-xs text-gray-400">Правильный интент</span>
									<select bind:value={editIntent}
										class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
										onchange={() => { evalState = null; evalMsg = ''; }}>
										{#each INTENTS as i}
											<option value={i}>{i}</option>
										{/each}
									</select>
								</label>

								<!-- Ответ -->
								<label class="block">
									<span class="text-xs text-gray-400">Ответ модели (reply)</span>
									<input bind:value={editReply}
										placeholder="Создаю лид…"
										class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100" />
								</label>

								<!-- Слоты -->
								<label class="block sm:col-span-2">
									<span class="text-xs text-gray-400">Слоты (JSON)</span>
									<textarea bind:value={editSlotsJson} rows="3"
										class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 font-mono"
										spellcheck="false"></textarea>
								</label>
							</div>

							<!-- Превью few-shot примера -->
							<div class="bg-gray-900 rounded-lg p-3 font-mono text-xs text-gray-500">
								<div class="text-gray-700 mb-1">Будет добавлено в промпт:</div>
								<div class="text-gray-400">Input: "{editPhrase}"</div>
								<div class="text-gray-400 break-all">Output: {previewExample()}</div>
							</div>

							<!-- Ошибки / статусы -->
							{#if formErr}
								<p class="text-sm text-red-400">{formErr}</p>
							{/if}
							{#if evalMsg}
								<p class="text-sm {evalState === 'pass' ? 'text-emerald-400' : evalState === 'fail' ? 'text-amber-400' : 'text-red-400'}">{evalMsg}</p>
							{/if}
							{#if saveMsg}
								<p class="text-sm text-emerald-400">{saveMsg}</p>
							{/if}

							<!-- Кнопки действий -->
							<div class="flex gap-2 flex-wrap">
								<!-- Шаг 2: eval -->
								<button type="button" onclick={runEval}
									disabled={evalState === 'running'}
									class="px-4 py-2 bg-cyan-800 hover:bg-cyan-700 disabled:opacity-50 text-white text-sm rounded-lg flex items-center gap-2">
									{#if evalState === 'running'}
										<span class="animate-spin">⟳</span> Прогон…
									{:else}
										▶ Прогнать eval
									{/if}
								</button>

								<!-- Шаг 3: добавить в промпт (только если eval pass) -->
								<button type="button" onclick={addToPrompt}
									disabled={evalState !== 'pass' || saving}
									title={evalState !== 'pass' ? 'Сначала прогони eval — должен пройти ✓' : ''}
									class="px-4 py-2 text-sm rounded-lg transition-colors flex items-center gap-1
										{evalState === 'pass'
											? 'bg-emerald-700 hover:bg-emerald-600 text-white'
											: 'bg-gray-800 text-gray-600 cursor-not-allowed'}">
									{saving ? 'Сохраняем…' : '✓ Добавить в промпт'}
								</button>

								<button type="button" onclick={closeEdit}
									class="px-3 py-2 border border-gray-700 text-gray-500 text-sm rounded-lg hover:bg-gray-800">
									Отмена
								</button>
							</div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
