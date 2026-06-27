<script>
	import {
		emailBodyParagraphs,
		emailMessageSnippet,
		sortThreadMessages,
		formatMessageDateShort,
		formatMessageDateFull,
		senderDisplayName,
		senderEmail,
	} from '$lib/email/emailThreadBody.js';

	let {
		thread = null,
		messages = [],
		loading = false,
		analyzeLoading = false,
		analyzeResult = null,
		analyzeError = '',
		replyBody = $bindable(''),
		replyLoading = false,
		approveLoading = false,
		onClose = () => {},
		onAnalyze = () => {},
		onApplyDraft = () => {},
		onReply = () => {},
	} = $props();

	let selectedIndex = $state(0);
	let lastThreadId = $state(null);

	const sorted = $derived(sortThreadMessages(messages));
	const activeMsg = $derived(sorted[selectedIndex] ?? null);
	const paragraphs = $derived(activeMsg ? emailBodyParagraphs(activeMsg.body || activeMsg.snippet) : []);

	$effect(() => {
		const tid = thread?.id;
		if (tid != null && tid !== lastThreadId) {
			lastThreadId = tid;
			selectedIndex = Math.max(0, sorted.length - 1);
		} else if (sorted.length && selectedIndex >= sorted.length) {
			selectedIndex = sorted.length - 1;
		}
	});

	let replyEl = $state(null);

	function focusReply() {
		replyEl?.focus();
		replyEl?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
	}

	function selectMessage(idx) {
		if (idx >= 0 && idx < sorted.length) selectedIndex = idx;
	}

	function prevMessage() {
		selectMessage(selectedIndex - 1);
	}

	function nextMessage() {
		selectMessage(selectedIndex + 1);
	}
</script>

