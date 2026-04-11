<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	import { intentColor, modelLabel } from '$lib/opsCommon.js';

	const API = getApiUrl();

	let singleEvalRunning = $state(false);
	let singleEvalId = $state(null);
	let singleIncludeGroq = $state(false);
	let singleEvalResult = $state(null);

	let items = $state([]);
	let total = $state(0);
	let loading = $state(true);
	let err = $state('');

	let editingId = $state(null);
	let form = $state({
		title: '',
		phrase: '',
		expected_intent: 'noop',
		expected_slots_json: '{}',
		success_criteria: '',
		desired_outcome: '',
		notes: '',
		status: 'draft'
	});

	const statuses = [
		['draft', 'Черновик'],
		['pending_review', 'На проверке'],
		['approved', 'Утверждён (в eval из БД)'],
		['archived', 'Архив']
	];

	async function load() {
		loading = true;
		try {
			const r = await fetch(`${API}/api/ops/scenarios?limit=500`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			items = d.items || [];
			total = d.total ?? 0;
			err = '';
		} catch (e) {
			err = String(e?.message || e);
		} finally {
			loading = false;
		}
	}

	function resetForm() {
		editingId = null;
		form = {
			title: '',
			phrase: '',
			expected_intent: 'noop',
			expected_slots_json: '{}',
			success_criteria: '',
			desired_outcome: '',
			notes: '',
			status: 'draft'
		};
	}

	function edit(row) {
		editingId = row.id;
		form = {
			title: row.title || '',
			phrase: row.phrase,
			expected_intent: row.expected_intent,
			expected_slots_json: JSON.stringify(row.expected_slots || {}, null, 2),
			success_criteria: row.success_criteria || '',
			desired_outcome: row.desired_outcome || '',
			notes: row.notes || '',
			status: row.status
		};
	}

	async function save() {
		let slots = {};
		try {
			slots = JSON.parse(form.expected_slots_json || '{}');
		} catch {
			err = 'Поле «ожидаемые слоты» — невалидный JSON';
			return;
		}
		const payload = {
			title: form.title,
			phrase: form.phrase.trim(),
			expected_intent: form.expected_intent.trim(),
			expected_slots: slots,
			success_criteria: form.success_criteria,
			desired_outcome: form.desired_outcome,
			notes: form.notes,
			status: form.status
		};
		if (!payload.phrase || !payload.expected_intent) {
			err = 'Заполните фразу и ожидаемый интент';
			return;
		}
		err = '';
		const url = editingId ? `${API}/api/ops/scenarios/${editingId}` : `${API}/api/ops/scenarios`;
		const method = editingId ? 'PATCH' : 'POST';
		const r = await fetch(url, {
			method,
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload)
		});
		if (!r.ok) {
			err = await r.text();
			return;
		}
		resetForm();
		await load();
	}

	async function approve(id) {
		await fetch(`${API}/api/ops/scenarios/${id}/approve`, { method: 'POST' });
		await load();
	}

	async function remove(id) {
		if (!confirm('Удалить сценарий?')) return;
		await fetch(`${API}/api/ops/scenarios/${id}`, { method: 'DELETE' });
		await load();
	}

	function modelsSingle() {
		const m = ['hermes3'];
		if (singleIncludeGroq) m.push('groq');
		return m;
	}

	async function runSingleEval(row) {
		singleEvalRunning = true;
		singleEvalId = row.id;
		singleEvalResult = null;
		try {
			const r = await fetch(`${API}/api/ops/scenarios/${row.id}/eval`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ models: modelsSingle() })
			});
			const data = await r.json();
			if (!r.ok) {
				singleEvalResult = { error: typeof data.detail === 'string' ? data.detail : JSON.stringify(data) };
			} else {
				singleEvalResult = data;
			}
		} catch (e) {
			singleEvalResult = { error: String(e) };
		} finally {
			singleEvalRunning = false;
		}
	}

	onMount(load);
</script>

