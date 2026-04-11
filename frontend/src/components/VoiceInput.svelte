<script>
	import { onMount } from 'svelte';
	import { connect, sendText, sendAudio, onMessage, postCommand, getApiUrl } from '$lib/websocket.js';

	let { onResult } = $props();

	let recording = $state(false);
	let processing = $state(false);
	let transcript = $state('');
	let reply = $state('');
	let textInput = $state('');
	let status = $state('idle'); // idle | recording | processing | done | error
	let wsConnected = $state(false);
	let mediaRecorder = null;
	let audioChunks = [];
	let lastTraceId = $state(null);
	let feedbackSent = $state(null); // 'good' | 'bad' | null

	async function sendFeedback(fb) {
		if (!lastTraceId || feedbackSent) return;
		feedbackSent = fb;
		try {
			await fetch(`${getApiUrl()}/api/ops/feedback`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ trace_id: lastTraceId, feedback: fb })
			});
		} catch (e) { /* тихо */ }
	}

	onMount(() => {
		connect();
		const unsub = onMessage(handleMessage);
		return unsub;
	});

	function handleMessage(data) {
		if (data.type === 'connected') { wsConnected = true; return; }
		if (data.type === 'disconnected') { wsConnected = false; return; }

		if (data.type === 'processing') {
			status = 'processing';
			processing = true;
		}
		if (data.type === 'transcript') {
			transcript = data.text;
			status = 'processing';
		}
		if (data.type === 'intent') {
			processing = false;
			status = 'done';
			reply = data.reply;
			lastTraceId = data.trace_id || null;
			feedbackSent = null;
			onResult?.(data);
			setTimeout(() => { status = 'idle'; reply = ''; transcript = ''; lastTraceId = null; feedbackSent = null; }, 8000);
		}
		if (data.type === 'error') {
			processing = false;
			status = 'error';
			reply = data.message;
			setTimeout(() => { status = 'idle'; reply = ''; }, 4000);
		}
	}

	async function toggleRecording() {
		if (recording) {
			stopRecording();
		} else {
			await startRecording();
		}
	}

	async function startRecording() {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
			audioChunks = [];
			mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
			mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
			mediaRecorder.onstop = () => {
				const blob = new Blob(audioChunks, { type: 'audio/webm' });
				stream.getTracks().forEach(t => t.stop());
				status = 'processing';
				processing = true;
				transcript = 'Распознаю...';
				sendAudio(blob);
			};
			mediaRecorder.start();
			recording = true;
			status = 'recording';
		} catch (e) {
			status = 'error';
			reply = 'Нет доступа к микрофону. Разреши в браузере.';
			setTimeout(() => { status = 'idle'; reply = ''; }, 4000);
		}
	}

	function stopRecording() {
		mediaRecorder?.stop();
		recording = false;
	}

	async function submitText() {
		if (!textInput.trim() || processing) return;
		const text = textInput.trim();
		textInput = '';
		transcript = text;
		status = 'processing';
		processing = true;

		// Используем WebSocket если подключён, иначе HTTP
		if (wsConnected) {
			sendText(text);
		} else {
			try {
				const result = await postCommand(text);
				handleMessage({ type: 'intent', ...result });
			} catch {
				handleMessage({ type: 'error', message: 'Сервер недоступен' });
			}
		}
	}

	function handleKeydown(e) {
		if (e.key === 'Enter') submitText();
	}
</script>

<div class="bg-indigo-950 border-b border-indigo-800 px-6 py-3">
	<div class="flex items-center gap-4">

		<!-- Кнопка записи -->
		<button
			onclick={toggleRecording}
			disabled={processing}
			title={recording ? 'Остановить' : 'Записать голос'}
			class="flex items-center justify-center w-11 h-11 rounded-full shrink-0 transition-all duration-200
				{recording
					? 'bg-red-600 hover:bg-red-500 shadow-lg shadow-red-900 scale-110'
					: processing
						? 'bg-gray-700 cursor-not-allowed opacity-50'
						: 'bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-900 hover:scale-105'}"
		>
			{#if processing}
				<span class="text-white text-base">⟳</span>
			{:else if recording}
				<span class="text-white text-base">⏹</span>
			{:else}
				<span class="text-white text-base">🎙</span>
			{/if}
		</button>

		<!-- Центр -->
		<div class="flex-1">
			{#if status === 'recording'}
				<div class="text-indigo-200 text-sm font-medium mb-1">Говори... (нажми ⏹ чтобы остановить)</div>
				<div class="flex items-end gap-px h-4">
					{#each Array(20) as _, i}
						<div
							class="w-0.5 bg-red-400 rounded-full animate-bounce"
							style="animation-delay: {i * 0.05}s; height: {30 + Math.abs(Math.sin(i)) * 70}%"
						></div>
					{/each}
				</div>

			{:else if status === 'processing'}
				<div class="text-indigo-300 text-sm flex items-center gap-2">
					<span class="animate-spin inline-block">⟳</span> Обрабатываю...
				</div>
				{#if transcript && transcript !== 'Распознаю...'}
					<div class="text-xs text-indigo-400 mt-0.5 italic">"{transcript}"</div>
				{/if}

			{:else if status === 'done'}
				<div class="flex items-center gap-3">
					<div class="flex-1">
						<div class="text-green-300 text-sm font-medium">✓ {reply}</div>
						{#if transcript}
							<div class="text-xs text-indigo-400 mt-0.5 italic">"{transcript}"</div>
						{/if}
					</div>
					{#if lastTraceId}
						<div class="flex gap-1 shrink-0">
							<button
								onclick={() => sendFeedback('good')}
								disabled={!!feedbackSent}
								title="Правильно распознано"
								class="text-xs px-2 py-1 rounded-lg transition-colors
									{feedbackSent === 'good' ? 'bg-emerald-700 text-white' : 'bg-indigo-900 text-indigo-400 hover:bg-indigo-800 disabled:opacity-40'}"
							>👍</button>
							<button
								onclick={() => sendFeedback('bad')}
								disabled={!!feedbackSent}
								title="Неправильно распознано"
								class="text-xs px-2 py-1 rounded-lg transition-colors
									{feedbackSent === 'bad' ? 'bg-red-800 text-white' : 'bg-indigo-900 text-indigo-400 hover:bg-indigo-800 disabled:opacity-40'}"
							>👎</button>
						</div>
					{/if}
				</div>

			{:else if status === 'error'}
				<div class="text-red-300 text-sm">✕ {reply}</div>

			{:else}
				<input
					bind:value={textInput}
					onkeydown={handleKeydown}
					disabled={processing}
					placeholder="Скажи или напиши команду... (Enter)"
					class="w-full bg-indigo-900/40 border border-indigo-700/50 text-indigo-100 text-sm rounded-lg px-3 py-1.5 placeholder-indigo-500 focus:outline-none focus:border-indigo-400 transition-colors"
				/>
				<div class="text-xs text-indigo-600 mt-1">
					"создай лид компания АКМЕ" · "удали лид 3" · "покажи горячих" · "измени статус лида на переговоры"
				</div>
			{/if}
		</div>

		<!-- WS статус -->
		<div class="flex items-center gap-1.5 shrink-0">
			<div class="w-1.5 h-1.5 rounded-full {wsConnected ? 'bg-green-400' : 'bg-red-500'}"></div>
			<span class="text-xs text-indigo-500">{wsConnected ? 'онлайн' : 'офлайн'}</span>
		</div>

	</div>
</div>
