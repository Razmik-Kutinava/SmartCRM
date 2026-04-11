<script>
	import { getApiUrl } from '$lib/websocket.js';
	import { intentColor } from '$lib/opsCommon.js';

	const API = getApiUrl();

	const EXAMPLE_JSON = `[
  {"phrase": "создай лид Ромашка телефон 79161234567", "intent": "create_lead", "slots": {"company": "Ромашка", "phone": "+79161234567"}, "reply": "Создаю лид Ромашка."},
  {"phrase": "удали лид Ромашка", "intent": "delete_lead", "slots": {"company": "Ромашка"}, "reply": "Удаляю лид Ромашка."},
  {"phrase": "поправь лид Вектор этап Переговоры", "intent": "update_lead", "slots": {"company": "Вектор", "field": "stage", "value": "Переговоры"}, "reply": "Обновляю этап."}
]`;

	// Состояние
	let rawText     = $state('');
	let items       = $state([]);   // распарсенный список
	let parseErr    = $state('');

	let evalRunning = $state(false);
	let evalDone    = $state(false);
	let evalResults = $state([]);   // [{phrase,expected,got,passed,slots,reply}]
	let evalSummary = $state(null); // {total,passed,accuracy_pct}

	let adding      = $state(false);
	let addMsg      = $state('');

	// Какие записи выбраны для добавления в промпт
	let selected    = $state(new Set());

	function toggleSelect(i) {
		const s = new Set(selected);
		s.has(i) ? s.delete(i) : s.add(i);
		selected = s;
	}

	function selectAll(onlyPassed = false) {
		const s = new Set();
		(evalDone ? evalResults : items).forEach((r, i) => {
			if (!onlyPassed || r.passed) s.add(i);
		});
		selected = s;
	}

	// Парсим JSON или CSV из textarea
	function parseInput() {
		parseErr = '';
		evalDone = false;
		evalResults = [];
		selected = new Set();
		addMsg = '';
		const t = rawText.trim();
		if (!t) { items = []; return; }

		// Попытка JSON
		try {
			const parsed = JSON.parse(t);
			if (!Array.isArray(parsed)) { parseErr = 'JSON должен быть массивом []'; return; }
			items = parsed.map(r => ({
				phrase: String(r.phrase || r.text || '').trim(),
				intent: String(r.intent || r.expected_intent || '').trim(),
				slots:  typeof r.slots === 'object' ? r.slots : {},
				reply:  String(r.reply || '').trim(),
			})).filter(r => r.phrase && r.intent);
			if (!items.length) parseErr = 'Нет валидных записей (нужны поля phrase + intent)';
			return;
		} catch {}

		// Попытка CSV (phrase,intent,slots_json,reply)
		try {
			const lines = t.split('\n').filter(l => l.trim());
			const header = lines[0].toLowerCase();
			const start = header.includes('phrase') || header.includes('фраза') ? 1 : 0;
			items = lines.slice(start).map(line => {
				const cols = line.split(',');
				return {
					phrase: (cols[0] || '').trim().replace(/^"|"$/g, ''),
					intent: (cols[1] || '').trim().replace(/^"|"$/g, ''),
					slots:  (() => { try { return JSON.parse(cols[2] || '{}'); } catch { return {}; } })(),
					reply:  (cols[3] || '').trim().replace(/^"|"$/g, ''),
				};
			}).filter(r => r.phrase && r.intent);
			if (!items.length) parseErr = 'CSV: нет данных. Колонки: phrase,intent,slots_json,reply';
		} catch (e) {
			parseErr = String(e);
		}
	}

	// Загрузка файла
	function onFileChange(e) {
		const file = e.target.files?.[0];
		if (!file) return;
		const reader = new FileReader();
		reader.onload = ev => { rawText = ev.target.result; parseInput(); };
		reader.readAsText(file, 'utf-8');
	}

	// Запускаем eval на весь список
	async function runEval() {
		if (!items.length) return;
		evalRunning = true;
		evalDone = false;
		addMsg = '';
		selected = new Set();
		try {
			const r = await fetch(`${API}/api/ops/hermes/bulk-eval`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(items),
			});
			const d = await r.json();
			evalResults = d.results || [];
			evalSummary = { total: d.total, passed: d.passed, accuracy_pct: d.accuracy_pct };
			evalDone = true;
			// Автовыбор прошедших
			selectAll(true);
		} catch (e) {
			parseErr = String(e);
		} finally {
			evalRunning = false;
		}
	}

	// Добавляем выбранные в промпт
	async function addSelected() {
		const list = evalDone
			? evalResults.filter((_, i) => selected.has(i))
			: items.filter((_, i) => selected.has(i));
		if (!list.length) return;
		adding = true;
		addMsg = '';
		try {
			const r = await fetch(`${API}/api/ops/hermes/bulk-add`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(list.map(r => ({
					phrase: r.phrase,
					intent: r.expected ?? r.intent,
					slots:  r.slots || {},
					reply:  r.reply || '',
				}))),
			});
			const d = await r.json();
			addMsg = `✓ Добавлено ${d.added} примеров в промпт (${d.prompt_chars} симв.)`;
		} catch (e) {
			addMsg = `Ошибка: ${e}`;
		} finally {
			adding = false;
		}
	}

	const displayList = $derived(evalDone ? evalResults : items);
</script>