<div class="px-6 py-6 max-w-5xl">
	<p class="text-sm text-gray-400 mb-4">
		Сценарии для регрессии Hermes: фраза, ожидаемый интент, критерии успеха и желаемый результат. «Прогнать только этот» вызывает
		<strong class="text-gray-300">одну фразу</strong> через Hermes3 (Ollama) — без апрува и без полного списка. Groq — опционально
		(токены API).
	</p>
	<div class="flex flex-wrap items-center gap-3 mb-6 text-sm">
		<label class="flex items-center gap-2 cursor-pointer text-gray-400">
			<input type="checkbox" bind:checked={singleIncludeGroq} class="accent-indigo-500" />
			При прогоне одного сценария добавлять Groq
		</label>
	</div>

	{#if singleEvalResult && !singleEvalResult.error}
		<div class="mb-6 bg-gray-900 border border-indigo-900/50 rounded-xl p-4 text-sm">
			<div class="text-xs text-gray-500 mb-2">Результат прогона #{singleEvalId}</div>
			<div class="grid grid-cols-2 gap-2 max-w-md">
				{#each Object.entries(singleEvalResult.summary || {}) as [model, s]}
					<div>
						<span class="text-gray-400">{modelLabel(model)}:</span>
						<span class="text-white ml-1">{s.accuracy_pct}%</span>
						<span class="text-gray-500 text-xs">({s.correct}/{s.total})</span>
					</div>
				{/each}
			</div>
			{#if singleEvalResult.results?.[0]}
				{@const row = singleEvalResult.results[0]}
				<div class="mt-3 text-xs text-gray-400 space-y-1">
					<div>Ожидалось: <span class="text-gray-200">{row.expected}</span></div>
					{#each modelsSingle() as model}
						{@const m = row.models?.[model]}
						{#if m}
							<div>
								{modelLabel(model)}: {#if m.correct === true}<span class="text-emerald-400">✓</span>{:else}<span class="text-red-400">✗</span>{/if}
								<span class="px-1 rounded {intentColor(m.intent)}">{m.intent}</span>
								{m.duration_ms}ms
							</div>
						{/if}
					{/each}
				</div>
			{/if}
		</div>
	{:else if singleEvalResult?.error}
		<div class="mb-6 text-sm text-red-400">{singleEvalResult.error}</div>
	{/if}

	{#if err}
		<div class="mb-4 text-sm text-red-400 whitespace-pre-wrap">{err}</div>
	{/if}

	<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-8">
		<h2 class="text-sm font-medium text-white mb-3">{editingId ? `Редактирование #${editingId}` : 'Новый сценарий'}</h2>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
			<label class="block">
				<span class="text-xs text-gray-500">Название</span>
				<input
					class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
					bind:value={form.title}
				/>
			</label>
			<label class="block">
				<span class="text-xs text-gray-500">Статус</span>
				<select
					class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
					bind:value={form.status}
				>
					{#each statuses as [v, l]}
						<option value={v}>{l}</option>
					{/each}
				</select>
			</label>
			<label class="block md:col-span-2">
				<span class="text-xs text-gray-500">Фраза пользователя (текст команды)</span>
				<input
					class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
					bind:value={form.phrase}
				/>
			</label>
			<label class="block">
				<span class="text-xs text-gray-500">Ожидаемый интент (Hermes)</span>
				<input
					class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
					bind:value={form.expected_intent}
				/>
			</label>
			<label class="block">
				<span class="text-xs text-gray-500">Ожидаемые слоты (JSON)</span>
				<textarea
					rows="3"
					class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 font-mono"
					bind:value={form.expected_slots_json}
				></textarea>
			</label>
			<label class="block md:col-span-2">
				<span class="text-xs text-gray-500">Критерий успеха (что считаем правильным ответом роутера)</span>
				<textarea
					rows="2"
					class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
					bind:value={form.success_criteria}
				></textarea>
			</label>
			<label class="block md:col-span-2">
				<span class="text-xs text-gray-500">Ожидаемый результат / чего хотим в продукте</span>
				<textarea
					rows="2"
					class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
					bind:value={form.desired_outcome}
				></textarea>
			</label>
			<label class="block md:col-span-2">
				<span class="text-xs text-gray-500">Заметки</span>
				<textarea
					rows="2"
					class="mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
					bind:value={form.notes}
				></textarea>
			</label>
		</div>
		<div class="flex gap-2 mt-4">
			<button type="button" onclick={save} class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg">
				Сохранить
			</button>
			{#if editingId}
				<button type="button" onclick={resetForm} class="px-4 py-2 border border-gray-600 text-gray-300 text-sm rounded-lg">
					Отмена
				</button>
			{/if}
		</div>
	</div>

	<h2 class="text-sm font-medium text-gray-300 mb-2">Список ({total})</h2>
	{#if loading}
		<p class="text-gray-500">Загрузка…</p>
	{:else if items.length === 0}
		<p class="text-gray-500">Пока пусто.</p>
	{:else}
		<div class="space-y-2">
			{#each items as row}
				<div class="bg-gray-900 border border-gray-800 rounded-lg p-3 text-sm">
					<div class="flex flex-wrap justify-between gap-2">
						<div>
							<span class="text-gray-500">#{row.id}</span>
							<span class="text-white ml-2">{row.title || 'Без названия'}</span>
							<span class="text-xs text-amber-400 ml-2">{row.status}</span>
						</div>
						<div class="flex flex-wrap gap-2 items-center">
							<button
								type="button"
								disabled={singleEvalRunning}
								class="text-cyan-400 hover:text-cyan-300 disabled:opacity-50 text-sm"
								onclick={() => runSingleEval(row)}
							>
								{singleEvalRunning && singleEvalId === row.id ? 'Прогон…' : 'Прогнать только этот'}
							</button>
							<button type="button" class="text-indigo-400 hover:text-indigo-300" onclick={() => edit(row)}>Изменить</button>
							{#if row.status !== 'approved'}
								<button type="button" class="text-emerald-400 hover:text-emerald-300" onclick={() => approve(row.id)}
									>Утвердить</button
								>
							{/if}
							<button type="button" class="text-red-400 hover:text-red-300" onclick={() => remove(row.id)}>Удалить</button>
						</div>
					</div>
					<p class="text-gray-300 mt-2">"{row.phrase}"</p>
					<p class="text-gray-500 text-xs mt-1">интент: {row.expected_intent}</p>
					{#if row.success_criteria}
						<p class="text-gray-500 text-xs mt-1">критерий: {row.success_criteria}</p>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
