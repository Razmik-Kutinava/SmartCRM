<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	let data = $state(null);
	let loading = $state(true);
	let err = $state('');
	let promptText = $state('');
	let saving = $state(false);
	let resetting = $state(false);

	// Suggest-prompt state
	let suggesting = $state(false);
	let suggestion = $state(null); // { patterns, explanation, few_shot_examples[], bad_traces_analyzed }
	let suggErr = $state('');
	// Какие few-shot примеры выбрал пользователь для вставки
	let selectedExamples = $state([]);
	// Применяем ли предложение
	let applying = $state(false);

	async function load() {
		loading = true;
		try {
			const r = await fetch(`${API}/api/ops/improvement`);
			if (!r.ok) throw new Error(await r.text());
			data = await r.json();
			promptText = data.prompt?.text ?? '';
			err = '';
		} catch (e) {
			err = String(e?.message || e);
		} finally {
			loading = false;
		}
	}

	async function savePrompt() {
		saving = true;
		err = '';
		try {
			const r = await fetch(`${API}/api/ops/hermes/prompt`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ prompt: promptText })
			});
			if (!r.ok) {
				const j = await r.json().catch(() => ({}));
				err = typeof j.detail === 'string' ? j.detail : JSON.stringify(j);
				return;
			}
			err = '';
			suggestion = null;
			selectedExamples = [];
			await load();
		} finally {
			saving = false;
		}
	}

	async function resetPrompt() {
		if (!confirm('Вернуть встроенный промпт из кода? Файл переопределения будет удалён.')) return;
		resetting = true;
		try {
			await fetch(`${API}/api/ops/hermes/prompt`, { method: 'DELETE' });
			err = '';
			suggestion = null;
			selectedExamples = [];
			await load();
		} finally {
			resetting = false;
		}
	}

	async function suggestFix() {
		suggesting = true;
		suggErr = '';
		suggestion = null;
		selectedExamples = [];
		try {
			const r = await fetch(`${API}/api/ops/suggest-prompt`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ max_bad_traces: 10 })
			});
			const j = await r.json();
			if (!r.ok) {
				suggErr = j.detail || JSON.stringify(j);
				return;
			}
			if (!j.has_suggestion) {
				suggErr = j.message || 'Нет плохих трейсов для анализа';
				return;
			}
			suggestion = j;
			// По умолчанию — все примеры выбраны
			selectedExamples = j.few_shot_examples.map((_, i) => i);
		} catch (e) {
			suggErr = String(e?.message || e);
		} finally {
			suggesting = false;
		}
	}

	function toggleExample(i) {
		if (selectedExamples.includes(i)) {
			selectedExamples = selectedExamples.filter((x) => x !== i);
		} else {
			selectedExamples = [...selectedExamples, i];
		}
	}

	function applyExamplesToPrompt() {
		if (!suggestion) return;
		const toAdd = selectedExamples
			.sort((a, b) => a - b)
			.map((i) => suggestion.few_shot_examples[i])
			.join('\n\n');

		// Вставляем перед последней строкой (закрывающей """)
		const marker = '"""';
		const idx = promptText.lastIndexOf(marker);
		if (idx !== -1) {
			promptText = promptText.slice(0, idx).trimEnd() + '\n\n' + toAdd + '\n' + promptText.slice(idx);
		} else {
			promptText = promptText.trimEnd() + '\n\n' + toAdd;
		}
		suggestion = null;
		selectedExamples = [];
	}

	onMount(load);
</script>

<svelte:head><title>Улучшение · Ops</title></svelte:head>