{#if thread}
	<button class="fixed inset-0 bg-black/40 z-40 cursor-default" onclick={onClose} aria-label="Закрыть"></button>
	<div class="fixed inset-2 md:inset-4 lg:inset-8 z-50 flex pointer-events-none" data-testid="email-thread-view">
		<div class="bg-white rounded-2xl shadow-2xl w-full max-w-6xl mx-auto flex flex-col pointer-events-auto overflow-hidden border border-gray-200">

			<!-- toolbar -->
			<div class="flex items-center gap-2 px-4 py-2 border-b border-gray-100 flex-shrink-0 text-sm">
				<button type="button" class="px-3 py-1.5 rounded-lg hover:bg-gray-100 text-gray-800" onclick={focusReply}>
					Ответить
				</button>
				<button type="button" class="px-3 py-1.5 rounded-lg hover:bg-gray-100 text-gray-500" disabled title="Скоро">
					Переслать
				</button>
				<div class="flex-1"></div>
				<button type="button" onclick={onClose} class="w-8 h-8 rounded-lg hover:bg-gray-100 text-gray-500 text-xl leading-none" aria-label="Закрыть">×</button>
			</div>

			<div class="flex flex-1 min-h-0">
				<!-- центр: одно письмо -->
				<div class="flex-1 flex flex-col min-w-0 border-r border-gray-100">
					<div class="px-6 py-4 border-b border-gray-50 flex-shrink-0">
						<h2 class="text-lg font-bold text-gray-900 leading-snug pr-4">{thread.subject || 'Без темы'}</h2>
					</div>

					<div class="flex-1 overflow-y-auto min-h-0 px-6 py-4">
						{#if loading}
							<p class="text-gray-500 text-sm">Загрузка сообщений…</p>
						{:else if !activeMsg}
							<p class="text-gray-500 text-sm">Нет сообщений в этом треде.</p>
						{:else}
							<div class="flex items-start gap-3 mb-4">
								<div class="w-10 h-10 rounded-full bg-[#ffdb4d]/50 flex items-center justify-center text-sm font-bold text-gray-800 flex-shrink-0">
									{senderDisplayName(activeMsg.sender).charAt(0).toUpperCase()}
								</div>
								<div class="flex-1 min-w-0">
									<div class="flex flex-wrap items-baseline gap-x-2 gap-y-1">
										<span class="font-semibold text-gray-900">{senderDisplayName(activeMsg.sender)}</span>
										{#if senderEmail(activeMsg.sender)}
											<span class="text-sm text-gray-500">{senderEmail(activeMsg.sender)}</span>
										{/if}
									</div>
									<div class="text-sm text-gray-500 mt-0.5">{formatMessageDateFull(activeMsg.sentAt)}</div>
									{#if activeMsg.recipients}
										<div class="text-xs text-gray-500 mt-2">
											<span class="text-gray-400">Кому:</span> {activeMsg.recipients}
										</div>
									{/if}
									{#if activeMsg.cc}
										<div class="text-xs text-gray-500">
											<span class="text-gray-400">Копия:</span> {activeMsg.cc}
										</div>
									{/if}
								</div>
							</div>

							<div class="prose prose-sm max-w-none text-gray-800 space-y-4" data-testid="email-message-body">
								{#each paragraphs as para, i (i)}
									<p class="text-[15px] leading-relaxed m-0">{para}</p>
								{:else}
									<p class="text-gray-400 text-sm italic">(пустое письмо)</p>
								{/each}
							</div>

							<details class="mt-6 text-xs text-gray-400">
								<summary class="cursor-pointer hover:text-gray-600">Показать полный текст с цитатами</summary>
								<pre class="mt-2 p-3 bg-gray-50 rounded-lg whitespace-pre-wrap text-gray-600 text-xs leading-relaxed max-h-48 overflow-y-auto">{activeMsg.body || activeMsg.snippet || ''}</pre>
							</details>
						{/if}
					</div>

					<!-- ответ + анализ -->
					<div class="px-6 py-4 border-t border-gray-100 flex-shrink-0 space-y-3 bg-gray-50/50">
						<div class="flex flex-wrap items-center gap-2">
							<button
								type="button"
								onclick={onAnalyze}
								disabled={analyzeLoading || !messages.length}
								class="px-3 py-1.5 rounded-full bg-violet-100 text-violet-800 text-xs font-semibold hover:bg-violet-200 disabled:opacity-50"
							>{analyzeLoading ? 'Анализ…' : '✨ Анализ + черновик'}</button>
							{#if analyzeResult}
								<span class="text-xs px-2 py-1 rounded-full bg-gray-200 text-gray-700">{analyzeResult.category_label}</span>
								<button type="button" onclick={onApplyDraft} class="text-xs text-[#0066cc] hover:underline">В ответ ↓</button>
							{/if}
						</div>
						{#if analyzeError}<p class="text-xs text-red-600">{analyzeError}</p>{/if}
						{#if analyzeResult?.draft?.body}
							<div class="rounded-xl border border-violet-200 bg-violet-50 px-3 py-2 text-xs text-gray-700">
								<div class="font-semibold text-violet-900 mb-1">{analyzeResult.draft.subject}</div>
								<p class="whitespace-pre-wrap line-clamp-3">{analyzeResult.draft.body}</p>
							</div>
						{/if}
						<div class="relative">
							<textarea
								bind:this={replyEl}
								bind:value={replyBody}
								class="w-full h-24 rounded-xl bg-white border border-gray-200 px-4 py-3 pr-28 text-sm text-gray-900 resize-none focus:outline-none focus:ring-2 focus:ring-[#ffdb4d]/80"
								placeholder="Написать ответ…"
							></textarea>
							<button
								type="button"
								onclick={onReply}
								disabled={replyLoading || approveLoading || !replyBody.trim()}
								class="absolute bottom-3 right-3 px-4 py-1.5 rounded-lg bg-[#ffdb4d] hover:bg-[#ffcc00] text-xs font-semibold text-gray-900 disabled:opacity-50"
							>Ответить</button>
						</div>
					</div>
				</div>

				<!-- правая колонка: письма на тему -->
				<aside class="w-56 md:w-64 flex-shrink-0 flex flex-col bg-gray-50/80" data-testid="email-thread-sidebar">
					<div class="px-3 py-3 border-b border-gray-200 flex items-center justify-between">
						<span class="text-xs font-semibold text-gray-600 uppercase tracking-wide">Письма на тему</span>
						<div class="flex gap-1 text-xs">
							<button type="button" class="text-[#0066cc] disabled:text-gray-300" disabled={selectedIndex <= 0} onclick={prevMessage}>‹ Пред</button>
							<button type="button" class="text-[#0066cc] disabled:text-gray-300" disabled={selectedIndex >= sorted.length - 1} onclick={nextMessage}>След ›</button>
						</div>
					</div>
					<div class="flex-1 overflow-y-auto py-1">
						{#if loading}
							<p class="px-3 text-xs text-gray-400">…</p>
						{:else}
							{#each sorted as msg, idx (msg.id)}
								<button
									type="button"
									class="w-full text-left px-3 py-2.5 border-l-2 transition-colors
										{idx === selectedIndex ? 'border-[#ffcc00] bg-white shadow-sm' : 'border-transparent hover:bg-white/70'}"
									onclick={() => selectMessage(idx)}
									data-testid="thread-msg-{msg.id}"
								>
									<div class="text-sm font-medium text-gray-900 truncate">{senderDisplayName(msg.sender)}</div>
									<div class="text-xs text-gray-500 mt-0.5">{formatMessageDateShort(msg.sentAt)}</div>
									<div class="text-xs text-gray-500 mt-1 line-clamp-2 leading-snug">
										{emailMessageSnippet(msg.body || msg.snippet)}
									</div>
								</button>
							{/each}
						{/if}
					</div>
					<div class="px-3 py-2 border-t border-gray-200 text-xs text-gray-500">
						{sorted.length} {sorted.length === 1 ? 'письмо' : sorted.length < 5 ? 'письма' : 'писем'}
					</div>
				</aside>
			</div>
		</div>
	</div>
{/if}
