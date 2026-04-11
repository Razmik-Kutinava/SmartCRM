<script>
	import { onMount, onDestroy } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	import { severityBadge, severityLabel } from '$lib/opsCommon.js';

	const API = getApiUrl();

	let overview = $state(null);
	let loading = $state(true);
	let snapshotting = $state(false);
	let recomputing = $state(false);
	let err = $state('');
	let pollInterval = null;

	async function load() {
		try {
			const r = await fetch(`${API}/api/ops/overview`);
			if (!r.ok) throw new Error(await r.text());
			overview = await r.json();
			err = '';
		} catch (e) {
			err = String(e?.message || e);
		} finally {
			loading = false;
		}
	}

	async function takeSnapshot() {
		snapshotting = true;
		try {
			await fetch(`${API}/api/ops/snapshot`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ label: '' })
			});
			await load();
		} finally {
			snapshotting = false;
		}
	}

	async function recompute() {
		recomputing = true;
		try {
			await fetch(`${API}/api/ops/recompute`, { method: 'POST' });
			await load();
		} finally {
			recomputing = false;
		}
	}

	function pipeStatusClass(st) {
		if (st === 'ok') return 'border-emerald-900/80 bg-emerald-950/30';
		if (st === 'warn') return 'border-amber-800 bg-amber-950/30';
		return 'border-red-900 bg-red-950/40';
	}

	function pipeDot(st) {
		if (st === 'ok') return 'bg-emerald-500';
		if (st === 'warn') return 'bg-amber-500';
		return 'bg-red-500';
	}

	onMount(() => {
		load();
		pollInterval = setInterval(load, 8000);
	});
	onDestroy(() => clearInterval(pollInterval));
</script>

<div class="px-6 py-6 space-y-8 max-w-6xl">
	<!-- Быстрые входы в разделы -->
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
		<a href="/ops/intents/traces"
			class="block bg-indigo-950/40 border border-indigo-800/60 rounded-xl p-4 hover:bg-indigo-950/60 transition-colors">
			<div class="text-sm font-medium text-indigo-200">🎯 Интенты / Hermes</div>
			<p class="text-xs text-gray-400 mt-1">Трейсы, промпт, eval, история точности</p>
		</a>
		<a href="/ops/voice"
			class="block bg-gray-900 border border-gray-800 rounded-xl p-4 hover:bg-gray-800 transition-colors">
			<div class="text-sm font-medium text-gray-300">🎙 Голос / Whisper</div>
			<p class="text-xs text-gray-500 mt-1">Распознавание речи — в разработке</p>
		</a>
		<a href="/ops/agents"
			class="block bg-gray-900 border border-gray-800 rounded-xl p-4 hover:bg-gray-800 transition-colors">
			<div class="text-sm font-medium text-gray-300">🤖 Агенты</div>
			<p class="text-xs text-gray-500 mt-1">Промпты ролей, RAG — в разработке</p>
		</a>
		<a href="/ops/search"
			class="block bg-gray-900 border border-gray-800 rounded-xl p-4 hover:bg-gray-800 transition-colors">
			<div class="text-sm font-medium text-gray-300">🔍 Поиск</div>
			<p class="text-xs text-gray-500 mt-1">Парсеры, источники — в разработке</p>
		</a>
	</div>

	{#if loading}
		<p class="text-gray-500">Загрузка обзора…</p>
	{:else if err}
		<p class="text-red-400">{err}</p>
	{:else if overview}
		<!-- Пайплайн -->
		<section>
			<h2 class="text-sm font-medium text-gray-300 mb-3">Цепочка обработки команды</h2>
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
				{#each overview.pipeline as step}
					<div class="rounded-xl border p-4 {pipeStatusClass(step.status)}">
						<div class="flex items-center gap-2 mb-2">
							<span class="w-2 h-2 rounded-full {pipeDot(step.status)}"></span>
							<span class="text-sm font-medium text-white">{step.name}</span>
						</div>
						<p class="text-xs text-gray-400 leading-relaxed">{step.hint}</p>
					</div>
				{/each}
			</div>
		</section>

		<!-- LLM -->
		<section class="flex flex-wrap gap-4 items-center">
			<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm">
				<span class="text-gray-500">LLM:</span>
				<span class="text-white ml-2">{overview.llm?.active || '—'}</span>
				<span class="text-gray-500 ml-3">Groq</span>
				<span class="{overview.llm?.groq ? 'text-emerald-400' : 'text-red-400'} ml-1">{overview.llm?.groq ? 'да' : 'нет'}</span>
				<span class="text-gray-500 ml-3">Ollama</span>
				<span class="{overview.llm?.ollama ? 'text-emerald-400' : 'text-red-400'} ml-1">{overview.llm?.ollama ? 'да' : 'нет'}</span>
			</div>
			<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm">
				<span class="text-gray-500">Команд в буфере трейсов:</span>
				<span class="text-white font-semibold ml-2">{overview.stats?.total ?? 0}</span>
			</div>
		</section>

		<!-- Очередь превью -->
		<section>
			<div class="flex items-center justify-between mb-3">
				<h2 class="text-sm font-medium text-gray-300">Где нужна твоя реакция</h2>
				<a href="/ops/queue" class="text-sm text-indigo-400 hover:text-indigo-300">Вся очередь →</a>
			</div>
			{#if overview.queue?.preview?.length === 0}
				<p class="text-gray-500 text-sm">Открытых авто-задач нет. Нажми «Пересчитать очередь», если менялись трейсы.</p>
			{:else}
				<div class="space-y-2">
					{#each overview.queue.preview as item}
						<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
							<div>
								<span class="text-xs px-2 py-0.5 rounded {severityBadge(item.severity)}">{severityLabel(item.severity)}</span>
								<h3 class="text-white text-sm font-medium mt-2">{item.title}</h3>
								<p class="text-xs text-gray-400 mt-1">{item.detail}</p>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</section>

		<!-- Действия -->
		<section class="flex flex-wrap gap-3">
			<button
				type="button"
				onclick={recompute}
				disabled={recomputing}
				class="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white text-sm rounded-lg disabled:opacity-50"
			>
				{recomputing ? 'Считаем…' : 'Пересчитать очередь'}
			</button>
			<button
				type="button"
				onclick={takeSnapshot}
				disabled={snapshotting}
				class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg disabled:opacity-50"
			>
				{snapshotting ? 'Сохраняем…' : 'Зафиксировать снимок метрик'}
			</button>
			<a href="/ops/intents/history" class="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-700 rounded-lg">
				История «было — стало»
			</a>
		</section>
	{/if}
</div>