<div class="px-6 py-6 max-w-5xl space-y-8">
	<section>
		<h2 class="text-lg font-semibold text-white mb-1">Улучшение Hermes и голоса</h2>
		<p class="text-sm text-gray-400 leading-relaxed max-w-3xl">
			Цикл: плохой трейс (👎) → <a href="/ops/traces" class="text-indigo-400 hover:underline">сценарий eval</a> →
			<strong class="text-gray-300">предложи правку промпта</strong> → апруви → сохрани → зафиксируй снимок →
			<a href="/ops/history" class="text-indigo-400 hover:underline">сравни «было / стало»</a>.
		</p>
	</section>

	<!-- Быстрые ссылки -->
	<section class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
		{#each [
			['/ops/traces', 'Трейсы', 'голос и текст'],
			['/ops/scenarios', 'Сценарии', 'фразы и интенты'],
			['/ops/eval', 'Eval', 'регрессия'],
			['/ops/history', 'История', 'метрики'],
			['/ops/insights', 'Инсайты', 'эвристики'],
			['/ops/queue', 'Очередь', 'задачи']
		] as [href, title, sub]}
			<a {href} class="bg-gray-900 border border-gray-800 rounded-xl p-3 hover:border-indigo-700 transition-colors">
				<div class="text-sm font-medium text-white">{title}</div>
				<div class="text-xs text-gray-500 mt-0.5">{sub}</div>
			</a>
		{/each}
	</section>

	{#if loading}
		<p class="text-gray-500">Загрузка…</p>
	{:else if err && !data}
		<p class="text-red-400">{err}</p>
	{:else if data}

		<!-- Сигналы -->
		{#if data.signals}
			<section class="flex flex-wrap gap-3 text-sm">
				<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-2 flex gap-3 items-center">
					<span class="text-gray-500">Фидбек:</span>
					<span class="text-emerald-400 font-semibold">👍 {data.signals.feedback_good ?? 0}</span>
					<span class="text-red-400 font-semibold">👎 {data.signals.feedback_bad ?? 0}</span>
					<span class="text-gray-500 ml-2">Ошибок: {data.signals.errors_recent ?? 0}</span>
				</div>
				{#if (data.signals.feedback_bad ?? 0) > 0}
					<div class="bg-amber-950/40 border border-amber-800/50 rounded-xl px-4 py-2 text-amber-300 text-sm">
						Есть 👎 трейсы → нажми «Предложи правку промпта»
					</div>
				{/if}
			</section>
		{/if}

		<!-- ── Suggest-prompt блок ───────────────────────────────────── -->
		<section class="bg-gray-900 border border-gray-800 rounded-xl p-5">
			<div class="flex flex-wrap items-center justify-between gap-3 mb-3">
				<div>
					<h3 class="text-sm font-semibold text-white">Предложи правку промпта</h3>
					<p class="text-xs text-gray-400 mt-0.5">Groq проанализирует плохие трейсы и предложит few-shot примеры для вставки.</p>
				</div>
				<button
					type="button"
					onclick={suggestFix}
					disabled={suggesting}
					class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm rounded-lg flex items-center gap-2"
				>
					{#if suggesting}
						<span class="animate-spin inline-block text-base">⟳</span> Анализирую трейсы…
					{:else}
						✦ Предложи правку промпта
					{/if}
				</button>
			</div>

			{#if suggErr}
				<p class="text-sm text-amber-400">{suggErr}</p>
			{/if}

			{#if suggestion}
				<div class="space-y-4 mt-2">
					<!-- Паттерны + объяснение -->
					<div class="bg-gray-800/60 rounded-lg p-4">
						<div class="text-xs text-gray-400 mb-1">Проанализировано трейсов: {suggestion.bad_traces_analyzed}</div>
						{#if suggestion.patterns}
							<p class="text-sm text-gray-300 mb-2"><strong class="text-white">Проблемы:</strong> {suggestion.patterns}</p>
						{/if}
						{#if suggestion.explanation}
							<p class="text-sm text-gray-300"><strong class="text-white">Что исправить:</strong> {suggestion.explanation}</p>
						{/if}
					</div>

					<!-- Few-shot примеры — выбираем какие вставить -->
					{#if suggestion.few_shot_examples?.length}
						<div>
							<div class="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">
								Выбери примеры для вставки в промпт ({selectedExamples.length} / {suggestion.few_shot_examples.length})
							</div>
							<div class="space-y-2">
								{#each suggestion.few_shot_examples as ex, i}
									<label class="flex gap-3 items-start cursor-pointer group">
										<input
											type="checkbox"
											checked={selectedExamples.includes(i)}
											onchange={() => toggleExample(i)}
											class="mt-1 accent-indigo-500 shrink-0"
										/>
										<pre class="text-xs text-gray-300 bg-gray-950 rounded-lg p-3 flex-1 whitespace-pre-wrap font-mono leading-relaxed group-hover:border-indigo-800 border border-gray-800">{ex}</pre>
									</label>
								{/each}
							</div>

							<div class="flex gap-2 mt-3">
								<button
									type="button"
									onclick={applyExamplesToPrompt}
									disabled={selectedExamples.length === 0}
									class="px-4 py-2 bg-emerald-700 hover:bg-emerald-600 disabled:opacity-40 text-white text-sm rounded-lg"
								>
									✓ Вставить выбранные в промпт ({selectedExamples.length})
								</button>
								<button
									type="button"
									onclick={() => { suggestion = null; selectedExamples = []; }}
									class="px-3 py-2 border border-gray-600 text-gray-400 text-sm rounded-lg hover:bg-gray-800"
								>
									Отмена
								</button>
							</div>
							<p class="text-xs text-gray-500 mt-2">После вставки промпт обновится в редакторе ниже — проверь и нажми «Сохранить».</p>
						</div>
					{:else}
						<p class="text-sm text-gray-400">Groq не сгенерировал конкретных примеров. Попробуй ещё раз с большим количеством трейсов.</p>
					{/if}
				</div>
			{/if}
		</section>

		<!-- ── Системный промпт ──────────────────────────────────────── -->
		<section>
			<div class="flex flex-wrap items-center justify-between gap-2 mb-2">
				<h3 class="text-sm font-medium text-white">Системный промпт Hermes</h3>
				<div class="flex items-center gap-2 text-xs">
					<span class="px-2 py-0.5 rounded {data.prompt?.source === 'override' ? 'bg-amber-900/50 text-amber-200' : 'bg-gray-800 text-gray-400'}">
						{data.prompt?.source === 'override' ? 'файл override' : 'встроенный из кода'}
					</span>
					<span class="text-gray-600">{promptText.length} симв.</span>
				</div>
			</div>

			{#if err}
				<p class="text-sm text-red-400 mb-2">{err}</p>
			{/if}

			<textarea
				bind:value={promptText}
				rows="20"
				class="w-full bg-gray-950 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-100 font-mono leading-relaxed focus:outline-none focus:border-indigo-500"
				spellcheck="false"
			></textarea>

			<div class="flex flex-wrap gap-2 mt-3">
				<button
					type="button"
					onclick={savePrompt}
					disabled={saving}
					class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm rounded-lg"
				>
					{saving ? 'Сохраняем…' : 'Сохранить промпт'}
				</button>
				<button
					type="button"
					onclick={resetPrompt}
					disabled={resetting || data.prompt?.source !== 'override'}
					class="px-4 py-2 border border-gray-600 text-gray-300 text-sm rounded-lg hover:bg-gray-800 disabled:opacity-40"
				>
					{resetting ? '…' : 'Сбросить на встроенный'}
				</button>
			</div>
			<p class="text-xs text-gray-500 mt-2">
				После сохранения новый текст сразу используется в голосовом пайплайне. Перезапуск сервера не нужен.
			</p>
		</section>

		<!-- Авто-рекомендации -->
		{#if data.suggestions?.length}
			<section>
				<h3 class="text-sm font-medium text-gray-400 mb-3">Автоматические рекомендации</h3>
				<div class="space-y-2">
					{#each data.suggestions as s}
						<div class="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
							<div class="flex justify-between gap-2 mb-1">
								<h4 class="text-white text-sm font-medium">{s.title}</h4>
								<span class="text-xs text-gray-500">уверенность {Math.round((s.confidence || 0) * 100)}%</span>
							</div>
							<p class="text-sm text-gray-400">{s.body}</p>
						</div>
					{/each}
				</div>
			</section>
		{/if}
	{/if}
</div>