<div class="px-6 py-6 max-w-5xl space-y-6">
	<div>
		<h2 class="text-base font-semibold text-white mb-1">Импорт few-shot примеров</h2>
		<p class="text-sm text-gray-400">
			Загрузи JSON или CSV → проверь через eval → добавь прошедшие в промпт Hermes.
		</p>
	</div>

	<!-- Загрузка файла -->
	<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
		<div class="flex flex-wrap gap-3 items-center">
			<label class="cursor-pointer px-4 py-2 bg-indigo-700 hover:bg-indigo-600 text-white text-sm rounded-lg">
				📂 Выбрать файл (JSON / CSV)
				<input type="file" accept=".json,.csv,.txt" class="hidden" onchange={onFileChange} />
			</label>
			<span class="text-xs text-gray-500">или вставь текст ниже</span>
		</div>

		<textarea
			bind:value={rawText}
			oninput={parseInput}
			rows="8"
			spellcheck="false"
			placeholder={EXAMPLE_JSON}
			class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 font-mono focus:outline-none focus:border-indigo-500 resize-y"
		></textarea>

		{#if parseErr}
			<p class="text-sm text-red-400">{parseErr}</p>
		{:else if items.length}
			<p class="text-sm text-emerald-400">✓ Распознано {items.length} записей</p>
		{/if}
	</div>

	<!-- Действия -->
	{#if items.length > 0}
		<div class="flex flex-wrap gap-3 items-center">
			<button type="button" onclick={runEval} disabled={evalRunning}
				class="px-4 py-2 bg-cyan-800 hover:bg-cyan-700 disabled:opacity-50 text-white text-sm rounded-lg flex items-center gap-2">
				{evalRunning ? '⟳ Прогон eval…' : '▶ Прогнать eval'}
			</button>

			{#if evalRunning}
				<span class="text-xs text-gray-400">~{items.length * 2}с на {items.length} фраз…</span>
			{/if}

			{#if evalDone && evalSummary}
				<span class="text-sm {evalSummary.accuracy_pct >= 80 ? 'text-emerald-400' : 'text-amber-400'}">
					{evalSummary.accuracy_pct}% прошло ({evalSummary.passed}/{evalSummary.total})
				</span>
			{/if}
		</div>
	{/if}

	<!-- Таблица результатов / превью -->
	{#if displayList.length > 0}
		<div class="bg-gray-900 border border-gray-800 rounded-xl overflow-x-auto">
			<div class="flex items-center justify-between px-4 py-2 border-b border-gray-800">
				<span class="text-xs text-gray-500">{displayList.length} записей · выбрано {selected.size}</span>
				<div class="flex gap-2">
					<button type="button" onclick={() => selectAll(false)}
						class="text-xs text-indigo-400 hover:text-indigo-300">Все</button>
					{#if evalDone}
						<button type="button" onclick={() => selectAll(true)}
							class="text-xs text-emerald-400 hover:text-emerald-300">Только ✓</button>
					{/if}
					<button type="button" onclick={() => selected = new Set()}
						class="text-xs text-gray-500 hover:text-gray-300">Снять</button>
				</div>
			</div>

			<table class="w-full text-sm min-w-[640px]">
				<thead class="bg-gray-800 text-gray-400 text-xs">
					<tr>
						<th class="px-3 py-2 w-8"></th>
						<th class="px-3 py-2 text-left">Фраза</th>
						<th class="px-3 py-2 text-left">Ожидается</th>
						{#if evalDone}
							<th class="px-3 py-2 text-left">Groq вернул</th>
							<th class="px-3 py-2 w-12">✓</th>
						{/if}
						<th class="px-3 py-2 text-left">Слоты</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-800">
					{#each displayList as row, i}
						<tr class="hover:bg-gray-800/40 {evalDone && !row.passed ? 'opacity-50' : ''}">
							<td class="px-3 py-2">
								<input type="checkbox"
									checked={selected.has(i)}
									onchange={() => toggleSelect(i)}
									class="accent-indigo-500" />
							</td>
							<td class="px-3 py-2 text-gray-200 max-w-xs">
								<div class="truncate text-xs" title={row.phrase}>"{row.phrase}"</div>
							</td>
							<td class="px-3 py-2">
								<span class="text-xs px-1.5 py-0.5 rounded {intentColor(row.intent ?? row.expected)}">
									{row.intent ?? row.expected}
								</span>
							</td>
							{#if evalDone}
								<td class="px-3 py-2">
									<span class="text-xs px-1.5 py-0.5 rounded {intentColor(row.got)}">
										{row.got}
									</span>
								</td>
								<td class="px-3 py-2 text-center">
									{#if row.passed}
										<span class="text-emerald-400 text-sm">✓</span>
									{:else}
										<span class="text-red-400 text-sm">✗</span>
									{/if}
								</td>
							{/if}
							<td class="px-3 py-2 text-xs text-gray-500 font-mono max-w-[200px] truncate">
								{JSON.stringify(row.slots || {})}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Добавить в промпт -->
		<div class="flex flex-wrap gap-3 items-center">
			<button type="button" onclick={addSelected}
				disabled={selected.size === 0 || adding}
				class="px-4 py-2 text-sm rounded-lg transition-colors
					{selected.size > 0 ? 'bg-emerald-700 hover:bg-emerald-600 text-white' : 'bg-gray-800 text-gray-600 cursor-not-allowed'}">
				{adding ? 'Добавляем…' : `✓ Добавить выбранные (${selected.size}) в промпт`}
			</button>
			{#if addMsg}
				<span class="text-sm {addMsg.startsWith('✓') ? 'text-emerald-400' : 'text-red-400'}">{addMsg}</span>
			{/if}
		</div>
	{/if}

	<!-- Формат подсказка -->
	<details class="text-xs text-gray-600">
		<summary class="cursor-pointer hover:text-gray-400">Формат файла</summary>
		<pre class="mt-2 bg-gray-900 rounded-lg p-3 text-gray-400 overflow-x-auto">{EXAMPLE_JSON}</pre>
		<p class="mt-2">CSV: <code>phrase,intent,slots_json,reply</code> (заголовок опционален)</p>
	</details>
</div>
