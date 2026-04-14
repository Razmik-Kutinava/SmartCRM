<script>
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { page } from '$app/stores';
	import { enrichLeadForCard, getLeadById } from '$lib/leadsStorage.js';
	import { fetchEmailAccounts, fetchEmailThreads } from '$lib/emailStorage.js';

	let lead    = $state(null);
	let notFound = $state(false);

	function sync() {
		const id = get(page).params.id;
		const raw = getLeadById(id);
		lead     = raw ? enrichLeadForCard(raw) : null;
		notFound = !raw;
	}

	onMount(() => {
		sync();
		return page.subscribe(() => sync());
	});

	let activeTab = $state('overview');
	let noteText  = $state('');

	const activityHistory = $derived(lead?.history ?? []);
	const leadTasks       = $derived(lead?.tasks   ?? []);

	// ─── Агенты ─────────────────────────────────────────────────
	let agentRunning  = $state('');
	let agentResult   = $state(null);
	let agentError    = $state('');
	let agentTask     = $state('');
	let showAgentTask = $state(false);
	let pendingAgent  = $state('');
	let agentHistory  = $state([]);
	let showHistory   = $state(false);
	let feedbackSent  = $state('');     // 'good' | 'bad' | ''
	let feedbackNote  = $state('');
	let showBadNote   = $state(false);

	const AGENT_LIST = [
		{ key: 'marketer',   label: 'Маркетолог', desc: 'Прочитает переписку → напишет письмо', icon: '✉️' },
		{ key: 'analyst',    label: 'Аналитик',   desc: 'Пересчитает скоринг и даст рекомендации', icon: '📊' },
		{ key: 'strategist', label: 'Стратег',    desc: 'Предложит следующий шаг по сделке', icon: '🧠' },
		{ key: 'economist',  label: 'Экономист',  desc: 'Рассчитает ROI и обоснует бюджет', icon: '💰' },
	];

	function startAgent(agentKey) {
		pendingAgent  = agentKey;
		agentTask     = '';
		agentResult   = null;
		agentError    = '';
		showAgentTask = true;
	}

	async function runAgent() {
		if (!lead) return;
		agentRunning  = pendingAgent;
		agentResult   = null;
		agentError    = '';
		feedbackSent  = '';
		showAgentTask = false;
		try {
			const r = await fetch('/api/agents/email/run', {
				method:  'POST',
				headers: { 'Content-Type': 'application/json' },
				body:    JSON.stringify({ lead_id: lead.id, agent: pendingAgent, task: agentTask }),
			});
			if (!r.ok) throw new Error(await r.text());
			agentResult = await r.json();
		} catch (e) { agentError = '❌ ' + e.message; }
		finally { agentRunning = ''; }
	}

	async function sendFeedback(type) {
		if (!agentResult?.run_id) return;
		feedbackSent = type;
		if (type === 'bad') { showBadNote = true; return; }
		await _postFeedback(type, '');
	}

	async function submitBadNote() {
		showBadNote = false;
		await _postFeedback('bad', feedbackNote);
		feedbackNote = '';
	}

	async function _postFeedback(type, note) {
		try {
			await fetch('/api/agents/email/feedback', {
				method:  'POST',
				headers: { 'Content-Type': 'application/json' },
				body:    JSON.stringify({ run_id: agentResult.run_id, feedback: type, note }),
			});
		} catch (e) { console.error(e); }
	}

	async function markFewShot() {
		if (!agentResult?.run_id) return;
		try {
			await fetch('/api/agents/email/few-shots', {
				method:  'POST',
				headers: { 'Content-Type': 'application/json' },
				body:    JSON.stringify({ run_id: agentResult.run_id }),
			});
			feedbackSent = 'good';
		} catch (e) { console.error(e); }
	}

	async function loadHistory() {
		if (!lead) return;
		try {
			const r = await fetch(`/api/agents/email/history/${lead.id}`);
			if (r.ok) agentHistory = await r.json();
		} catch (e) { console.error(e); }
		showHistory = true;
	}

	// ─── Email-таб ──────────────────────────────────────────────
	let emailAccounts      = $state([]);
	let leadThreads        = $state([]);
	let loadingEmails      = $state(false);
	let emailsLoaded       = $state(false);

	// compose
	let showCompose    = $state(false);
	let composeTo      = $state('');
	let composeSubject = $state('');
	let composeBody    = $state('');
	let sendingNew     = $state(false);
	let composeError   = $state('');
	let composeSent    = $state(false);

	// тред
	let selectedThread  = $state(null);
	let threadMessages  = $state([]);
	let loadingMsgs     = $state(false);
	let replyBody       = $state('');
	let replyLoading    = $state(false);

	// Загружаем письма только когда переходим на таб
	async function loadEmails() {
		if (emailsLoaded || !lead) return;
		loadingEmails = true;
		try {
			const [accs, threads] = await Promise.all([
				fetchEmailAccounts(),
				fetchEmailThreads({ lead_id: lead.id }),
			]);
			emailAccounts = accs;
			leadThreads   = threads;
			emailsLoaded  = true;
		} catch (e) {
			console.error('Ошибка загрузки писем лида:', e);
		} finally {
			loadingEmails = false;
		}
	}

	function onTabChange(tab) {
		activeTab = tab;
		if (tab === 'emails') loadEmails();
	}

	// ─── Compose ────────────────────────────────────────────────
	function openCompose(to = '', subject = '', body = '') {
		composeTo      = to || lead?.email || '';
		composeSubject = subject;
		composeBody    = body;
		composeError   = '';
		composeSent    = false;
		showCompose    = true;
	}

	async function sendEmail() {
		composeError = '';
		if (!composeTo || !composeSubject) { composeError = 'Заполни кому и тему'; return; }
		sendingNew = true;
		try {
			const r = await fetch('/api/email/send', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					to: [composeTo],
					subject: composeSubject,
					body: composeBody,
					lead_id: lead?.id,
				}),
			});
			if (!r.ok) throw new Error(await r.text());
			composeSent  = true;
			emailsLoaded = false;          // сбросить кэш
			await loadEmails();            // перезагрузить
			setTimeout(() => { showCompose = false; }, 1200);
		} catch (e) { composeError = '❌ ' + e.message; }
		finally { sendingNew = false; }
	}

	// ─── Thread detail ──────────────────────────────────────────
	async function openThread(thread) {
		selectedThread = thread;
		threadMessages = [];
		replyBody      = '';
		loadingMsgs    = true;
		try {
			const r = await fetch(`/api/email/threads/${thread.id}/messages`);
			if (r.ok) threadMessages = await r.json();
		} catch (e) { console.error(e); }
		finally { loadingMsgs = false; }
	}

	function closeThread() { selectedThread = null; threadMessages = []; replyBody = ''; }

	async function sendReply() {
		if (!replyBody.trim() || !selectedThread) return;
		replyLoading = true;
		try {
			const r = await fetch('/api/email/reply', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ thread_id: selectedThread.id, body: replyBody }),
			});
			if (!r.ok) throw new Error(await r.text());
			const data = await r.json();
			threadMessages = [...threadMessages, data.message];
			replyBody = '';
		} catch (e) { alert('Ошибка: ' + e.message); }
		finally { replyLoading = false; }
	}

	// ─── helpers ────────────────────────────────────────────────
	function fmtTime(iso) {
		if (!iso) return '—';
		const d = new Date(iso);
		if (d.toDateString() === new Date().toDateString())
			return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
		return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
	}
	function fmtFull(iso) {
		if (!iso) return '—';
		return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
	}
