<script>
	import '../app.css';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { getApiUrl, connect, sendText, sendAudio, onMessage } from '$lib/websocket.js';
	import { goto } from '$app/navigation';

	let { children } = $props();

	const API = getApiUrl();

	const navItems = [
		{ href: '/', label: 'Дашборд', icon: '⬡' },
		{ href: '/leads', label: 'Лиды', icon: '⬢' },
		{ href: '/email', label: 'Email', icon: '✉️' },
		{ href: '/agents', label: 'Агенты', icon: '⬣' },
		{ href: '/rag', label: 'База знаний', icon: '⬤' },
		{ href: '/search', label: 'Поиск', icon: '◎' },
		{ href: '/analytics', label: 'Аналитика', icon: '◈' },
		{ href: '/ops', label: 'Ops / Качество', icon: '◉' },
		{ href: '/settings', label: 'Настройки', icon: '◎' },
	];

	const AGENT_NAMES = {
		analyst: 'Аналитик',
		strategist: 'Стратег',
		economist: 'Экономист',
		marketer: 'Маркетолог',
		tech_specialist: 'Тех. спец',
	};

	let agents = $state([
		{ id: 'analyst',       name: 'Аналитик',   implemented: false },
		{ id: 'strategist',    name: 'Стратег',     implemented: false },
		{ id: 'economist',     name: 'Экономист',   implemented: false },
		{ id: 'marketer',      name: 'Маркетолог',  implemented: false },
		{ id: 'tech_specialist', name: 'Тех. спец', implemented: false },
	]);

	// ── Глобальный голосовой ввод ────────────────────────────────────────────────
	let voice_recording  = $state(false);
	let voice_processing = $state(false);
	let voice_status     = $state('idle');   // idle | recording | processing | done | error
	let voice_transcript = $state('');
	let voice_reply      = $state('');
	let voice_text       = $state('');
	let voice_ws         = $state(false);
	let voice_traceId    = $state(null);
	let voice_feedback   = $state(null);
	let mediaRecorder    = null;
	let audioChunks      = [];

	// Контекст текущей страницы для Hermes
	function pageContext() {
		const path = $page.url.pathname;
		if (path.startsWith('/leads'))    return 'Страница: Лиды';
		if (path.startsWith('/search'))   return 'Страница: Поиск';
		if (path.startsWith('/email'))    return 'Страница: Email';
		if (path.startsWith('/rag'))      return 'Страница: База знаний';
		if (path.startsWith('/agents'))   return 'Страница: Агенты';
		if (path.startsWith('/analytics')) return 'Страница: Аналитика';
		if (path.startsWith('/ops'))      return 'Страница: Ops';
		if (path === '/')                 return 'Страница: Дашборд';
		return '';
	}

	onMount(async () => {
		// Загружаем статус агентов
		try {
			const r = await fetch(`${API}/api/ops/agents`);
			if (r.ok) {
				const d = await r.json();
				agents = (d.agents || []).map(a => ({
					id: a.id,
					name: AGENT_NAMES[a.id] || a.id,
					implemented: !!a.implemented,
				}));
			}
		} catch { /* тихо */ }

		// Подключаем WebSocket и слушаем события
		connect();
		const unsub = onMessage((data) => {
			if (data.type === 'connected')    { voice_ws = true; return; }
			if (data.type === 'disconnected') { voice_ws = false; return; }
			if (data.type === 'processing')   { voice_status = 'processing'; voice_processing = true; }
			if (data.type === 'transcript')   { voice_transcript = data.text; voice_status = 'processing'; }
			if (data.type === 'intent') {
				voice_processing = false;
				voice_status = 'done';
				voice_reply = data.reply || '';
				voice_traceId = data.trace_id || null;
				voice_feedback = null;
				// Навигация по интенту
				_handleIntentNav(data);
				setTimeout(() => {
					voice_status = 'idle'; voice_reply = ''; voice_transcript = '';
					voice_traceId = null; voice_feedback = null;
				}, 7000);
			}
			if (data.type === 'error') {
				voice_processing = false;
				voice_status = 'error';
				voice_reply = data.message || 'Ошибка';
				setTimeout(() => { voice_status = 'idle'; voice_reply = ''; }, 4000);
			}
		});
		return unsub;
	});

	function _handleIntentNav(data) {
		const intent = data.intent;
		// При создании/показе лидов — переходим на страницу лидов
		if (['create_lead','list_leads','update_lead','delete_lead'].includes(intent)) {
			if (!$page.url.pathname.startsWith('/leads')) goto('/leads');
		}
		// При поиске — переходим на поиск
		if (intent === 'search_web' && !$page.url.pathname.startsWith('/search')) {
			goto('/search');
		}
	}

	async function voiceToggle() {
		if (voice_recording) {
			mediaRecorder?.stop();
			voice_recording = false;
		} else {
			try {
				const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
				audioChunks = [];
				mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
				mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
				mediaRecorder.onstop = () => {
					const blob = new Blob(audioChunks, { type: 'audio/webm' });
					stream.getTracks().forEach(t => t.stop());
					voice_status = 'processing'; voice_processing = true;
					voice_transcript = 'Распознаю...';
					sendAudio(blob);
				};
				mediaRecorder.start();
				voice_recording = true;
				voice_status = 'recording';
			} catch {
				voice_status = 'error';
				voice_reply = 'Нет доступа к микрофону';
				setTimeout(() => { voice_status = 'idle'; voice_reply = ''; }, 3000);
			}
		}
	}

	async function voiceSubmitText() {
		if (!voice_text.trim() || voice_processing) return;
		const t = voice_text.trim();
		voice_text = '';
		voice_transcript = t;
		voice_status = 'processing'; voice_processing = true;
		// Добавляем контекст страницы к тексту команды
		const ctx = pageContext();
		const full = ctx ? `[${ctx}] ${t}` : t;
		sendText(full);
	}

	function voiceKeydown(e) { if (e.key === 'Enter') voiceSubmitText(); }

	async function sendVoiceFeedback(fb) {
		if (!voice_traceId || voice_feedback) return;
		voice_feedback = fb;
		try {
			await fetch(`${API}/api/ops/feedback`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ trace_id: voice_traceId, feedback: fb }),
			});
		} catch { /* тихо */ }
	}
