<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	import { readLeadsCache } from '$lib/leadsStorage.js';

	const API = getApiUrl();

	// Лиды — сразу из кэша, потом из API
	let leads = $state(readLeadsCache().slice(0, 5));
	let agentActivity = $state([]);
	let agentsStatus = $state([]);
	let stats = $state(null);

	onMount(async () => {
		// Загружаем лиды
		try {
			const r = await fetch(`${API}/api/leads`);
			if (r.ok) {
				const all = await r.json();
				leads = all.slice(0, 5);
				const total = all.length;
				const hot = all.filter(l => (l.score || 0) >= 70).length;
				const inWork = all.filter(l => ['Квалифицирован', 'КП отправлено', 'Переговоры'].includes(l.stage)).length;
				const budgets = all
					.map(l => parseInt(String(l.budget || '').replace(/\D/g, ''), 10))
					.filter(n => !isNaN(n) && n > 0);
				const budgetSum = budgets.reduce((s, n) => s + n, 0);
				stats = {
					total,
					hot,
					inWork,
					budgetFmt: budgetSum >= 1_000_000
						? (budgetSum / 1_000_000).toFixed(1) + 'M ₽'
						: budgetSum > 0 ? budgetSum.toLocaleString('ru-RU') + ' ₽' : '—',
				};
			}
		} catch { /* нет API — показываем кэш */ }

		// Загружаем статусы агентов
		try {
			const r = await fetch(`${API}/api/ops/agents`);
			if (r.ok) {
				const d = await r.json();
				agentsStatus = d.agents || [];
			}
		} catch {}

		// Загружаем трейсы как «активность агентов»
		try {
			const r = await fetch(`${API}/api/ops/traces?limit=5`);
			if (r.ok) {
				const d = await r.json();
				const traces = Array.isArray(d) ? d : (d.traces || []);
				agentActivity = traces.slice(0, 4).map(t => ({
					agent: agentFromIntent(t.intent),
					action: traceAction(t),
					time: fmtAge(t.ts),
				}));
			}
		} catch {}
	});

	function agentFromIntent(intent) {
		if (!intent) return 'Hermes';
		if (intent.includes('lead')) return 'Аналитик';
		if (intent.includes('email')) return 'Маркетолог';
		if (intent.includes('task')) return 'Аналитик';
		if (intent === 'run_analysis') return 'Стратег';
		return 'Hermes';
	}

	function traceAction(t) {
		const intentMap = {
			create_lead: `Создан лид${t.slots?.company ? ' ' + t.slots.company : ''}`,
			update_lead: `Обновлён лид${t.slots?.company ? ' ' + t.slots.company : ''}`,
			delete_lead: `Удалён лид`,
			list_leads: 'Запрос списка лидов',
			write_email: `Написано письмо${t.slots?.target ? ' для ' + t.slots.target : ''}`,
			create_task: `Задача: ${t.slots?.title || '—'}`,
			noop: 'Нераспознанная команда',
		};
		return intentMap[t.intent] || t.intent || 'Команда';
	}

	function fmtAge(ts) {
		if (!ts) return '';
		const diff = Math.floor((Date.now() / 1000) - ts);
		if (diff < 60) return `${diff}с назад`;
		if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`;
		if (diff < 86400) return `${Math.floor(diff / 3600)} ч назад`;
		return `${Math.floor(diff / 86400)} дн назад`;
	}

	function stageColor(stage) {
		const map = {
			'Новый': 'bg-gray-700 text-gray-300',
			'Квалифицирован': 'bg-blue-900 text-blue-300',
			'КП отправлено': 'bg-yellow-900 text-yellow-300',
			'Переговоры': 'bg-indigo-900 text-indigo-300',
			'Выигран': 'bg-green-900 text-green-300',
			'Проигран': 'bg-red-900 text-red-300',
		};
		return map[stage] || 'bg-gray-700 text-gray-300';
	}

	function scoreColor(score) {
		if (score >= 80) return 'text-green-400';
		if (score >= 60) return 'text-yellow-400';
		return 'text-red-400';
	}
</script>

<!-- Header -->
<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900 shrink-0">
	<div>
		<h1 class="text-lg font-semibold text-white">Дашборд</h1>
		<p class="text-xs text-gray-500">SmartCRM · AI отдел продаж</p>
	</div>
	<div class="flex items-center gap-2">
		<a href="/leads" class="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg transition-colors">
			Все лиды
		</a>
		<a href="/agents" class="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg transition-colors">
			🤖 Агенты
		</a>
	</div>
</div>

<div class="flex-1 overflow-y-auto px-6 py-5 space-y-6">

	<!-- Stats -->
	{#if stats}
		<div class="grid grid-cols-4 gap-4">
			<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
				<div class="text-xs text-gray-500 mb-1">Всего лидов</div>
				<div class="text-2xl font-bold text-white">{stats.total}</div>
			</div>
			<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
				<div class="text-xs text-gray-500 mb-1">Горячих (≥70)</div>
				<div class="text-2xl font-bold text-green-400">{stats.hot}</div>
			</div>
			<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
				<div class="text-xs text-gray-500 mb-1">Сделок в работе</div>
				<div class="text-2xl font-bold text-white">{stats.inWork}</div>
			</div>
			<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
				<div class="text-xs text-gray-500 mb-1">Бюджет (сумма)</div>
				<div class="text-2xl font-bold text-white">{stats.budgetFmt}</div>
			</div>
		</div>
	{:else}
		<div class="grid grid-cols-4 gap-4">
			{#each Array(4) as _}
				<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 animate-pulse h-20"></div>
			{/each}
		</div>
	{/if}

	<div class="grid grid-cols-3 gap-5">

		<!-- Последние лиды -->
		<div class="col-span-2 bg-gray-900 border border-gray-800 rounded-xl">
			<div class="flex items-center justify-between px-5 py-3.5 border-b border-gray-800">
				<span class="text-sm font-medium text-white">Последние лиды</span>
				<a href="/leads" class="text-xs text-indigo-400 hover:text-indigo-300">Все лиды →</a>
			</div>
			<div class="divide-y divide-gray-800">
				{#each leads as lead}
					<a href="/leads/{lead.id}" class="flex items-center gap-4 px-5 py-3 hover:bg-gray-800/50 transition-colors">
						<div class="flex-1 min-w-0">
							<div class="text-sm font-medium text-white truncate">{lead.company}</div>
							<div class="text-xs text-gray-500">{lead.contact !== '—' ? lead.contact : '—'}</div>
						</div>
						<div class="flex items-center gap-3">
							<span class="text-xs px-2 py-0.5 rounded-full {stageColor(lead.stage)}">{lead.stage}</span>
							<span class="text-xs font-bold {scoreColor(lead.score || 50)}">{lead.score || 50}</span>
							<span class="text-xs text-gray-600">{lead.source || '—'}</span>
						</div>
					</a>
				{/each}
				{#if leads.length === 0}
					<div class="px-5 py-8 text-center text-sm text-gray-500">Лидов пока нет. Создай первый голосом!</div>
				{/if}
			</div>
		</div>

		<!-- Активность -->
		<div class="bg-gray-900 border border-gray-800 rounded-xl">
			<div class="px-5 py-3.5 border-b border-gray-800">
				<span class="text-sm font-medium text-white">Активность агентов</span>
			</div>
			<div class="px-4 py-3 space-y-4">
				{#if agentActivity.length}
					{#each agentActivity as activity}
						<div>
							<div class="flex items-center gap-2 mb-0.5">
								<div class="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
								<span class="text-xs font-medium text-indigo-400">{activity.agent}</span>
							</div>
							<p class="text-xs text-gray-300 pl-3.5">{activity.action}</p>
							<p class="text-xs text-gray-600 pl-3.5 mt-0.5">{activity.time}</p>
						</div>
					{/each}
				{:else}
					<p class="text-xs text-gray-600">Нет активности. Начни голосовую команду!</p>
				{/if}
			</div>

			<!-- Статусы агентов -->
			{#if agentsStatus.length}
				<div class="px-5 py-3 border-t border-gray-800">
					<div class="text-xs text-gray-600 mb-2 uppercase tracking-wider">Агенты</div>
					<div class="space-y-1.5">
						{#each agentsStatus as a}
							<div class="flex items-center justify-between">
								<span class="text-xs text-gray-400">{a.id}</span>
								<div class="flex items-center gap-1.5">
									<div class="w-1.5 h-1.5 rounded-full {a.implemented ? 'bg-green-400' : 'bg-gray-600'}"></div>
									<span class="text-xs {a.implemented ? 'text-green-500' : 'text-gray-600'}">
										{a.implemented ? 'готов' : '—'}
									</span>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>

	</div>

	<!-- Быстрые действия -->
	<div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
		<div class="text-sm font-medium text-white mb-3">Быстрые действия</div>
		<div class="flex flex-wrap gap-2">
			<a href="/leads" class="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">+ Новый лид</a>
			<a href="/agents" class="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">🤖 Задача агенту</a>
			<a href="/ops/intents/traces" class="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">📡 Трейсы</a>
			<a href="/ops/voice" class="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">🎙 Настройка голоса</a>
			<a href="/ops/agents" class="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">🧠 Промпты агентов</a>
		</div>
	</div>

</div>