</script>

{#if notFound}
	<div class="flex flex-col items-center justify-center flex-1 p-8 text-center">
		<p class="text-lg text-white mb-2">Лид не найден</p>
		<a href="/leads" class="text-indigo-400 hover:text-indigo-300 text-sm">← К списку лидов</a>
	</div>
{:else if lead}
	<!-- Header -->
	<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900 shrink-0">
		<div class="flex items-center gap-3">
			<a href="/leads" class="text-gray-500 hover:text-white transition-colors text-sm">← Лиды</a>
			<span class="text-gray-700">/</span>
			<span class="text-sm text-white font-medium">{lead.company}</span>
		</div>
		<div class="flex items-center gap-2">
			<button class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">🔍 Исследовать</button>
			<button
				class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors"
				onclick={() => { onTabChange('emails'); openCompose(lead.email, ''); }}
			>✉️ Написать</button>
			<button class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">📊 Анализ</button>
			<button class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors">🎙 Голос</button>
		</div>
	</div>

	<div class="flex-1 overflow-hidden flex">
		<!-- Left: Lead info -->
		<div class="w-80 border-r border-gray-800 overflow-y-auto bg-gray-900 shrink-0">
			<div class="p-5 space-y-5">
				<div>
					<div class="text-lg font-bold text-white">{lead.company}</div>
					<div class="text-sm text-gray-400 mt-0.5">{lead.contact} · {lead.position}</div>
					<div class="flex items-center gap-2 mt-2">
						<span class="px-2 py-0.5 bg-blue-900 text-blue-300 text-xs rounded-full font-medium">{lead.stage}</span>
						<span class="text-green-400 font-bold text-sm">{lead.score}/100</span>
					</div>
				</div>

				<div class="space-y-2">
					<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Контакты</div>
					<div class="space-y-1.5 text-sm">
						<div class="flex items-center gap-2 text-gray-300">
							<span class="text-gray-600 w-4">✉</span>
							{#if lead.email && lead.email !== '—'}
								<button class="text-indigo-400 hover:text-indigo-300 transition-colors text-left"
									onclick={() => { onTabChange('emails'); openCompose(lead.email); }}>
									{lead.email}
								</button>
							{:else}
								<span class="text-gray-500">—</span>
							{/if}
						</div>
						<div class="flex items-center gap-2 text-gray-300">
							<span class="text-gray-600 w-4">✆</span> {lead.phone}
						</div>
						<div class="flex items-center gap-2 text-gray-300">
							<span class="text-gray-600 w-4">🌐</span> {lead.website}
						</div>
					</div>
				</div>

				<div class="space-y-2">
					<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Детали</div>
					<div class="space-y-2 text-sm">
						{#each [
							['Отрасль',        lead.industry],
							['Сотрудники',     lead.employees],
							['Город',          lead.city],
							['Источник',       lead.source],
							['Бюджет',         lead.budget],
							['Ответственный',  lead.responsible],
							['Создан',         lead.created],
							['Следующий звонок', lead.nextCall],
						] as [label, value]}
							<div class="flex justify-between">
								<span class="text-gray-500">{label}</span>
								<span class="text-gray-300">{value}</span>
							</div>
						{/each}
					</div>
				</div>

				{#if lead.description}
					<div class="space-y-1.5">
						<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Описание</div>
						<p class="text-sm text-gray-300 leading-relaxed">{lead.description}</p>
					</div>
				{/if}

				<div class="space-y-2">
					<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Сменить этап</div>
					<div class="grid grid-cols-2 gap-1">
						{#each ['Новый', 'Квалифицирован', 'КП отправлено', 'Переговоры', 'Выигран', 'Проигран'] as stage}
							<button class="px-2 py-1 text-xs rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors text-left">
								{stage}
							</button>
						{/each}
					</div>
				</div>
			</div>
		</div>

		<!-- Right: Tabs -->
		<div class="flex-1 flex flex-col overflow-hidden">
			<div class="flex gap-4 px-6 pt-4 border-b border-gray-800 shrink-0">
				{#each [['overview', 'Обзор'], ['tasks', 'Задачи'], ['emails', 'Письма'], ['agents', 'Агенты'], ['checko', 'Checko']] as [id, label]}
					<button
						onclick={() => onTabChange(id)}
						class="pb-3 text-sm transition-colors border-b-2 {activeTab === id
							? 'text-white border-indigo-500'
							: 'text-gray-500 border-transparent hover:text-gray-300'}"
					>{label}</button>
				{/each}
			</div>

			<div class="flex-1 overflow-y-auto p-6">

				<!-- ── ОБЗОР ── -->
				{#if activeTab === 'overview'}
					<div class="mb-5">
						<textarea bind:value={noteText} placeholder="Добавить заметку или команду агентам..."
							class="w-full bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-lg px-4 py-3 placeholder-gray-600 focus:outline-none focus:border-indigo-500 resize-none h-20"></textarea>
						<div class="flex gap-2 mt-2">
							<button class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors">Добавить заметку</button>
							<button class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">Поручить агенту</button>
						</div>
					</div>
					<div class="space-y-3">
						{#each activityHistory as item}
							<div class="flex gap-3">
								<div class="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5
									{item.type === 'agent' ? 'bg-indigo-900 text-indigo-300' : 'bg-gray-800 text-gray-400'} text-xs">
									{item.type === 'call' ? '✆' : item.type === 'agent' ? '⬡' : '✎'}
								</div>
								<div class="flex-1">
									<div class="flex items-center gap-2 mb-0.5">
										<span class="text-xs font-medium {item.type === 'agent' ? 'text-indigo-400' : 'text-gray-400'}">{item.author}</span>
										<span class="text-xs text-gray-600">{item.date}</span>
									</div>
									<p class="text-sm text-gray-300">{item.text}</p>
								</div>
							</div>
						{/each}
					</div>

				<!-- ── ЗАДАЧИ ── -->
				{:else if activeTab === 'tasks'}
					<div class="space-y-2">
						{#each leadTasks as task}
							<div class="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
								<div class="w-4 h-4 rounded border {task.status === 'done' ? 'bg-green-500 border-green-500' : 'border-gray-600'} flex items-center justify-center shrink-0">
									{#if task.status === 'done'}<span class="text-white text-xs">✓</span>{/if}
								</div>
								<div class="flex-1">
									<div class="text-sm {task.status === 'done' ? 'line-through text-gray-500' : 'text-gray-200'}">{task.title}</div>
									<div class="text-xs text-gray-600">{task.due}</div>
								</div>
							</div>
						{/each}
						<button class="w-full p-3 border border-dashed border-gray-700 rounded-lg text-sm text-gray-500 hover:text-gray-300 hover:border-gray-500 transition-colors">
							+ Добавить задачу
						</button>
					</div>

				<!-- ── ПИСЬМА ── -->
				{:else if activeTab === 'emails'}
					<div class="flex flex-col h-full gap-4">

						<!-- шапка таба -->
						<div class="flex items-center justify-between">
							<div>
								<h3 class="text-sm font-semibold text-white">Переписка с {lead.company}</h3>
								{#if lead.email && lead.email !== '—'}
									<p class="text-xs text-gray-500 mt-0.5">{lead.email}</p>
								{/if}
							</div>
							<button
								class="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors"
								onclick={() => openCompose(lead.email)}
							>✏ Написать письмо</button>
						</div>

						<!-- нет аккаунта -->
						{#if !loadingEmails && emailAccounts.length === 0}
							<div class="flex-1 flex flex-col items-center justify-center text-center py-10">
								<div class="text-3xl mb-3">✉️</div>
								<p class="text-gray-400 text-sm mb-3">Почта не подключена</p>
								<a href="/email" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors">
									Подключить почту →
								</a>
							</div>

						<!-- загрузка -->
						{:else if loadingEmails}
							<div class="text-gray-500 text-sm flex items-center gap-2">
								<span class="animate-spin">⟳</span> Загрузка писем...
							</div>

						<!-- нет писем -->
						{:else if leadThreads.length === 0}
							<div class="flex-1 flex flex-col items-center justify-center text-center py-10">
								<div class="text-3xl mb-3">✉️</div>
								<p class="text-gray-400 text-sm mb-1">Писем пока нет</p>
								<p class="text-gray-600 text-xs mb-4">Переписки с этим лидом ещё не было</p>
								<button
									class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors"
									onclick={() => openCompose(lead.email)}
								>✏ Написать первое письмо</button>
							</div>

						<!-- список тредов -->
						{:else}
							<div class="space-y-2">
								{#each leadThreads as thread (thread.id)}
									<button
										class="w-full text-left flex items-start gap-3 px-4 py-3 rounded-xl border border-gray-800 bg-gray-900
											   hover:bg-gray-800 hover:border-indigo-700 transition-colors group"
										onclick={() => openThread(thread)}
									>
										<div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5
											{thread.category === 'outbound' ? 'bg-indigo-800/60 text-indigo-300' : 'bg-gray-700 text-gray-300'}">
											{thread.category === 'outbound' ? '↑' : '↓'}
										</div>
										<div class="flex-1 min-w-0">
											<div class="flex items-baseline justify-between gap-2">
												<span class="text-sm font-semibold text-white truncate group-hover:text-indigo-300 transition-colors">
													{thread.subject || 'Без темы'}
												</span>
												<span class="text-xs text-gray-500 flex-shrink-0">{fmtTime(thread.lastMessageAt)}</span>
											</div>
											<p class="text-xs text-gray-400 truncate mt-0.5">{thread.snippet || ''}</p>
										</div>
									</button>
								{/each}
							</div>
						{/if}
					</div>

				<!-- ── АГЕНТЫ ── -->
				{:else if activeTab === 'agents'}
					<div class="space-y-4">
						<div class="flex items-center justify-between">
							<p class="text-sm text-gray-400">Агент читает переписку с клиентом и действует по настроенным правилам</p>
							<a href="/ops/email-agents" class="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">⚙ Настроить правила →</a>
						</div>

						{#if agentError}
							<div class="px-4 py-3 rounded-xl bg-red-950 border border-red-800 text-red-200 text-sm">{agentError}</div>
						{/if}

						<!-- кнопки агентов -->
						<div class="space-y-2">
							{#each AGENT_LIST as item}
								<div class="flex items-center gap-3 p-4 bg-gray-900 border border-gray-800 hover:border-indigo-800/60 rounded-xl transition-colors">
									<span class="text-xl flex-shrink-0">{item.icon}</span>
									<div class="flex-1 min-w-0">
										<div class="text-sm font-medium text-white">{item.label}</div>
										<div class="text-xs text-gray-500">{item.desc}</div>
									</div>
									<button
										onclick={() => startAgent(item.key)}
										disabled={agentRunning === item.key}
										class="flex-shrink-0 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white rounded-lg transition-colors disabled:bg-gray-700"
									>
										{agentRunning === item.key ? '⟳ Думает...' : 'Запустить'}
									</button>
								</div>
							{/each}
						</div>

						<!-- результат агента -->
						{#if agentResult}
							<div class="bg-gray-900 border border-indigo-800/50 rounded-2xl p-5 space-y-4">
								<!-- заголовок результата -->
								<div class="flex items-center justify-between flex-wrap gap-2">
									<span class="text-xs font-semibold text-indigo-400 uppercase tracking-wide">
										{AGENT_LIST.find(a => a.key === agentResult.agent)?.label} · результат
									</span>
									<div class="flex items-center gap-2 text-xs text-gray-600">
										<span>Тредов: {agentResult.threads_analyzed}</span>
										<span>·</span>
										<span>Правил: {agentResult.intents_applied}</span>
										{#if agentResult.few_shots_used > 0}
											<span>·</span>
											<span class="text-indigo-500">✦ few-shot</span>
										{/if}
									</div>
								</div>

								<!-- письмо -->
								{#if agentResult.result?.first_email}
									<div class="bg-gray-950 border border-gray-800 rounded-xl p-4">
										<div class="text-xs text-gray-500 mb-1">Тема:</div>
										<div class="text-sm font-semibold text-white mb-3">{agentResult.result.first_email.subject}</div>
										<div class="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{agentResult.result.first_email.body}</div>
										<button
											onclick={() => openCompose(lead.email, agentResult.result.first_email.subject, agentResult.result.first_email.body)}
											class="mt-3 px-4 py-1.5 rounded-lg bg-indigo-600 text-xs font-semibold text-white hover:bg-indigo-500 transition-colors"
										>↗ Открыть в compose</button>
									</div>
								{/if}

								{#if agentResult.result?.value_hook}
									<div class="text-sm text-gray-300 border-l-2 border-indigo-600 pl-3">
										<span class="text-xs text-gray-500 block mb-0.5">Крючок внимания</span>
										{agentResult.result.value_hook}
									</div>
								{/if}

								{#if agentResult.result?.summary}
									<p class="text-xs text-gray-500 italic">{agentResult.result.summary}</p>
								{/if}

								{#if agentResult.result?.touch_sequence?.length}
									<div>
										<div class="text-xs text-gray-500 mb-2">📅 План касаний</div>
										<div class="space-y-1">
											{#each agentResult.result.touch_sequence as t}
												<div class="text-xs text-gray-300">
													<span class="text-indigo-400 w-12 inline-block">День {t.day}</span>
													<span class="text-gray-600 mr-2">{t.channel}</span>
													{t.action}
												</div>
											{/each}
										</div>
									</div>
								{/if}

								<!-- 👍/👎 обратная связь -->
								<div class="border-t border-gray-800 pt-3 flex items-center gap-3 flex-wrap">
									<span class="text-xs text-gray-500">Качество ответа:</span>
									{#if feedbackSent === 'good'}
										<span class="text-xs text-green-400">✓ Отлично! Добавлено как пример для обучения.</span>
										<button onclick={markFewShot} class="text-xs text-indigo-400 hover:text-indigo-300 underline">+ В few-shot</button>
									{:else if feedbackSent === 'bad'}
										<span class="text-xs text-red-400">✗ Записано. Агент учтёт это.</span>
									{:else}
										<button onclick={() => sendFeedback('good')}
											class="flex items-center gap-1 px-3 py-1 rounded-lg bg-gray-800 hover:bg-green-900/40 hover:border-green-700 border border-gray-700 text-xs text-gray-300 hover:text-green-300 transition-colors">
											👍 Хорошо
										</button>
										<button onclick={() => sendFeedback('bad')}
											class="flex items-center gap-1 px-3 py-1 rounded-lg bg-gray-800 hover:bg-red-900/40 hover:border-red-700 border border-gray-700 text-xs text-gray-300 hover:text-red-300 transition-colors">
											👎 Плохо
										</button>
									{/if}
								</div>

								<!-- комментарий к плохому ответу -->
								{#if showBadNote}
									<div class="space-y-2">
										<textarea bind:value={feedbackNote}
											class="w-full h-16 rounded-xl bg-gray-950 border border-gray-700 px-3 py-2 text-sm text-white resize-none focus:outline-none focus:border-red-500 transition-colors"
											placeholder="Что именно не так? (опционально)"></textarea>
										<div class="flex gap-2">
											<button onclick={submitBadNote}
												class="px-4 py-1.5 rounded-lg bg-red-700 text-xs text-white hover:bg-red-600 transition-colors">
												Отправить отзыв
											</button>
											<button onclick={() => { showBadNote = false; feedbackNote = ''; }}
												class="px-4 py-1.5 rounded-lg bg-gray-800 text-xs text-gray-300 hover:bg-gray-700 transition-colors">
												Пропустить
											</button>
										</div>
									</div>
								{/if}
							</div>
						{/if}

						<!-- история запусков -->
						<div class="flex items-center justify-between">
							<button onclick={loadHistory}
								class="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
								{showHistory ? '▲ Скрыть историю' : '▼ История запусков агентов'}
							</button>
						</div>

						{#if showHistory}
							<div class="space-y-2">
								{#if agentHistory.length === 0}
									<p class="text-xs text-gray-600">История пуста.</p>
								{:else}
									{#each agentHistory as h (h.id)}
										<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
											<div class="flex items-center justify-between gap-2">
												<div class="flex items-center gap-2">
													<span class="text-xs font-medium text-gray-300">{h.agentName}</span>
													{#if h.feedback === 'good'}
														<span class="text-xs text-green-500">👍</span>
													{:else if h.feedback === 'bad'}
														<span class="text-xs text-red-500">👎</span>
													{/if}
													{#if h.isFewShot}
														<span class="text-xs text-indigo-400">✦</span>
													{/if}
												</div>
												<span class="text-xs text-gray-600">{h.created}</span>
											</div>
											{#if h.task}
												<p class="text-xs text-gray-500 mt-1">Задача: {h.task}</p>
											{/if}
											{#if h.emailSubject}
												<p class="text-xs text-gray-400 mt-1 truncate">✉ {h.emailSubject}</p>
											{/if}
										</div>
									{/each}
								{/if}
							</div>
						{/if}
					</div>
				{/if}

				<!-- ── CHECKO ── -->
				{#if activeTab === 'checko'}
					{@const ck = lead.checko || {}}
					{@const co = ck.company || {}}
					{@const fin = ck.financials || {}}
					{@const tech = ck.tech || {}}
					{@const risks = co.risk_flags || {}}

					{#if !lead.inn && !Object.keys(ck).length}
						<div class="text-center py-12 text-gray-600 text-sm">
							Нет данных Checko. Лид нужно создать через Лидогенератор.
						</div>
					{:else}
						<div class="space-y-4">

							<!-- ЕГРЮЛ -->
							<div class="bg-gray-950 rounded-xl border border-gray-800 p-4">
								<h3 class="text-sm font-medium text-gray-300 mb-3">📋 ЕГРЮЛ</h3>
								<div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
									{#each [
										['ИНН', lead.inn], ['ОГРН', lead.ogrn], ['КПП', co.kpp],
										['Статус', co.status], ['Дата рег.', co.registration_date],
										['ОКВЭД', co.okved ? co.okved + (co.okved_name ? ' — ' + co.okved_name : '') : null],
										['МСП', co.smb_category], ['Сотрудников', co.employees_count],
										['Филиалов', co.branch_count], ['Тип управления', co.management_type],
									].filter(([,v]) => v != null && v !== '') as [label, value]}
										<div class="flex justify-between gap-2">
											<span class="text-gray-500 shrink-0">{label}</span>
											<span class="text-gray-300 text-right text-xs">{value}</span>
										</div>
									{/each}
								</div>
								{#if co.address}
									<div class="mt-2 pt-2 border-t border-gray-800 text-xs text-gray-500">Адрес: <span class="text-gray-300">{co.address}</span></div>
								{/if}
								{#if risks.is_bad_supplier || risks.has_disqualified_leader || risks.is_mass_address}
									<div class="flex flex-wrap gap-1.5 mt-2">
										{#if risks.is_bad_supplier}<span class="text-xs px-2 py-0.5 rounded-full bg-red-900 text-red-300">⛔ Недобросовестный поставщик</span>{/if}
										{#if risks.has_disqualified_leader}<span class="text-xs px-2 py-0.5 rounded-full bg-orange-900 text-orange-300">⚠ Дисквалифицированный руководитель</span>{/if}
										{#if risks.is_mass_address}<span class="text-xs px-2 py-0.5 rounded-full bg-yellow-900 text-yellow-300">📍 Массовый адрес</span>{/if}
									</div>
								{/if}
							</div>

							<!-- Контакты -->
							{#if co.phones?.length || co.emails?.length || lead.website}
								<div class="bg-gray-950 rounded-xl border border-gray-800 p-4">
									<h3 class="text-sm font-medium text-gray-300 mb-3">📞 Контакты</h3>
									<div class="space-y-1.5 text-sm">
										{#if lead.website}
											<div class="flex justify-between"><span class="text-gray-500">Сайт</span><a href="https://{lead.website}" target="_blank" class="text-indigo-400 hover:underline">{lead.website}</a></div>
										{/if}
										{#each (co.phones || []) as ph}
											<div class="flex justify-between"><span class="text-gray-500">📞</span><a href="tel:{ph}" class="text-green-400 hover:underline font-mono text-xs">{ph}</a></div>
										{/each}
										{#each (co.emails || []) as em}
											<div class="flex justify-between"><span class="text-gray-500">✉</span><span class="text-gray-300 font-mono text-xs">{em}</span></div>
										{/each}
									</div>
								</div>
							{/if}

							<!-- Учредители + связанные компании -->
							{#if co.founders?.length || co.related_companies?.length}
								<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
									{#if co.founders?.length}
										<div class="bg-gray-950 rounded-xl border border-gray-800 p-4">
											<h3 class="text-xs font-medium text-gray-400 mb-2">👥 Учредители ({co.founders.length})</h3>
											{#each co.founders as f}
												<div class="flex justify-between text-xs py-0.5">
													<span class="text-gray-300">{f.name}</span>
													<span class="text-gray-600">{f.type === 'LEGAL' ? '🏢' : '👤'} {f.share_percent ? f.share_percent + '%' : ''}</span>
												</div>
											{/each}
										</div>
									{/if}
									{#if co.related_companies?.length}
										<div class="bg-gray-950 rounded-xl border border-purple-900/30 p-4">
											<h3 class="text-xs font-medium text-purple-400 mb-2">🔗 Связанные ({co.related_companies.length})</h3>
											{#each co.related_companies as rc}
												<div class="text-xs py-0.5">
													<span class="text-gray-300">{rc.name_full || rc.name}</span>
													{#if rc.inn}<span class="text-gray-600 ml-1">· {rc.inn}</span>{/if}
												</div>
											{/each}
										</div>
									{/if}
								</div>
							{/if}

							<!-- Финансы -->
							{#if fin.revenue}
								<div class="bg-gray-950 rounded-xl border border-gray-800 p-4">
									<h3 class="text-sm font-medium text-gray-300 mb-3">💰 Финансы {fin.finance_year ? '(' + fin.finance_year + ' г.)' : ''}</h3>
									<div class="grid grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
										{#each [['Выручка', fin.revenue],['Прибыль', fin.profit],['Активы', fin.assets],['Расходы', fin.expense],['Кред. задолж.', fin.debt]].filter(([,v]) => v) as [l, v]}
											<div class="flex justify-between">
												<span class="text-gray-500">{l}</span>
												<span class="text-white text-xs">{v >= 1e9 ? (v/1e9).toFixed(1) + ' млрд' : v >= 1e6 ? (v/1e6).toFixed(1) + ' млн' : v?.toLocaleString('ru')} ₽</span>
											</div>
										{/each}
									</div>
									{#if fin.revenue_series?.length > 1}
										<div class="mt-2 pt-2 border-t border-gray-800 flex flex-wrap gap-3">
											{#each fin.revenue_series as [yr, rev]}
												<span class="text-xs text-gray-500">{yr}: <span class="text-gray-300">{rev >= 1e9 ? (rev/1e9).toFixed(1) + ' млрд' : (rev/1e6).toFixed(1) + ' млн'} ₽</span></span>
											{/each}
										</div>
									{/if}
								</div>
							{/if}

							<!-- Юр. данные: ФССП / Арбитраж / Госзакупки / Проверки / Федресурс -->
							<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
								{#if fin.contracts_count > 0}
									<div class="bg-gray-950 rounded-xl border border-green-900/30 p-3">
										<div class="text-xs font-medium text-green-400 mb-2">🏛️ Госзакупки · {fin.contracts_count}</div>
										{#each (fin.contracts || []) as c}
											<div class="text-xs pb-1 border-b border-gray-800 mb-1">
												<div class="text-gray-300 line-clamp-1">{c.subject || c.number}</div>
												<div class="text-green-400">{c.amount >= 1e6 ? (c.amount/1e6).toFixed(1) + ' млн' : c.amount} ₽ · {c.date}</div>
											</div>
										{/each}
									</div>
								{/if}
								{#if fin.enforcement_count > 0}
									<div class="bg-gray-950 rounded-xl border border-red-900/30 p-3">
										<div class="text-xs font-medium text-red-400 mb-2">🚨 ФССП · {fin.enforcement_count}</div>
										{#each (fin.enforcements || []) as e}
											<div class="text-xs pb-1 border-b border-gray-800 mb-1">
												<div class="text-gray-400 line-clamp-1">{e.reason || e.number}</div>
												<div class="text-red-400">{e.amount >= 1e6 ? (e.amount/1e6).toFixed(1) + ' млн' : e.amount} ₽ · {e.date}</div>
											</div>
										{/each}
									</div>
								{/if}
								{#if fin.arbitration_count > 0}
									<div class="bg-gray-950 rounded-xl border border-yellow-900/30 p-3">
										<div class="text-xs font-medium text-yellow-400 mb-2">⚖️ Арбитраж · {fin.arbitration_count}</div>
										{#each (fin.arbitration_cases || []) as c}
											<div class="text-xs pb-1 border-b border-gray-800 mb-1">
												<span class="text-gray-400">{c.number}</span>
												{#if c.amount}<span class="text-yellow-400 ml-2">{c.amount >= 1e6 ? (c.amount/1e6).toFixed(1) + ' млн' : c.amount} ₽</span>{/if}
											</div>
										{/each}
									</div>
								{/if}
								{#if fin.inspection_count > 0}
									<div class="bg-gray-950 rounded-xl border border-gray-700 p-3">
										<div class="text-xs font-medium text-gray-400 mb-2">🔍 Проверки ГП · {fin.inspection_count}</div>
										{#each (fin.inspections || []) as i}
											<div class="text-xs pb-1 border-b border-gray-800 mb-1">
												<div class="text-gray-400">{i.authority}</div>
												<div class="text-gray-600">{i.date} {i.violations ? '· Нарушения' : ''}</div>
											</div>
										{/each}
									</div>
								{/if}
								{#if fin.fedresurs_count > 0}
									<div class="bg-gray-950 rounded-xl border border-orange-900/30 p-3">
										<div class="text-xs font-medium text-orange-400 mb-2">📋 Федресурс · {fin.fedresurs_count}</div>
										{#each (fin.fedresurs_messages || []) as m}
											<div class="text-xs pb-1 border-b border-gray-800 mb-1">
												<span class="text-orange-400">{m.type}</span> · <span class="text-gray-600">{m.date}</span>
												{#if m.text}<div class="text-gray-500 line-clamp-1">{m.text}</div>{/if}
											</div>
										{/each}
									</div>
								{/if}
								{#if fin.has_bankruptcy}
									<div class="bg-gray-950 rounded-xl border border-red-800/50 p-3">
										<div class="text-xs font-medium text-red-400 mb-2">⛔ Банкротство ЕФРСБ</div>
										{#each (fin.bankruptcy_messages || []) as m}
											<div class="text-xs pb-1"><span class="text-red-400">{m.type}</span> · <span class="text-gray-600">{m.date}</span></div>
										{/each}
									</div>
								{/if}
							</div>

							<!-- Лицензии -->
							{#if co.licenses?.length}
								<div class="bg-gray-950 rounded-xl border border-gray-800 p-4">
									<h3 class="text-xs font-medium text-gray-400 mb-2">📜 Лицензии ({co.licenses.length})</h3>
									{#each co.licenses as lic}<div class="text-xs text-gray-400 py-0.5">· {lic}</div>{/each}
								</div>
							{/if}

							<!-- Технологии -->
							{#if tech.count > 0 || tech.all?.length}
								<div class="bg-gray-950 rounded-xl border border-gray-800 p-4">
									<h3 class="text-xs font-medium text-gray-400 mb-2">💻 Технологии · {tech.count ?? 0}</h3>
									{#if tech.crm?.length}<div class="text-xs text-indigo-400 mb-1">CRM: {tech.crm.join(', ')}</div>{/if}
									<div class="flex flex-wrap gap-1">
										{#each (tech.all || []) as t}<span class="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">{t}</span>{/each}
									</div>
								</div>
							{/if}

						</div>
					{/if}
				{/if}

			</div>
		</div>
	</div>
{:else}
	<div class="flex flex-col items-center justify-center flex-1 p-8 text-gray-500 text-sm">Загрузка…</div>
{/if}

<!-- ═══ МОДАЛ: ЗАДАЧА ДЛЯ АГЕНТА ════════════════════════════ -->
{#if showAgentTask}
	<button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={() => showAgentTask = false} aria-label="Закрыть"></button>
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
		<div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-md pointer-events-auto">
			<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
				<h3 class="text-sm font-semibold text-white">
					{AGENT_LIST.find(a => a.key === pendingAgent)?.icon}
					{AGENT_LIST.find(a => a.key === pendingAgent)?.label}
				</h3>
				<button onclick={() => showAgentTask = false} class="text-gray-500 hover:text-white text-xl">&times;</button>
			</div>
			<div class="px-6 py-4 space-y-3">
				<p class="text-xs text-gray-500">Агент прочитает переписку с клиентом и применит настроенные правила. Можешь добавить конкретную задачу:</p>
				<textarea
					bind:value={agentTask}
					class="w-full h-24 rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white resize-none focus:outline-none focus:border-indigo-500 transition-colors"
					placeholder="Напр: 'Клиент интересовался ценой, предложи скидку 10%'"
				></textarea>
				<p class="text-xs text-gray-600">Если оставишь пустым — агент сам решит что нужно</p>
			</div>
			<div class="px-6 pb-5 flex gap-3">
				<button onclick={() => showAgentTask = false} class="flex-1 rounded-xl bg-gray-800 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors">Отмена</button>
				<button onclick={runAgent} class="flex-1 rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors">
					▶ Запустить
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- ═══ МОДАЛ: COMPOSE ════════════════════════════════════════ -->
{#if showCompose}
	<button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={() => showCompose = false} aria-label="Закрыть"></button>
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
		<div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-lg pointer-events-auto flex flex-col">
			<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
				<h2 class="text-sm font-semibold text-white">
					✏ Письмо {lead?.company ? '→ ' + lead.company : ''}
				</h2>
				<button onclick={() => showCompose = false} class="text-gray-500 hover:text-white text-xl">&times;</button>
			</div>
			<div class="px-6 py-4 space-y-0">
				<div class="flex items-center gap-3 border-b border-gray-800 py-3">
					<span class="text-xs text-gray-500 w-12 flex-shrink-0">Кому:</span>
					<input bind:value={composeTo} class="flex-1 bg-transparent text-sm text-white outline-none placeholder-gray-600" placeholder="email@example.com" />
				</div>
				<div class="flex items-center gap-3 border-b border-gray-800 py-3">
					<span class="text-xs text-gray-500 w-12 flex-shrink-0">Тема:</span>
					<input bind:value={composeSubject} class="flex-1 bg-transparent text-sm text-white outline-none placeholder-gray-600" placeholder="Тема письма" />
				</div>
				<textarea
					bind:value={composeBody}
					class="w-full h-48 bg-transparent text-sm text-white outline-none resize-none placeholder-gray-600 leading-relaxed py-4"
					placeholder="Текст письма..."
				></textarea>
				{#if composeError}<div class="text-red-400 text-xs pb-2">{composeError}</div>{/if}
				{#if composeSent}<div class="text-green-400 text-xs pb-2">✅ Письмо отправлено!</div>{/if}
			</div>
			<div class="px-6 pb-5 flex items-center justify-between border-t border-gray-800 pt-4">
				<button onclick={() => showCompose = false} class="text-sm text-gray-500 hover:text-white transition-colors">Отмена</button>
				<button onclick={sendEmail} disabled={sendingNew || !composeTo || !composeSubject}
					class="px-6 py-2 rounded-xl bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 transition-colors">
					{sendingNew ? 'Отправка...' : '↑ Отправить'}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- ═══ МОДАЛ: ТРЕД ═══════════════════════════════════════════ -->
{#if selectedThread}
	<button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={closeThread} aria-label="Закрыть"></button>
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
		<div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col pointer-events-auto">

			<div class="flex items-start gap-3 px-6 py-4 border-b border-gray-800 flex-shrink-0">
				<div class="flex-1 min-w-0">
					<h2 class="text-sm font-semibold text-white">{selectedThread.subject || 'Без темы'}</h2>
					<div class="flex items-center gap-2 mt-1">
						<span class="text-xs text-gray-500">{fmtFull(selectedThread.lastMessageAt)}</span>
						<span class="text-xs text-gray-600">·</span>
						<span class="text-xs text-gray-500">{threadMessages.length} сообщ.</span>
					</div>
				</div>
				<button onclick={closeThread} class="text-gray-500 hover:text-white text-2xl leading-none flex-shrink-0">&times;</button>
			</div>

			<div class="flex-1 overflow-y-auto px-6 py-4 space-y-4 min-h-0">
				{#if loadingMsgs}
					<div class="flex items-center gap-2 text-gray-500 text-sm"><span class="animate-spin">⟳</span> Загрузка...</div>
				{:else if threadMessages.length === 0}
					<p class="text-gray-500 text-sm">Нет сообщений.</p>
				{:else}
					{#each threadMessages as msg (msg.id)}
						<div class="rounded-xl border px-4 py-3
							{msg.direction === 'outbound' ? 'border-indigo-800/60 bg-indigo-950/30 ml-6' : 'border-gray-800 bg-gray-900 mr-6'}">
							<div class="flex items-center justify-between mb-2 gap-2">
								<div class="flex items-center gap-2 min-w-0">
									<div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0
										{msg.direction === 'outbound' ? 'bg-indigo-700 text-indigo-200' : 'bg-gray-700 text-gray-300'}">
										{msg.direction === 'outbound' ? '↑' : '↓'}
									</div>
									<span class="text-xs font-semibold text-gray-200 truncate">{msg.sender || '—'}</span>
								</div>
								<span class="text-xs text-gray-500 flex-shrink-0">{fmtFull(msg.sentAt)}</span>
							</div>
							{#if msg.recipients && msg.direction === 'outbound'}
								<p class="text-xs text-gray-600 mb-2">Кому: {msg.recipients}</p>
							{/if}
							<p class="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{msg.body || msg.snippet || '(нет текста)'}</p>
						</div>
					{/each}
				{/if}
			</div>

			<div class="px-6 py-4 border-t border-gray-800 flex-shrink-0">
				<div class="relative">
					<textarea
						bind:value={replyBody}
						class="w-full h-20 rounded-xl bg-gray-900 border border-gray-700 px-4 py-3 pr-28 text-sm text-white
							   resize-none focus:outline-none focus:border-indigo-500 transition-colors"
						placeholder="Написать ответ..."
					></textarea>
					<button
						onclick={sendReply}
						disabled={replyLoading || !replyBody.trim()}
						class="absolute bottom-3 right-3 px-4 py-1.5 rounded-lg bg-indigo-600 text-xs font-semibold text-white
							   hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 transition-colors"
					>{replyLoading ? '...' : '↑ Ответить'}</button>
				</div>
			</div>
		</div>
	</div>
{/if}