</script>

<div class="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">

	<!-- Sidebar -->
	<aside class="w-56 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">

		<!-- Logo -->
		<div class="px-4 py-4 border-b border-gray-800">
			<div class="flex items-center gap-2.5">
				<div class="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center font-bold text-white text-sm">S</div>
				<div>
					<div class="font-semibold text-sm text-white leading-tight">SmartCRM</div>
					<div class="text-xs text-gray-500 leading-tight">AI отдел продаж</div>
				</div>
			</div>
		</div>

		<!-- Nav -->
		<nav class="flex-1 px-2 py-3 space-y-0.5">
			{#each navItems as item}
				<a
					href={item.href}
					class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all duration-150
						{$page.url.pathname === item.href
							? 'bg-indigo-600 text-white font-medium'
							: 'text-gray-400 hover:text-white hover:bg-gray-800'}"
				>
					<span class="text-xs opacity-70">{item.icon}</span>
					{item.label}
				</a>
			{/each}
		</nav>

		<!-- Agents status -->
		<div class="px-3 py-3 border-t border-gray-800">
			<div class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Агенты</div>
			<div class="space-y-1.5">
			{#each agents as agent}
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<div class="w-1.5 h-1.5 rounded-full transition-colors {agent.implemented ? 'bg-green-400' : 'bg-gray-600'}"></div>
						<span class="text-xs text-gray-400">{agent.name}</span>
					</div>
					<span class="text-xs {agent.implemented ? 'text-green-600' : 'text-gray-600'}">
						{agent.implemented ? 'активен' : 'ожидает'}
					</span>
				</div>
			{/each}
			</div>
		</div>

	</aside>

	<!-- Main content -->
	<div class="flex-1 flex flex-col overflow-hidden">

		<!-- ── Глобальная голосовая панель ── -->
		<div class="bg-indigo-950/80 border-b border-indigo-900/60 px-4 py-2 shrink-0 backdrop-blur-sm">
			<div class="flex items-center gap-3">

				<!-- Кнопка микрофона -->
				<button
					onclick={voiceToggle}
					disabled={voice_processing}
					title={voice_recording ? 'Стоп' : 'Голосовая команда'}
					class="flex items-center justify-center w-9 h-9 rounded-full shrink-0 transition-all
						{voice_recording
							? 'bg-red-600 hover:bg-red-500 shadow-md shadow-red-900 scale-110 animate-pulse'
							: voice_processing
								? 'bg-gray-700 cursor-not-allowed opacity-50'
								: 'bg-indigo-600 hover:bg-indigo-500 shadow-sm hover:scale-105'}"
				>
					{#if voice_processing}
						<span class="text-white text-sm animate-spin inline-block">⟳</span>
					{:else if voice_recording}
						<span class="text-white text-sm">⏹</span>
					{:else}
						<span class="text-white text-sm">🎙</span>
					{/if}
				</button>

				<!-- Центральная зона -->
				<div class="flex-1 min-w-0">
					{#if voice_status === 'recording'}
						<div class="flex items-center gap-2">
							<span class="text-xs text-red-300 font-medium">Говори...</span>
							<div class="flex items-end gap-px h-3">
								{#each Array(16) as _, i}
									<div class="w-0.5 bg-red-400 rounded-full animate-bounce"
										style="animation-delay: {i * 0.05}s; height: {40 + Math.abs(Math.sin(i)) * 60}%"></div>
								{/each}
							</div>
						</div>

					{:else if voice_status === 'processing'}
						<div class="text-xs text-indigo-300">
							⟳ Обрабатываю...
							{#if voice_transcript && voice_transcript !== 'Распознаю...'}
								<span class="text-indigo-500 italic ml-1">"{voice_transcript}"</span>
							{/if}
						</div>

					{:else if voice_status === 'done'}
						<div class="flex items-center gap-2 min-w-0">
							<span class="text-xs text-green-300 font-medium truncate">✓ {voice_reply}</span>
							{#if voice_transcript}
								<span class="text-xs text-indigo-500 italic truncate hidden sm:block">"{voice_transcript}"</span>
							{/if}
							{#if voice_traceId}
								<div class="flex gap-1 shrink-0">
									<button onclick={() => sendVoiceFeedback('good')} disabled={!!voice_feedback}
										class="text-xs px-1.5 py-0.5 rounded {voice_feedback==='good' ? 'bg-emerald-700 text-white' : 'bg-indigo-900 text-indigo-400 hover:bg-indigo-800 disabled:opacity-40'}">👍</button>
									<button onclick={() => sendVoiceFeedback('bad')} disabled={!!voice_feedback}
										class="text-xs px-1.5 py-0.5 rounded {voice_feedback==='bad' ? 'bg-red-800 text-white' : 'bg-indigo-900 text-indigo-400 hover:bg-indigo-800 disabled:opacity-40'}">👎</button>
								</div>
							{/if}
						</div>

					{:else if voice_status === 'error'}
						<div class="text-xs text-red-300">✕ {voice_reply}</div>

					{:else}
						<input
							bind:value={voice_text}
							onkeydown={voiceKeydown}
							disabled={voice_processing}
							placeholder="Скажи или напиши команду... — «найди лид Ромашка» · «прибыль Яндекса 2025» · «напиши письмо Альфа»"
							class="w-full bg-indigo-900/30 border border-indigo-800/40 text-indigo-100 text-xs rounded-lg px-3 py-1.5 placeholder-indigo-600 focus:outline-none focus:border-indigo-500"
						/>
					{/if}
				</div>

				<!-- Контекст страницы + WS статус -->
				<div class="flex items-center gap-2 shrink-0 text-xs">
					<span class="text-indigo-700 hidden md:block">{pageContext()}</span>
					<div class="flex items-center gap-1">
						<div class="w-1.5 h-1.5 rounded-full {voice_ws ? 'bg-green-400' : 'bg-red-500'}"></div>
						<span class="text-indigo-600">{voice_ws ? 'ws' : 'off'}</span>
					</div>
				</div>

			</div>
		</div>

		{@render children()}
	</div>

</div>
