<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	let loading = $state(true);
	let saving = $state(false);
	let message = $state('');
	let err = $state('');

	let model = $state('whisper-large-v3-turbo');
	let language = $state('ru');
	let temperature = $state(0);
	let prompt = $state('');
	let ffmpeg_preprocess = $state(true);

	let defaults_from_env = $state(null);
	let saved_to_disk = $state(false);
	let updated_at = $state(null);

	let testFile = $state(null);
	let testBusy = $state(false);
	let testResult = $state('');

	function fmtUpdated(ts) {
		if (ts == null || ts === undefined) return '';
		try {
			return new Date(ts * 1000).toLocaleString('ru-RU');
		} catch {
			return String(ts);
		}
	}

	async function load() {
		err = '';
		loading = true;
		try {
			const r = await fetch(`${API}/api/ops/voice/whisper`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			const e = d.effective || {};
			model = e.model ?? 'whisper-large-v3-turbo';
			language = e.language ?? 'ru';
			temperature = typeof e.temperature === 'number' ? e.temperature : 0;
			prompt = e.prompt ?? '';
			ffmpeg_preprocess = !!e.ffmpeg_preprocess;
			defaults_from_env = d.defaults_from_env ?? null;
			saved_to_disk = !!d.saved_to_disk;
			updated_at = d.updated_at ?? null;
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	async function save() {
		err = '';
		message = '';
		saving = true;
		try {
			const r = await fetch(`${API}/api/ops/voice/whisper`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					model,
					language,
					temperature: Number(temperature),
					prompt,
					ffmpeg_preprocess
				})
			});
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			message = 'Сохранено. Новые запросы к Whisper используют эти параметры.';
			if (d.effective) {
				const e = d.effective;
				model = e.model ?? model;
				language = e.language ?? language;
				temperature = e.temperature ?? temperature;
				prompt = e.prompt ?? prompt;
				ffmpeg_preprocess = !!e.ffmpeg_preprocess;
			}
			saved_to_disk = true;
			await load();
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally {
			saving = false;
		}
	}

	async function resetToEnv() {
		if (!confirm('Сбросить файл настроек и снова использовать только переменные из .env?')) return;
		err = '';
		message = '';
		saving = true;
		try {
			const r = await fetch(`${API}/api/ops/voice/whisper`, {
				method: 'DELETE'
			});
			if (!r.ok) throw new Error(await r.text());
			message = 'Файл настроек удалён, действуют значения из окружения.';
			await load();
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally {
			saving = false;
		}
	}

	async function runTest() {
		testResult = '';
		if (!testFile) {
			testResult = 'Выберите аудиофайл.';
			return;
		}
		testBusy = true;
		try {
			const fd = new FormData();
			fd.append('file', testFile);
			const r = await fetch(`${API}/api/voice/transcribe`, { method: 'POST', body: fd });
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			testResult = d.transcript ?? JSON.stringify(d);
		} catch (e) {
			testResult = e instanceof Error ? e.message : String(e);
		} finally {
			testBusy = false;
		}
	}

	onMount(load);
</script>

<div class="px-6 py-8 max-w-3xl">
	<div class="flex items-center gap-3 mb-2">
		<span class="text-2xl">🎙</span>
		<h2 class="text-lg font-semibold text-white">Голос → Текст (Whisper)</h2>
	</div>
	<p class="text-sm text-gray-400 mb-6">
		Параметры Groq Whisper хранятся в <code class="text-gray-500">backend/data/whisper_settings.json</code>.
		После сохранения применяются без перезапуска сервера. GROQ_API_KEY по-прежнему только из .env.
	</p>

	{#if loading}
		<p class="text-sm text-gray-500">Загрузка…</p>
	{:else}
		{#if err}
			<div class="mb-4 rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-2 text-sm text-red-200">{err}</div>
		{/if}
		{#if message}
			<div class="mb-4 rounded-lg border border-emerald-900/50 bg-emerald-950/30 px-4 py-2 text-sm text-emerald-200">{message}</div>
		{/if}

		<div class="flex flex-wrap items-center gap-2 mb-4 text-xs text-gray-500">
			{#if saved_to_disk}
				<span class="rounded bg-gray-800 px-2 py-0.5 text-gray-300">Есть сохранённый файл</span>
			{:else}
				<span class="rounded bg-gray-800 px-2 py-0.5 text-gray-400">Сейчас только .env (файла нет)</span>
			{/if}
			{#if updated_at}
				<span>Обновлено: {fmtUpdated(updated_at)}</span>
			{/if}
		</div>

		<div class="space-y-4 rounded-xl border border-gray-800 bg-gray-900/50 p-6">
			<div>
				<label for="wm" class="block text-xs font-medium uppercase tracking-wider text-gray-500 mb-1">Модель</label>
				<select
					id="wm"
					bind:value={model}
					class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
				>
					<option value="whisper-large-v3-turbo">whisper-large-v3-turbo (быстрее)</option>
					<option value="whisper-large-v3">whisper-large-v3 (точнее)</option>
				</select>
			</div>

			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<label for="wl" class="block text-xs font-medium uppercase tracking-wider text-gray-500 mb-1">Язык</label>
					<input
						id="wl"
						bind:value={language}
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
						placeholder="ru"
					/>
				</div>
				<div>
					<label for="wt" class="block text-xs font-medium uppercase tracking-wider text-gray-500 mb-1">Температура (0–1)</label>
					<input
						id="wt"
						type="number"
						min="0"
						max="1"
						step="0.1"
						bind:value={temperature}
						class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
					/>
				</div>
			</div>

			<div>
				<label for="wp" class="block text-xs font-medium uppercase tracking-wider text-gray-500 mb-1">
					Подсказка (prompt) — словарь терминов, имён, названий компаний
				</label>
				<textarea
					id="wp"
					bind:value={prompt}
					rows="8"
					class="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100 font-mono"
				></textarea>
			</div>

			<label class="flex items-center gap-2 cursor-pointer text-sm text-gray-300">
				<input type="checkbox" bind:checked={ffmpeg_preprocess} class="rounded border-gray-600" />
				Нормализация аудио через ffmpeg (16 kHz mono WAV перед API), если ffmpeg установлен на сервере
			</label>

			<div class="flex flex-wrap gap-2 pt-2">
				<button
					type="button"
					onclick={save}
					disabled={saving}
					class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
				>
					{saving ? 'Сохранение…' : 'Сохранить'}
				</button>
				<button
					type="button"
					onclick={resetToEnv}
					disabled={saving || !saved_to_disk}
					class="rounded-lg border border-gray-600 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 disabled:opacity-40"
				>
					Сбросить к .env
				</button>
			</div>
		</div>

		{#if defaults_from_env}
			<details class="mt-6 rounded-lg border border-gray-800 bg-gray-900/30 p-4">
				<summary class="cursor-pointer text-sm text-gray-400">Дефолты из окружения (без файла)</summary>
				<pre class="mt-3 overflow-x-auto text-xs text-gray-500">{JSON.stringify(defaults_from_env, null, 2)}</pre>
			</details>
		{/if}

		<div class="mt-8 rounded-xl border border-gray-800 bg-gray-900/50 p-6">
			<h3 class="text-sm font-medium text-white mb-2">Проверка транскрипции</h3>
			<p class="text-xs text-gray-500 mb-3">
				Загрузите фрагмент записи (webm, wav, mp3, ogg). Используются текущие настройки сверху — после сохранения или из .env.
			</p>
			<div class="flex flex-wrap items-center gap-2 mb-3">
				<input
					type="file"
					accept="audio/*,.webm,.wav,.mp3,.ogg,.m4a"
					onchange={(e) => {
						const f = e.currentTarget.files?.[0];
						testFile = f ?? null;
					}}
					class="text-sm text-gray-400"
				/>
				<button
					type="button"
					onclick={runTest}
					disabled={testBusy}
					class="rounded-lg bg-gray-700 px-3 py-1.5 text-sm text-white hover:bg-gray-600 disabled:opacity-50"
				>
					{testBusy ? 'Распознаю…' : 'Транскрибировать'}
				</button>
			</div>
			{#if testResult}
				<div class="rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-200 whitespace-pre-wrap">
					{testResult}
				</div>
			{/if}
		</div>
	{/if}
</div>
