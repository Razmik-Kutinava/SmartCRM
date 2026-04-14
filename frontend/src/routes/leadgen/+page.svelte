<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	const API = getApiUrl();

	// ── Режимы ────────────────────────────────────────────────────────────────
	const MODES = [
		{ id: 'direct',   label: 'По ИНН / названию', icon: '🏢' },
		{ id: 'portrait', label: 'По портрету',        icon: '🎯' },
		{ id: 'cluster',  label: 'Кластер / Холдинг',  icon: '🕸' },
		{ id: 'news',     label: 'Новости рынка',       icon: '📰' },
		{ id: 'limits',   label: 'API Лимиты',          icon: '🔑' },
	];
	let mode = $state('direct');

	// ── Прямой поиск ─────────────────────────────────────────────────────────
	let direct_inn     = $state('');
	let direct_name    = $state('');
	let direct_website = $state('');
	let direct_save    = $state(false);

	// ── Портрет (структурированные поля) ─────────────────────────────────────
	let portrait_industry  = $state('');   // IT, строительство, финансы...
	let portrait_city      = $state('');   // Москва, регион...
let portrait_inn       = $state('');   // ИНН эталонной компании
	let portrait_emp_min   = $state('');   // от N сотрудников
	let portrait_emp_max   = $state('');   // до N
	let portrait_revenue   = $state('');   // выручка от (млн)
	let portrait_no_crm    = $state(false);
	let portrait_growing   = $state(false);
	let portrait_gov       = $state(false);  // госконтракты
	let portrait_notes     = $state('');   // доп. текст
	let portrait_limit     = $state(3);
let portrait_deep      = $state(false);

	function buildPortraitText() {
		const parts = [];
		if (portrait_industry)  parts.push(portrait_industry);
		if (portrait_city)      parts.push(`в ${portrait_city}`);
		if (portrait_emp_min && portrait_emp_max) parts.push(`${portrait_emp_min}–${portrait_emp_max} сотрудников`);
		else if (portrait_emp_min) parts.push(`от ${portrait_emp_min} сотрудников`);
		if (portrait_revenue)   parts.push(`выручка от ${portrait_revenue} млн`);
		if (portrait_no_crm)    parts.push('нет CRM');
		if (portrait_growing)   parts.push('растущая компания');
		if (portrait_gov)       parts.push('работает с госзаказом');
		if (portrait_notes)     parts.push(portrait_notes);
		return parts.join(', ');
	}

	// ── Кластер ───────────────────────────────────────────────────────────────
	let cluster_inn    = $state('');

	// ── Новости рынка ─────────────────────────────────────────────────────────
	let news_query     = $state('');
	let news_language  = $state('any');
	let news_limit     = $state(20);
	let news_agents    = $state(true);
	let news_result    = $state(null);   // { articles, agents }
	// Быстрые пресеты запросов
	const NEWS_PRESETS = [
		'ITOM мониторинг инфраструктуры',
		'SIEM кибербезопасность',
		'IAM управление доступом',
		'ManageEngine',
		'Positive Technologies',
		'импортозамещение IT',
		'утечка персональных данных',
		'152-ФЗ ФСТЭК',
	];

	// ── API Лимиты ────────────────────────────────────────────────────────────
	let limits_stats   = $state([]);
	let limits_live    = $state(null);
	let limits_loading = $state(false);
	let limits_error   = $state('');
	let limits_alerts  = $state([]);
	let limits_summary = $state({ services_total: 0, alerts_total: 0, critical_total: 0, warning_total: 0 });

	async function loadLimits() {
		limits_loading = true; limits_error = '';
		try {
			const [rs, rl] = await Promise.all([
				fetch(`${API}/api/usage/stats`),
				fetch(`${API}/api/usage/live`),
			]);
			if (rs.ok) {
				const d = await rs.json();
				limits_stats = d.services || [];
				limits_alerts = d.alerts || [];
				limits_summary = d.summary || { services_total: 0, alerts_total: 0, critical_total: 0, warning_total: 0 };
			}
			if (rl.ok) limits_live = await rl.json();
		} catch (e) {
			limits_error = e.message;
		} finally {
			limits_loading = false;
		}
	}

	async function resetLimit(svc) {
		await fetch(`${API}/api/usage/reset/${svc}`, { method: 'POST' });
		loadLimits();
	}

	function lFmt(n) {
		if (!n && n !== 0) return '—';
		if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
		if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
		return String(n);
	}
	function lPctColor(p) {
		if (p === null || p === undefined) return 'text-gray-500';
		if (p >= 90) return 'text-red-400';
		if (p >= 70) return 'text-orange-400';
		if (p >= 40) return 'text-yellow-400';
		return 'text-green-400';
	}
	function lPctBar(p) {
		if (p === null || p === undefined) return 'bg-gray-700';
		if (p >= 90) return 'bg-red-500';
		if (p >= 70) return 'bg-orange-500';
		if (p >= 40) return 'bg-yellow-500';
		return 'bg-green-500';
	}
	function lKeyBadge(s) {
		if (s === 'set')   return 'bg-green-900/40 text-green-400';
		if (s === 'dummy') return 'bg-yellow-900/40 text-yellow-400';
		return 'bg-red-900/40 text-red-400';
	}
	function lKeyLabel(s) {
		if (s === 'set')   return '● ключ задан';
		if (s === 'dummy') return '⚠ не задан';
		return '✕ отсутствует';
	}
	function lSeverity(svc) {
		const pct = svc.pct_day ?? svc.pct_month ?? null;
		if (pct !== null && pct >= 90) return 'critical';
		if (pct !== null && pct >= 70) return 'warning';
		if ((svc.errors_today || 0) > 0) return 'warning';
		return 'ok';
	}

	// ── Состояние ─────────────────────────────────────────────────────────────
	let loading   = $state(false);
	let error     = $state('');
	let result    = $state(null);          // карточка /analyze
	let portrait_results = $state(null);   // список /portrait
	let cluster_result   = $state(null);   // дерево /cluster
	let saved_crm_id     = $state(null);

	function clearAll() {
		result = null; portrait_results = null; cluster_result = null;
		news_result = null; saved_crm_id = null; error = '';
	}

	// ── Config (для Ops) ──────────────────────────────────────────────────────
	let config    = $state(null);
	let show_config = $state(false);
	let config_saving = $state(false);

	onMount(async () => {
		try {
			const r = await fetch(`${API}/api/leadgen/config`);
			if (r.ok) config = await r.json();
		} catch {}
	});

	// ── API helpers ───────────────────────────────────────────────────────────
	async function post(path, body) {
		const r = await fetch(`${API}${path}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(body),
		});
		if (!r.ok) throw new Error(await r.text());
		return r.json();
	}

	// ── Запуск ────────────────────────────────────────────────────────────────
	async function run() {
		loading = true; clearAll();
		try {
			if (mode === 'direct') {
				if (!direct_inn.trim() && !direct_name.trim()) {
					throw new Error('Введи ИНН или название компании');
				}
				result = await post('/api/leadgen/analyze', {
					inn: direct_inn.trim(),
					company_name: direct_name.trim(),
					website: direct_website.trim(),
					save_to_crm: direct_save,
				});
				// Автозаполняем сайт из результата если не был задан
				if (result?.website && !direct_website.trim()) {
					direct_website = result.website;
				}
				if (direct_save && result?.crm_lead_id) {
					saved_crm_id = result.crm_lead_id;
				}
			} else if (mode === 'portrait') {
				const pt = buildPortraitText();
				const refInn = portrait_inn.trim();
				if (!pt.trim() && !refInn) throw new Error('Введи ИНН эталонной компании или опиши портрет клиента');
				portrait_results = await post('/api/leadgen/portrait', {
					portrait: pt || `похожие на компанию с ИНН ${refInn}`,
					limit: portrait_limit,
					deep_analysis: portrait_deep,
					reference_inn: refInn,
				});
			} else if (mode === 'cluster') {
				if (!cluster_inn.trim()) throw new Error('Введи ИНН якорной компании');
				cluster_result = await post('/api/leadgen/cluster', { inn: cluster_inn.trim() });
			} else if (mode === 'news') {
				if (!news_query.trim()) throw new Error('Введи поисковый запрос (например: ITOM или ManageEngine)');
				news_result = await post('/api/news/search', {
					query: news_query.trim(),
					language: news_language,
					limit: news_limit,
					agent_limit: 30,
					run_agents: news_agents,
				});
			}
		} catch (e) {
			error = e.message || String(e);
		} finally {
			loading = false;
		}
	}

	async function saveToCRM() {
		if (!result) return;
		loading = true;
		try {
			const r = await post('/api/leadgen/save', { card: result });
			saved_crm_id = r.lead_id;
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	async function analyzePortraitItem(company) {
		loading = true; clearAll(); mode = 'direct';
		direct_inn = company.inn || '';
		direct_name = company.name || '';
		try {
			result = await post('/api/leadgen/analyze', {
				inn: company.inn || '',
				company_name: company.name || '',
			});
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	async function saveConfig() {
		config_saving = true;
		try {
			const r = await fetch(`${API}/api/leadgen/config`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(config),
			});
			if (!r.ok) throw new Error(await r.text());
			config = await r.json();
		} catch (e) {
			error = e.message;
		} finally {
			config_saving = false;
		}
	}

	// ── Форматирование ────────────────────────────────────────────────────────
	function fmtMoney(v) {
		if (!v) return '—';
		const n = parseFloat(v);
		if (isNaN(n)) return v;
		if (n >= 1e9) return (n / 1e9).toFixed(1) + ' млрд ₽';
		if (n >= 1e6) return (n / 1e6).toFixed(1) + ' млн ₽';
		return n.toLocaleString('ru') + ' ₽';
	}

	function scoreColor(s) {
		if (!s && s !== 0) return 'text-gray-400';
		if (s >= 80) return 'text-red-400';
		if (s >= 60) return 'text-orange-400';
		if (s >= 40) return 'text-yellow-400';
		return 'text-gray-400';
	}

	function priorityBadge(p) {
		const map = {
			critical: 'bg-red-900 text-red-300',
			high:     'bg-orange-900 text-orange-300',
			medium:   'bg-yellow-900 text-yellow-300',
			low:      'bg-gray-800 text-gray-400',
		};
		return map[p] || 'bg-gray-800 text-gray-400';
	}

	function actionLabel(a) {
		return { call_now: 'Звони сейчас', schedule_call: 'Запланируй звонок', research_more: 'Изучи подробнее', monitor: 'Мониторь' }[a] || a;
	}

	function trendIcon(t) {
		return { growing: '↑', stable: '→', declining: '↓', unknown: '?' }[t] || '?';
	}

	function emailValidBadge(v) {
		if (v === true) return 'text-green-400';
		if (v === false) return 'text-red-400';
		return 'text-gray-500';
	}
</script>

<div class="flex-1 overflow-y-auto bg-gray-950 p-6">

	<!-- Заголовок -->
	<div class="flex items-center justify-between mb-6">
		<div>
			<h1 class="text-xl font-semibold text-white">Лидогенерация</h1>
			<p class="text-xs text-gray-500 mt-0.5">AI-анализ компаний: ЛПР, стек, финансы, скор и стратегия захода</p>
		</div>
		<button
			onclick={() => show_config = !show_config}
			class="text-xs px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
		>⚙ Настройки</button>
	</div>

	<!-- Режимы -->
	<div class="flex gap-2 mb-5">
		{#each MODES as m}
			<button
				onclick={() => { mode = m.id; clearAll(); if (m.id === 'limits') loadLimits(); }}
				class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all
					{mode === m.id
						? 'bg-indigo-600 text-white font-medium'
						: 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'}"
			>
				<span>{m.icon}</span>{m.label}
			</button>
		{/each}
	</div>

	<!-- ── API Лимиты (отдельный режим без формы) ── -->
	{#if mode === 'limits'}
		<div class="space-y-4">
			<!-- Шапка -->
			<div class="flex items-center justify-between flex-wrap gap-2">
				<p class="text-xs text-gray-500">Использование внешних API. Счётчики: дневные сбрасываются каждый день, месячные — каждый месяц.</p>
				<button onclick={loadLimits} disabled={limits_loading}
					class="text-xs px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors disabled:opacity-50">
					{limits_loading ? '...' : '↻ Обновить'}
				</button>
			</div>

			{#if limits_error}
				<div class="bg-red-950 border border-red-800 rounded-lg px-4 py-3 text-sm text-red-300">✕ {limits_error}</div>
			{/if}

			<!-- Быстрая сводка -->
			<div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
				<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
					<div class="text-xs text-gray-500">Сервисов</div>
					<div class="text-lg font-semibold text-white">{limits_summary.services_total || limits_stats.length}</div>
				</div>
				<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
					<div class="text-xs text-gray-500">Всего предупреждений</div>
					<div class="text-lg font-semibold text-yellow-300">{limits_summary.alerts_total || 0}</div>
				</div>
				<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
					<div class="text-xs text-gray-500">Критичные</div>
					<div class="text-lg font-semibold text-red-400">{limits_summary.critical_total || 0}</div>
				</div>
				<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
					<div class="text-xs text-gray-500">Предупреждения</div>
					<div class="text-lg font-semibold text-orange-300">{limits_summary.warning_total || 0}</div>
				</div>
			</div>

			<!-- Ранние алерты -->
			{#if limits_alerts.length > 0}
				<div class="space-y-2">
					{#each limits_alerts.slice(0, 6) as a}
						<div class="rounded-lg border px-3 py-2 text-xs
							{a.level === 'critical'
								? 'bg-red-950/60 border-red-800 text-red-300'
								: 'bg-yellow-950/40 border-yellow-800 text-yellow-300'}">
							{a.level === 'critical' ? '⛔' : '⚠'} {a.message}
						</div>
					{/each}
				</div>
			{/if}

			<!-- Живые данные провайдеров -->
			{#if limits_live}
				{@const g = limits_live.groq || {}}
				{@const h = limits_live.hunter || {}}
				{@const ap = limits_live.apollo || {}}
				{@const ch = limits_live.checko || {}}
				{@const chRt = ch.runtime || {}}
				<div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
					<!-- Groq -->
					<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-semibold text-white">⚡ Groq</span>
							<span class="text-xs px-1.5 py-0.5 rounded {g.available ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}">
								{g.available ? 'online' : 'offline'}
							</span>
						</div>
						{#if g.available}
							<div class="text-xs text-gray-400">Модель: <span class="text-gray-200">{g.current_model}</span></div>
							<div class="text-xs text-gray-500 mt-0.5">Моделей доступно: {g.models_count}</div>
						{:else}
							<div class="text-xs text-red-400">{g.error || 'недоступен'}</div>
						{/if}
					</div>
					<!-- Hunter -->
					<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-semibold text-white">🎯 Hunter.io</span>
							<span class="text-xs px-1.5 py-0.5 rounded {h.available ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}">
								{h.available ? 'online' : 'offline'}
							</span>
						</div>
						{#if h.available}
							<div class="text-xs text-gray-400">Тариф: <span class="text-gray-200">{h.plan}</span></div>
							{@const sp = h.searches_used + h.searches_available > 0 ? Math.round(h.searches_used / (h.searches_used + h.searches_available) * 100) : 0}
							<div class="text-xs text-gray-500 mt-1">Поиски: {h.searches_used}/{h.searches_used + h.searches_available}</div>
							<div class="w-full bg-gray-700 rounded-full h-1 mt-1">
								<div class="h-1 rounded-full {lPctBar(sp)}" style="width:{Math.min(sp,100)}%"></div>
							</div>
							<div class="text-xs text-gray-500 mt-1">Верификации: {h.verifications_used}/{h.verifications_used + h.verifications_available}</div>
						{:else}
							<div class="text-xs text-red-400">{h.error || 'недоступен'}</div>
						{/if}
					</div>
					<!-- Apollo -->
					<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-semibold text-white">🚀 Apollo.io</span>
							<span class="text-xs px-1.5 py-0.5 rounded {ap.available ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}">
								{ap.available ? (ap.is_logged_in ? 'авторизован' : 'online') : 'offline'}
							</span>
						</div>
						<div class="text-xs text-gray-400">{ap.available ? (ap.message || 'API работает') : (ap.error || 'недоступен')}</div>
					</div>
					<!-- Checko -->
					<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-semibold text-white">🏢 Checko (ЕГРЮЛ)</span>
							<span class="text-xs px-1.5 py-0.5 rounded {ch.available ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}">
								{ch.available ? 'online' : 'offline'}
							</span>
						</div>
						<div class="text-xs text-gray-400">{ch.available ? 'API работает' : (ch.error || 'недоступен')}</div>
						{#if chRt.cache_enabled}
							<div class="text-xs text-gray-500 mt-1">
								кэш: {chRt.cache_items || 0} · TTL: {Math.round((chRt.cache_ttl_seconds || 0) / 3600)}ч
							</div>
						{/if}
						{#if chRt.breaker_open}
							<div class="text-xs text-red-400 mt-1">
								breaker активен: ещё ~{chRt.breaker_blocked_for_seconds || 0}с
							</div>
						{:else if chRt.breaker_forbidden_streak > 0}
							<div class="text-xs text-yellow-400 mt-1">
								403 подряд: {chRt.breaker_forbidden_streak}/{chRt.breaker_threshold}
							</div>
						{/if}
					</div>
				</div>
			{/if}

			<!-- Таблица счётчиков -->
			{#if limits_loading && limits_stats.length === 0}
				<div class="text-center text-gray-500 py-8 text-sm">Загружаю...</div>
			{:else if limits_stats.length === 0}
				<div class="text-center text-gray-500 py-8 text-sm">Нет данных. Начни использовать систему — счётчики появятся здесь.</div>
			{:else}
				<div class="space-y-2">
					{#each limits_stats as s}
						{@const pct = s.pct_day ?? s.pct_month ?? null}
						{@const tokDay = (s.tokens_prompt_today || 0) + (s.tokens_completion_today || 0)}
						{@const tokMonth = (s.tokens_prompt_month || 0) + (s.tokens_completion_month || 0)}
						{@const sev = lSeverity(s)}
						<div class="bg-gray-900 rounded-xl border border-gray-800 p-4 hover:border-gray-700 transition-colors">
							<div class="flex items-start gap-4 flex-wrap">

								<!-- Название -->
								<div class="min-w-[140px]">
									<div class="flex items-center gap-2 flex-wrap">
										<span class="text-sm font-medium text-white">{s.name}</span>
										<span class="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">{s.plan}</span>
										{#if sev === 'critical'}
											<span class="text-xs px-1.5 py-0.5 rounded bg-red-900/40 text-red-400">критично</span>
										{:else if sev === 'warning'}
											<span class="text-xs px-1.5 py-0.5 rounded bg-yellow-900/40 text-yellow-400">внимание</span>
										{/if}
										{#if s.key_status}
											<span class="text-xs px-1.5 py-0.5 rounded {lKeyBadge(s.key_status)}">{lKeyLabel(s.key_status)}</span>
										{/if}
									</div>
									{#if s.last_used}
										<div class="text-xs text-gray-600 mt-0.5">последний вызов: {new Date(s.last_used).toLocaleString('ru', {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}</div>
									{:else}
										<div class="text-xs text-gray-700 mt-0.5">не использовался</div>
									{/if}
								</div>

								<!-- Счётчики запросов -->
								<div class="flex gap-5 flex-wrap">
									<div class="text-center">
										<div class="text-lg font-bold text-white">{lFmt(s.calls_today)}</div>
										<div class="text-xs text-gray-500">сегодня</div>
										{#if s.limit_day_calls}
											<div class="text-xs {lPctColor(s.pct_day)} mt-0.5">/ {lFmt(s.limit_day_calls)}</div>
										{/if}
									</div>
									<div class="text-center">
										<div class="text-lg font-bold text-white">{lFmt(s.calls_month)}</div>
										<div class="text-xs text-gray-500">месяц</div>
										{#if s.limit_month_calls}
											<div class="text-xs {lPctColor(s.pct_month)} mt-0.5">/ {lFmt(s.limit_month_calls)}</div>
										{/if}
									</div>
									<div class="text-center">
										<div class="text-base font-semibold text-gray-400">{lFmt(s.calls_total)}</div>
										<div class="text-xs text-gray-600">всего</div>
									</div>
									{#if s.errors_today > 0}
										<div class="text-center">
											<div class="text-base font-semibold text-red-400">{s.errors_today}</div>
											<div class="text-xs text-gray-600">ошибок/день</div>
										</div>
									{/if}
								</div>

								<!-- Токены (для LLM-сервисов — всегда показываем) -->
								{#if s.service === 'groq' || s.service === 'ollama' || tokDay > 0 || s.tokens_total > 0}
									<div class="flex gap-5 flex-wrap border-l border-gray-700 pl-4">
										<div class="text-center">
											<div class="text-sm font-bold text-indigo-300">{lFmt(tokDay)}</div>
											<div class="text-xs text-gray-500">токенов сегодня</div>
											{#if s.limit_day_tokens}
												<div class="text-xs {lPctColor(s.pct_day)} mt-0.5">/ {lFmt(s.limit_day_tokens)}</div>
											{/if}
										</div>
										<div class="text-center">
											<div class="text-sm font-bold text-indigo-300">{lFmt(tokMonth)}</div>
											<div class="text-xs text-gray-500">токенов месяц</div>
										</div>
										<div class="text-center">
											<div class="text-xs text-gray-500">prompt</div>
											<div class="text-xs text-gray-300">{lFmt(s.tokens_prompt_today)}</div>
										</div>
										<div class="text-center">
											<div class="text-xs text-gray-500">completion</div>
											<div class="text-xs text-gray-300">{lFmt(s.tokens_completion_today)}</div>
										</div>
									</div>
								{/if}

								<!-- Сброс -->
								<button onclick={() => resetLimit(s.service)}
									class="ml-auto self-start text-xs px-2 py-1 rounded bg-gray-800 text-gray-500 hover:text-red-400 hover:bg-red-900/20 transition-colors">
									↺
								</button>
							</div>

							<!-- Прогресс-бар -->
							{#if pct !== null}
								<div class="mt-3">
									<div class="flex justify-between text-xs text-gray-600 mb-1">
										<span>{s.reset === 'daily' ? 'использовано сегодня' : 'использовано в месяце'}</span>
										<span class="{lPctColor(pct)}">{pct}%</span>
									</div>
									<div class="w-full bg-gray-800 rounded-full h-1.5">
										<div class="h-1.5 rounded-full transition-all {lPctBar(pct)}" style="width:{Math.min(pct,100)}%"></div>
									</div>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{:else}

	<!-- ── Форма ── -->
	<div class="bg-gray-900 rounded-xl border border-gray-800 p-5 mb-5">

		{#if mode === 'direct'}
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
				<div>
					<div class="text-xs text-gray-500 mb-1 block">ИНН</div>
					<input bind:value={direct_inn} placeholder="7736207543"
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Название компании</div>
					<input bind:value={direct_name} placeholder="ООО Ромашка"
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Сайт (опционально)</div>
					<input bind:value={direct_website} placeholder="romashka.ru"
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>
			</div>
			<label class="flex items-center gap-2 text-sm text-gray-400 mb-4 cursor-pointer">
				<input type="checkbox" bind:checked={direct_save} class="accent-indigo-500" />
				Сохранить в CRM автоматически (если скор ≥ 30)
			</label>

		{:else if mode === 'portrait'}
			<!-- Главный режим: эталонная компания -->
			<div class="mb-4 p-3 rounded-xl bg-indigo-950/40 border border-indigo-800/40">
				<div class="text-xs text-indigo-400 mb-1 block font-semibold">⭐ ИНН эталонной компании — найдём похожих</div>
				<div class="flex gap-2">
					<input bind:value={portrait_inn} placeholder="7707083893 — введи ИНН клиента, похожих на которого хочешь найти"
						class="flex-1 bg-gray-800 border border-indigo-700/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>
				<div class="text-xs text-gray-500 mt-1">Система проанализирует компанию по ИНН и найдёт максимально похожих по отрасли, размеру и городу</div>
			</div>
			<div class="text-xs text-gray-600 mb-2">— или опиши портрет вручную —</div>
			<div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-3">
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Отрасль</div>
					<input bind:value={portrait_industry} placeholder="IT, строительство, ритейл..."
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Город / Регион</div>
					<input bind:value={portrait_city} placeholder="Москва, Урал, вся Россия..."
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Кол-во результатов</div>
					<input type="number" bind:value={portrait_limit} min="1" max="20"
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500" />
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Сотрудников от</div>
					<input bind:value={portrait_emp_min} placeholder="50"
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Сотрудников до</div>
					<input bind:value={portrait_emp_max} placeholder="500"
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Выручка от (млн ₽)</div>
					<input bind:value={portrait_revenue} placeholder="100"
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>
			</div>
			<div class="flex flex-wrap gap-4 mb-3">
				<label class="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
					<input type="checkbox" bind:checked={portrait_no_crm} class="accent-indigo-500" />
					Нет CRM
				</label>
				<label class="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
					<input type="checkbox" bind:checked={portrait_growing} class="accent-indigo-500" />
					Растущая (инвестиции/найм)
				</label>
				<label class="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
					<input type="checkbox" bind:checked={portrait_gov} class="accent-indigo-500" />
					Госконтракты
				</label>
				<label class="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
					<input type="checkbox" bind:checked={portrait_deep} class="accent-indigo-500" />
					Глубокий анализ (Apollo/Hunter)
				</label>
			</div>
			<div>
				<div class="text-xs text-gray-500 mb-1 block">Дополнительно (свободный текст)</div>
				<textarea bind:value={portrait_notes} rows="2"
					placeholder="Что ещё важно: например, есть команда DevOps, или ищут замену Jira..."
					class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 resize-none"
				></textarea>
			</div>
			{#if buildPortraitText()}
				<div class="mt-2 text-xs text-indigo-400 bg-indigo-950/30 rounded px-3 py-1.5">
					Запрос: «{buildPortraitText()}»
				</div>
			{/if}

		{:else if mode === 'cluster'}
			<div class="text-xs text-gray-500 mb-1 block">ИНН якорной компании</div>
			<input bind:value={cluster_inn} placeholder="7736207543 — найдём весь холдинг и учредителей"
				class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />

		{:else if mode === 'news'}
			<!-- Пресеты -->
			<div class="flex flex-wrap gap-1.5 mb-3">
				{#each NEWS_PRESETS as preset}
					<button
						onclick={() => news_query = preset}
						class="text-xs px-2.5 py-1 rounded-full bg-gray-800 text-gray-400 hover:text-indigo-300 hover:bg-indigo-900/40 border border-gray-700 hover:border-indigo-600 transition-colors"
					>{preset}</button>
				{/each}
			</div>
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
				<div class="sm:col-span-2">
					<div class="text-xs text-gray-500 mb-1 block">Поисковый запрос</div>
					<input bind:value={news_query}
						placeholder="ITOM, ManageEngine, кибербезопасность, 152-ФЗ..."
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Язык</div>
					<select bind:value={news_language}
						class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
					>
						<option value="any">Любой (шире)</option>
						<option value="ru">Русский</option>
						<option value="en">English</option>
					</select>
				</div>
			</div>
			<div class="flex flex-wrap items-center gap-4">
				<label class="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
					<input type="checkbox" bind:checked={news_agents} class="accent-indigo-500" />
					Запустить AI-агентов (5 экспертов анализируют тренды)
				</label>
				<label class="flex items-center gap-2 text-sm text-gray-500">
					<span class="text-xs">Статей:</span>
					<input type="number" bind:value={news_limit} min="5" max="50"
						class="w-16 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white focus:outline-none focus:border-indigo-500" />
				</label>
			</div>
		{/if}

		<button
			onclick={run}
			disabled={loading}
			class="mt-4 px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
		>
			{#if loading}
				<span class="animate-spin inline-block">⟳</span> {mode === 'news' ? 'Ищу новости...' : 'Анализирую...'}
			{:else}
				{mode === 'direct' ? '🔍 Анализировать' : mode === 'portrait' ? '🎯 Найти компании' : mode === 'cluster' ? '🕸 Найти связанные' : '📰 Найти новости'}
			{/if}
		</button>
	</div>

	<!-- Ошибка -->
	{#if error}
		<div class="bg-red-950 border border-red-800 rounded-lg px-4 py-3 text-sm text-red-300 mb-4">✕ {error}</div>
	{/if}

	<!-- ── РЕЗУЛЬТАТ: карточка лида ── -->
	{#if result}
		{@const lpr = result.lpr || {}}
		{@const fin = result.financials || {}}
		{@const tech = result.tech_stack || {}}
		{@const an = result.analyses || {}}
		{@const agents = result.agent_scores || {}}
		{@const agout = result.agent_outputs || {}}
		{@const risks = result.risk_flags || {}}

		<div class="space-y-4">

			<!-- ══ ШАПКА КОМПАНИИ ══ -->
			<div class="bg-gray-900 rounded-xl border border-gray-800 p-5">
				<div class="flex items-start justify-between gap-4 flex-wrap">
					<div class="flex-1 min-w-0">
						<h2 class="text-lg font-semibold text-white">{result.company_name || '—'}</h2>
						{#if result.company_short && result.company_short !== result.company_name}
							<div class="text-xs text-gray-600">{result.company_short}</div>
						{/if}

						<!-- ЕГРЮЛ строка -->
						<div class="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-gray-500 mt-1">
							<span>ИНН: <span class="text-gray-300">{result.inn || '—'}</span></span>
							{#if result.kpp}<span>КПП: <span class="text-gray-400">{result.kpp}</span></span>{/if}
							<span>ОГРН: <span class="text-gray-300">{result.ogrn || '—'}</span></span>
							{#if result.registration_date}<span>Рег: <span class="text-gray-400">{result.registration_date}</span></span>{/if}
							<span class="px-1.5 py-0.5 rounded {result.company_status === 'ACTIVE' ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}">
								{result.company_status === 'ACTIVE' ? '● Действует' : result.company_status || '—'}
							</span>
						</div>

						<!-- ОКВЭД + МСП -->
						<div class="text-xs text-gray-500 mt-1">
							{#if result.okved}<span class="text-gray-400">{result.okved}</span> {/if}
							<span class="text-gray-600">{result.okved_name || result.industry || ''}</span>
							{#if result.smb_category}<span class="ml-2 px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400">{result.smb_category}</span>{/if}
						</div>

						<!-- Адрес + сайт -->
						<div class="mt-1 text-xs text-gray-600">
							{#if result.address}<div>{result.address}</div>{:else if result.city}<div>{result.city}</div>{/if}
							{#if result.website}
								<a href="https://{result.website}" target="_blank" class="text-indigo-400 hover:underline">{result.website}</a>
							{/if}
						</div>

						<!-- Риск-флаги -->
						{#if risks.is_bad_supplier || risks.has_disqualified_leader || risks.is_mass_address}
							<div class="flex flex-wrap gap-1.5 mt-2">
								{#if risks.is_bad_supplier}
									<span class="text-xs px-2 py-0.5 rounded-full bg-red-900 text-red-300">⛔ Недобросовестный поставщик</span>
								{/if}
								{#if risks.has_disqualified_leader}
									<span class="text-xs px-2 py-0.5 rounded-full bg-orange-900 text-orange-300">⚠ Дисквалифицированный руководитель</span>
								{/if}
								{#if risks.is_mass_address}
									<span class="text-xs px-2 py-0.5 rounded-full bg-yellow-900 text-yellow-300">📍 Массовый адрес</span>
								{/if}
							</div>
						{/if}
					</div>

					<div class="flex flex-col items-end gap-2 shrink-0">
						<div class="flex items-center gap-3">
							<span class="text-4xl font-bold {scoreColor(result.final_score)}">{result.final_score ?? '—'}</span>
							<div class="text-right">
								<div class="text-xs text-gray-500">Итоговый скор</div>
								<span class="text-xs px-2 py-0.5 rounded-full {priorityBadge(result.priority)}">{result.priority || '—'}</span>
							</div>
						</div>
						<div class="text-sm font-medium text-indigo-300">{actionLabel(result.action)}</div>
					</div>
				</div>

				<!-- Триггеры -->
				{#if result.triggers?.length}
					<div class="mt-3 flex flex-wrap gap-2">
						{#each result.triggers as t}
							<span class="text-xs px-2 py-0.5 rounded-full bg-indigo-900/60 text-indigo-300 border border-indigo-800/40">⚡ {t}</span>
						{/each}
					</div>
				{/if}

				<!-- Сохранить в CRM -->
				{#if !direct_save}
					<div class="mt-4 flex items-center gap-3">
						{#if saved_crm_id}
							<span class="text-sm text-green-400">✓ Сохранён в CRM (ID: {saved_crm_id})</span>
							<a href="/leads/{saved_crm_id}" class="text-xs text-indigo-400 hover:underline">Открыть лид →</a>
						{:else}
							<button onclick={saveToCRM} disabled={loading}
								class="px-4 py-1.5 rounded-lg bg-green-700 hover:bg-green-600 text-white text-sm transition-colors disabled:opacity-50">
								+ Добавить в CRM
							</button>
						{/if}
					</div>
				{:else if saved_crm_id}
					<div class="mt-3 flex items-center gap-2 text-sm text-green-400">
						✓ Автосохранён в CRM <a href="/leads/{saved_crm_id}" class="text-indigo-400 hover:underline ml-1">Открыть лид →</a>
					</div>
				{/if}
			</div>

			<!-- ══ 2 КОЛОНКИ: ЛПР + ФИНАНСЫ ══ -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">

				<!-- ЛПР -->
				<div class="bg-gray-900 rounded-xl border border-indigo-900/50 p-4">
					<h3 class="text-sm font-medium text-indigo-300 mb-3">👤 ЛПР и контакты</h3>
					<div class="space-y-2 text-sm">
						<div class="flex justify-between">
							<span class="text-gray-500">Руководитель</span>
							<span class="text-white font-medium">{lpr.name || '—'}</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-500">Должность</span>
							<span class="text-gray-300">{lpr.role || '—'}</span>
						</div>

						<!-- Сайт -->
						{#if result.website}
							<div class="flex justify-between items-center">
								<span class="text-gray-500">🌐 Сайт</span>
								<a href="https://{result.website}" target="_blank" rel="noopener"
									class="text-indigo-400 hover:underline text-xs font-mono">{result.website}</a>
							</div>
						{/if}

						<!-- Все телефоны -->
						{#if lpr.dadata_phones?.length}
							{#each lpr.dadata_phones as ph}
								<div class="flex justify-between">
									<span class="text-gray-500">📞 Тел</span>
									<a href="tel:{ph}" class="text-green-400 font-mono text-xs hover:underline">{ph}</a>
								</div>
							{/each}
						{:else if lpr.phone}
							<div class="flex justify-between">
								<span class="text-gray-500">📞 Тел</span>
								<a href="tel:{lpr.phone}" class="text-green-400 font-mono text-xs hover:underline">{lpr.phone}</a>
							</div>
						{/if}

						<!-- Все email -->
						{#if lpr.email}
							<div class="flex justify-between items-center">
								<span class="text-gray-500">✉ Email</span>
								<div class="flex items-center gap-1">
									<a href="mailto:{lpr.email}" class="text-blue-400 font-mono text-xs hover:underline">{lpr.email}</a>
									<span class="text-xs {emailValidBadge(lpr.email_valid)}">
										{lpr.email_valid === true ? '✓' : lpr.email_valid === false ? '✗' : '?'}
									</span>
									{#if lpr.email_source}
										<span class="text-xs text-gray-600">({lpr.email_source})</span>
									{/if}
								</div>
							</div>
						{/if}
						<!-- Все остальные email из Checko/веба -->
						{#if lpr.dadata_emails?.length}
							{#each lpr.dadata_emails as em}
								{#if em !== lpr.email}
									<div class="flex justify-between">
										<span class="text-gray-500">✉ Email</span>
										<a href="mailto:{em}" class="text-blue-300 font-mono text-xs hover:underline">{em}</a>
									</div>
								{/if}
							{/each}
						{/if}

						<!-- LinkedIn / Twitter ЛПР -->
						{#if lpr.linkedin}
							<div class="flex justify-between">
								<span class="text-gray-500">LinkedIn</span>
								<a href="{lpr.linkedin}" target="_blank" rel="noopener" class="text-blue-400 text-xs hover:underline truncate max-w-[60%]">
									{lpr.linkedin.replace('https://www.linkedin.com/in/', '@').replace('https://linkedin.com/in/', '@')}
								</a>
							</div>
						{/if}

						<!-- Варианты email (паттерн) -->
						{#if lpr.email_variants?.length}
							<div class="pt-1 border-t border-gray-800/60">
								<div class="text-xs text-gray-600 mb-1">Вероятные email:</div>
								{#each lpr.email_variants.slice(0,3) as ev}
									<div class="flex justify-between">
										<span class="text-gray-600 text-xs">✉</span>
										<a href="mailto:{ev}" class="text-gray-500 font-mono text-xs hover:text-gray-300">{ev}</a>
									</div>
								{/each}
							</div>
						{/if}

						<!-- Hunter.io: паттерн + кол-во найденных -->
						{#if lpr.hunter_pattern || lpr.hunter_total_emails > 0}
							<div class="pt-1 border-t border-gray-800/60 text-xs text-gray-600">
								{#if lpr.hunter_pattern}
									<span>Формат email: <span class="text-gray-400 font-mono">{lpr.hunter_pattern}@{result.website || '...'}</span></span>
								{/if}
								{#if lpr.hunter_total_emails > 0}
									<span class="ml-2">Hunter нашёл: <span class="text-indigo-400">{lpr.hunter_total_emails}</span> адресов</span>
								{/if}
							</div>
						{/if}

						<!-- Нет контактов -->
						{#if !lpr.phone && !lpr.dadata_phones?.length && !lpr.email && !lpr.dadata_emails?.length}
							<div class="text-xs text-yellow-800 bg-yellow-950/20 rounded px-2 py-1.5 mt-1">
								⚠ Контакты в открытых реестрах не найдены.
								{#if result.website}
									Попробуй на сайте <a href="https://{result.website}" target="_blank" class="text-indigo-400 hover:underline">{result.website}</a>
								{:else}
									Введи сайт компании для поиска контактов.
								{/if}
							</div>
						{/if}
					</div>

					<!-- Apollo: топ-менеджеры -->
					{#if lpr.apollo_executives?.length > 0}
						<div class="mt-4 pt-3 border-t border-gray-800">
							<div class="text-xs text-gray-500 mb-2">🚀 Топ-менеджеры (Apollo.io)</div>
							{#each lpr.apollo_executives as exec}
								<div class="flex items-start gap-2 py-1.5 border-b border-gray-800/40">
									<div class="flex-1 min-w-0">
										<div class="flex items-center gap-1.5 flex-wrap">
											<span class="text-xs text-white font-medium">{exec.name || (exec.first_name + ' ' + exec.last_name)}</span>
											{#if exec.seniority === 'c_suite' || exec.seniority === 'vp'}
												<span class="text-xs px-1 py-0.5 rounded bg-purple-900/40 text-purple-300">{exec.seniority}</span>
											{/if}
											{#if exec.email_status === 'verified'}
												<span class="text-xs text-green-500">✓</span>
											{/if}
										</div>
										<div class="text-xs text-gray-500">{exec.title || '—'}</div>
										{#if exec.email}
											<a href="mailto:{exec.email}" class="text-xs text-blue-400 font-mono hover:underline">{exec.email}</a>
										{/if}
										{#if exec.phone || exec.mobile_phone}
											<div class="text-xs text-green-400 font-mono">📞 {exec.phone || exec.mobile_phone}</div>
										{/if}
									</div>
									{#if exec.linkedin}
										<a href="{exec.linkedin}" target="_blank" rel="noopener"
											class="text-xs text-blue-500 hover:text-blue-400 shrink-0">in</a>
									{/if}
								</div>
							{/each}
						</div>
					{/if}

					<!-- Hunter: все сотрудники найденные на домене -->
					{#if lpr.hunter_employees?.length > 0}
						<div class="mt-4 pt-3 border-t border-gray-800">
							<div class="text-xs text-gray-500 mb-2">
								👥 Сотрудники (Hunter.io, {lpr.hunter_employees.length} из {lpr.hunter_total_emails || lpr.hunter_employees.length})
							</div>
							{#each lpr.hunter_employees as emp}
								{#if emp.email}
									<div class="flex items-start gap-2 py-1 border-b border-gray-800/40">
										<div class="flex-1 min-w-0">
											<div class="flex items-center gap-2">
												{#if emp.first_name || emp.last_name}
													<span class="text-xs text-white">{emp.first_name} {emp.last_name}</span>
												{/if}
												{#if emp.seniority === 'executive'}
													<span class="text-xs px-1 py-0.5 rounded bg-purple-900/40 text-purple-300">exec</span>
												{/if}
											</div>
											{#if emp.position}
												<div class="text-xs text-gray-500">{emp.position}</div>
											{/if}
											<a href="mailto:{emp.email}" class="text-xs text-blue-400 font-mono hover:underline">{emp.email}</a>
										</div>
										<div class="flex gap-1 shrink-0">
											{#if emp.linkedin}
												<a href="{emp.linkedin}" target="_blank" rel="noopener" class="text-xs text-blue-500 hover:text-blue-400">in</a>
											{/if}
											{#if emp.confidence}
												<span class="text-xs text-gray-600">{emp.confidence}%</span>
											{/if}
										</div>
									</div>
								{/if}
							{/each}
						</div>
					{/if}

					<!-- Учредители -->
					{#if result.founders?.length}
						<div class="mt-4 pt-3 border-t border-gray-800">
							<div class="text-xs text-gray-500 mb-2">Учредители ({result.founders.length})</div>
							{#each result.founders.slice(0,8) as f}
								<div class="flex justify-between text-xs py-0.5">
									<span class="text-gray-300">{f.name || '—'}</span>
									<span class="text-gray-500">
										{f.type === 'LEGAL' ? '🏢' : '👤'}
										{f.share_percent ? f.share_percent + '%' : ''}
									</span>
								</div>
							{/each}
						</div>
					{/if}

					<!-- Управление -->
					{#if an.decision_structure}
						<div class="mt-3 pt-3 border-t border-gray-800 text-xs">
							<div class="flex gap-2 text-gray-600 flex-wrap">
								<span>Тип: <span class="text-gray-400">{result.management_type || '—'}</span></span>
								<span>Филиалов: <span class="text-gray-400">{result.branch_count || 0}</span></span>
								{#if result.employees_count}<span>Сотр.: <span class="text-gray-400">{result.employees_count}</span></span>{/if}
							</div>
							{#if an.decision_structure.secondary_lpr}
								<div class="mt-1 text-yellow-600">Также: {an.decision_structure.secondary_lpr}</div>
							{/if}
							<div class="mt-1 text-indigo-500">{an.decision_structure.approach_recommendation || ''}</div>
						</div>
					{/if}
				</div>

				<!-- Финансы -->
				<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
					<h3 class="text-sm font-medium text-gray-300 mb-3">💰 Финансы
						{#if fin.finance_year}<span class="text-xs text-gray-600 ml-1">({fin.finance_year} г.)</span>{/if}
					</h3>
					<div class="space-y-2 text-sm">
						<div class="flex justify-between">
							<span class="text-gray-500">Выручка</span>
							<span class="text-white font-medium">{fmtMoney(fin.revenue)}</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-500">Прибыль</span>
							<span class="{(fin.profit ?? fin.income) >= 0 ? 'text-green-400' : 'text-red-400'}">{fmtMoney(fin.profit ?? fin.income)}</span>
						</div>
						{#if fin.assets}
							<div class="flex justify-between">
								<span class="text-gray-500">Активы</span>
								<span class="text-gray-300">{fmtMoney(fin.assets)}</span>
							</div>
						{/if}
						{#if fin.expense}
							<div class="flex justify-between">
								<span class="text-gray-500">Расходы</span>
								<span class="text-gray-300">{fmtMoney(fin.expense)}</span>
							</div>
						{/if}
						{#if fin.debt}
							<div class="flex justify-between">
								<span class="text-gray-500">Кред. задолж.</span>
								<span class="text-red-400">{fmtMoney(fin.debt)}</span>
							</div>
						{/if}

						<!-- Динамика выручки -->
						{#if fin.revenue_series?.length > 1}
							<div class="mt-2 pt-2 border-t border-gray-800">
								<div class="text-xs text-gray-600 mb-1">Динамика выручки:</div>
								<div class="flex gap-2 flex-wrap">
									{#each fin.revenue_series as [yr, rev]}
										<span class="text-xs text-gray-400">{yr}: <span class="text-white">{fmtMoney(rev)}</span></span>
									{/each}
								</div>
							</div>
						{/if}

						<div class="pt-1 border-t border-gray-800">
							<div class="flex justify-between text-xs mt-1">
								<span class="text-gray-500">Тренд</span>
								<span class="{fin.trend === 'growing' ? 'text-green-400' : fin.trend === 'declining' ? 'text-red-400' : 'text-gray-400'}">
									{trendIcon(fin.trend)} {fin.trend || '—'}
								</span>
							</div>
						</div>

						<!-- Сводка рисков -->
						<div class="pt-1 border-t border-gray-800 space-y-1 text-xs">
							<div class="flex justify-between">
								<span class="text-gray-500">Арбитраж (КАД)</span>
								<span class="{fin.arbitration_count > 0 ? 'text-yellow-400' : 'text-gray-600'}">{fin.arbitration_count ?? 0} дел</span>
							</div>
							<div class="flex justify-between">
								<span class="text-gray-500">ФССП</span>
								<span class="{fin.enforcement_count > 0 ? 'text-red-400' : 'text-gray-600'}">{fin.enforcement_count ?? 0} произв. {fin.enforcement_count > 0 ? '· ' + fmtMoney(fin.enforcement_debt) : ''}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-gray-500">Госзакупки</span>
								<span class="{fin.contracts_count > 0 ? 'text-green-400' : 'text-gray-600'}">{fin.contracts_count ?? 0} конт. {fin.contracts_count > 0 ? '· ' + fmtMoney(fin.contracts_total_amount) : ''}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-gray-500">Проверки ГП</span>
								<span class="{fin.inspection_count > 0 ? 'text-yellow-600' : 'text-gray-600'}">{fin.inspection_count ?? 0}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-gray-500">Федресурс</span>
								<span class="{fin.fedresurs_count > 0 ? 'text-orange-400' : 'text-gray-600'}">{fin.fedresurs_count ?? 0} сообщ.</span>
							</div>
							<div class="flex justify-between">
								<span class="text-gray-500">Банкротство</span>
								<span class="{fin.has_bankruptcy ? 'text-red-500 font-medium' : 'text-green-600'}">{fin.has_bankruptcy ? '⛔ Да' : '✓ Нет'}</span>
							</div>
						</div>
					</div>

					{#if an.growth_trajectory?.sales_argument}
						<div class="mt-3 pt-3 border-t border-gray-800 text-xs">
							<div class="text-gray-500 mb-0.5">Аргумент:</div>
							<div class="text-gray-300">{an.growth_trajectory.sales_argument}</div>
						</div>
					{/if}
				</div>

				<!-- Технологии -->
				<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
					<h3 class="text-sm font-medium text-gray-300 mb-3">💻 Технологии
						{#if result.website}
							<span class="text-xs text-gray-600 ml-1">· {result.website}</span>
						{/if}
					</h3>
					<div class="space-y-2 text-sm mb-3">
						<div class="flex justify-between">
							<span class="text-gray-500">Технологий найдено</span>
							<span class="text-white">{tech.count ?? 0}</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-500">IT-зрелость</span>
							<span class="text-indigo-300 capitalize">{an.it_maturity?.level || tech.maturity || '—'}</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-500">CRM</span>
							<span class="text-gray-300">{tech.crm?.join(', ') || 'не обнаружена'}</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-500">Аналитика</span>
							<span class="text-gray-300">{tech.analytics?.join(', ') || 'не обнаружена'}</span>
						</div>
						{#if !result.website}
							<div class="text-xs text-yellow-700 pt-1">⚠ Сайт не найден — введи домен вручную для анализа стека</div>
						{/if}
					</div>

					{#if tech.all?.length}
						<div class="flex flex-wrap gap-1 mt-1">
							{#each tech.all as t}
								<span class="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">{t}</span>
							{/each}
						</div>
					{/if}

					{#if an.vendor_landscape}
						<div class="mt-3 pt-3 border-t border-gray-800 text-xs">
							<span class="text-gray-500">Позиционирование: </span>
							<span class="text-indigo-300">{an.vendor_landscape.positioning || '—'}</span>
							{#if an.vendor_landscape.gaps?.length}
								<div class="mt-1 text-yellow-600">Пробелы: {an.vendor_landscape.gaps.join(', ')}</div>
							{/if}
						</div>
					{/if}

					{#if result.recommended_products?.length}
						<div class="mt-3 pt-3 border-t border-gray-800">
							<div class="text-xs text-gray-500 mb-1">Рекомендовано:</div>
							<div class="flex flex-wrap gap-1">
								{#each result.recommended_products as p}
									<span class="text-xs px-2 py-0.5 rounded-full bg-indigo-900/50 text-indigo-300 border border-indigo-800/30">{p}</span>
								{/each}
							</div>
						</div>
					{/if}
				</div>

				<!-- Безопасность + Лицензии -->
				<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
					<h3 class="text-sm font-medium text-gray-300 mb-3">🔒 Безопасность и комплаенс</h3>
					{#if an.security_compliance}
						<div class="space-y-2 text-sm">
							<div class="flex justify-between">
								<span class="text-gray-500">Уровень</span>
								<span class="text-gray-300 capitalize">{an.security_compliance.compliance_level || '—'}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-gray-500">Регулируемая отрасль</span>
								<span class="{an.security_compliance.is_regulated_industry ? 'text-yellow-400' : 'text-gray-500'}">
									{an.security_compliance.is_regulated_industry ? 'Да ⚠' : 'Нет'}
								</span>
							</div>
						</div>
						<div class="mt-2 text-xs text-indigo-400">{an.security_compliance.product_recommendation || ''}</div>
					{/if}

					<!-- Лицензии -->
					{#if fin.licenses?.length}
						<div class="mt-3 pt-3 border-t border-gray-800">
							<div class="text-xs text-gray-500 mb-1">Лицензии ({fin.licenses.length}):</div>
							{#each fin.licenses.slice(0,4) as lic}
								<div class="text-xs text-gray-400 py-0.5">· {lic}</div>
							{/each}
						</div>
					{/if}
				</div>

			</div>

			<!-- ══ СВЯЗИ И СТРУКТУРА ══ -->
			{#if result.connections?.has_connections || result.founders?.length || result.related_companies?.length}
				{@const conn = result.connections || {}}
				{@const legal_founders = conn.legal_founders || []}
				{@const individual_founders = conn.individual_founders || []}
				{@const subsidiaries = conn.subsidiaries || result.related_companies || []}
				<div class="bg-gray-900 rounded-xl border border-purple-900/30 p-4">
					<div class="flex items-center justify-between mb-3">
						<h3 class="text-sm font-medium text-purple-300">
							🕸 Связи и структура собственности
						</h3>
						<button
							onclick={() => {
								cluster_inn = result.inn || '';
								mode = 'cluster';
								if (cluster_inn) run();
							}}
							class="text-xs px-2 py-1 rounded bg-purple-900/40 hover:bg-purple-800 text-purple-300 transition-colors">
							Полный кластер →
						</button>
					</div>

					<!-- Учредители-юрлица (материнские) -->
					{#if legal_founders.length}
						<div class="mb-3">
							<div class="text-xs text-gray-500 mb-1.5">🏢 Материнские компании / учредители-юрлица</div>
							<div class="space-y-1">
								{#each legal_founders as f}
									<div class="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2 text-xs">
										<div>
											<span class="text-gray-200">{f.name}</span>
											{#if f.inn}<span class="text-gray-600 ml-2">ИНН: {f.inn}</span>{/if}
										</div>
										<div class="flex items-center gap-2">
											{#if f.share_percent}<span class="text-purple-400 font-medium">{f.share_percent}%</span>{/if}
											{#if f.inn}
												<button onclick={() => { direct_inn = f.inn; mode = 'direct'; result = null; run(); }}
													class="text-xs px-2 py-0.5 rounded bg-gray-700 hover:bg-indigo-700 text-gray-300 transition-colors">
													→
												</button>
											{/if}
										</div>
									</div>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Учредители-физлица -->
					{#if individual_founders.length}
						<div class="mb-3">
							<div class="text-xs text-gray-500 mb-1.5">👤 Учредители — физические лица</div>
							<div class="flex flex-wrap gap-2">
								{#each individual_founders as f}
									<span class="text-xs bg-gray-800 rounded-full px-3 py-1 text-gray-300">
										{f.name}{f.share_percent ? ` · ${f.share_percent}%` : ''}
									</span>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Дочерние / аффилированные -->
					{#if subsidiaries.length}
						<div>
							<div class="text-xs text-gray-500 mb-1.5">
								🏗 Дочерние и аффилированные компании ({subsidiaries.length})
							</div>
							<div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
								{#each subsidiaries as rc}
									<div class="bg-gray-800 rounded-lg p-2 text-xs flex items-start justify-between gap-2">
										<div class="min-w-0">
											<div class="text-gray-200 font-medium truncate">{rc.name || rc.name_full || '—'}</div>
											<div class="text-gray-600 mt-0.5 flex gap-2 flex-wrap">
												{#if rc.inn}<span>ИНН: {rc.inn}</span>{/if}
												{#if rc.status}<span class="{rc.status === 'ACTIVE' ? 'text-green-600' : 'text-red-600'}">{rc.status === 'ACTIVE' ? '● Действует' : '○ ' + rc.status}</span>{/if}
											</div>
											{#if rc.okved}<div class="text-gray-600 truncate">{rc.okved}</div>{/if}
										</div>
										{#if rc.inn}
											<button onclick={() => { direct_inn = rc.inn; mode = 'direct'; result = null; run(); }}
												class="shrink-0 text-xs px-2 py-0.5 rounded bg-gray-700 hover:bg-indigo-700 text-gray-300 transition-colors">
												→
											</button>
										{/if}
									</div>
								{/each}
							</div>
						</div>
					{/if}
				</div>
			{/if}

			<!-- ══ ЮРИДИЧЕСКИЙ ПРОФИЛЬ (Checko) ══ -->
			{#if fin.arbitration_cases?.length || fin.enforcements?.length || fin.contracts?.length || fin.inspections?.length || fin.fedresurs_messages?.length || fin.bankruptcy_messages?.length}
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">

					<!-- Арбитраж КАД -->
					{#if fin.arbitration_count > 0}
						<div class="bg-gray-900 rounded-xl border border-yellow-900/30 p-4">
							<h3 class="text-sm font-medium text-yellow-400 mb-3">⚖️ Арбитраж КАД · {fin.arbitration_count} дел</h3>
							{#if fin.arbitration_cases?.length}
								<div class="space-y-2">
									{#each fin.arbitration_cases.slice(0,5) as c}
										<div class="text-xs border-b border-gray-800 pb-1">
											<span class="text-gray-400">{c.number}</span>
											<span class="text-gray-600 ml-2">{c.date}</span>
											{#if c.amount}<span class="text-yellow-400 ml-2">{fmtMoney(c.amount)}</span>{/if}
											{#if c.role}<span class="text-gray-500 ml-1">· {c.role}</span>{/if}
											{#if c.result}<div class="text-gray-600 mt-0.5">{c.result}</div>{/if}
										</div>
									{/each}
								</div>
							{:else}
								<div class="text-xs text-gray-600">Нет детальных данных</div>
							{/if}
						</div>
					{/if}

					<!-- ФССП -->
					{#if fin.enforcement_count > 0}
						<div class="bg-gray-900 rounded-xl border border-red-900/30 p-4">
							<h3 class="text-sm font-medium text-red-400 mb-3">🚨 ФССП · {fin.enforcement_count} произв. · {fmtMoney(fin.enforcement_debt)}</h3>
							{#if fin.enforcements?.length}
								<div class="space-y-2">
									{#each fin.enforcements as e}
										<div class="text-xs border-b border-gray-800 pb-1">
											<div class="text-gray-400 line-clamp-1">{e.reason || e.number}</div>
											<div class="flex gap-3 flex-wrap">
												{#if e.amount}<span class="text-red-400">{fmtMoney(e.amount)}</span>{/if}
												<span class="text-gray-600">{e.date}</span>
												{#if e.status}<span class="text-gray-500">{e.status}</span>{/if}
											</div>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/if}

					<!-- Госзакупки 44-ФЗ -->
					{#if fin.contracts_count > 0}
						<div class="bg-gray-900 rounded-xl border border-green-900/30 p-4">
							<h3 class="text-sm font-medium text-green-400 mb-3">🏛️ Госзакупки · {fin.contracts_count} конт. · {fmtMoney(fin.contracts_total_amount)}</h3>
							{#if fin.contracts?.length}
								<div class="space-y-2">
									{#each fin.contracts as c}
										<div class="text-xs border-b border-gray-800 pb-1">
											<div class="text-gray-300 line-clamp-1">{c.subject || c.number}</div>
											<div class="flex gap-3 flex-wrap">
												<span class="text-green-400">{fmtMoney(c.amount)}</span>
												<span class="text-gray-600">{c.date}</span>
												{#if c.customer}<span class="text-gray-500 line-clamp-1">{c.customer}</span>{/if}
											</div>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/if}

					<!-- Проверки ГП -->
					{#if fin.inspection_count > 0}
						<div class="bg-gray-900 rounded-xl border border-gray-700 p-4">
							<h3 class="text-sm font-medium text-gray-400 mb-3">🔍 Проверки ГП · {fin.inspection_count}</h3>
							{#if fin.inspections?.length}
								<div class="space-y-2">
									{#each fin.inspections as i}
										<div class="text-xs border-b border-gray-800 pb-1">
											<div class="text-gray-400 line-clamp-1">{i.authority}</div>
											<div class="flex gap-2 flex-wrap">
												<span class="text-gray-600">{i.date}</span>
												{#if i.violations}<span class="text-red-400 font-medium">! Нарушения</span>{/if}
												{#if i.result}<span class="text-gray-500">{i.result}</span>{/if}
											</div>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/if}

					<!-- Федресурс -->
					{#if fin.fedresurs_count > 0}
						<div class="bg-gray-900 rounded-xl border border-orange-900/30 p-4">
							<h3 class="text-sm font-medium text-orange-400 mb-3">📋 Федресурс · {fin.fedresurs_count} сообщ.</h3>
							{#if fin.fedresurs_messages?.length}
								<div class="space-y-2">
									{#each fin.fedresurs_messages as m}
										<div class="text-xs border-b border-gray-800 pb-1">
											<div class="flex gap-2">
												<span class="text-orange-400">{m.type}</span>
												<span class="text-gray-600">{m.date}</span>
											</div>
											{#if m.text}<div class="text-gray-500 mt-0.5 line-clamp-2">{m.text}</div>{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/if}

					<!-- Банкротство ЕФРСБ -->
					{#if fin.has_bankruptcy}
						<div class="bg-gray-900 rounded-xl border border-red-800/50 p-4">
							<h3 class="text-sm font-medium text-red-400 mb-3">⛔ Банкротство ЕФРСБ</h3>
							{#if fin.bankruptcy_messages?.length}
								<div class="space-y-2">
									{#each fin.bankruptcy_messages as m}
										<div class="text-xs border-b border-gray-800 pb-1">
											<div class="flex gap-2">
												<span class="text-red-400">{m.type}</span>
												<span class="text-gray-600">{m.date}</span>
											</div>
											{#if m.text}<div class="text-gray-500 mt-0.5 line-clamp-2">{m.text}</div>{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/if}

				</div>
			{/if}

			<!-- Скоры агентов -->
			<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
				<h3 class="text-sm font-medium text-gray-300 mb-4">🤖 Оценки агентов</h3>
				<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
					{#each [
						{ key: 'analyst', label: 'Аналитик' },
						{ key: 'tech_specialist', label: 'Тех. спец' },
						{ key: 'marketer', label: 'Маркетолог' },
						{ key: 'strategist', label: 'Стратег' },
					] as ag}
						<div class="bg-gray-800 rounded-lg p-3 text-center">
							<div class="text-xs text-gray-500 mb-1">{ag.label}</div>
							<div class="text-2xl font-bold {scoreColor(agents[ag.key])}">{agents[ag.key] ?? '—'}</div>
							{#if agout[ag.key]?.summary}
								<div class="text-xs text-gray-600 mt-1 line-clamp-2">{agout[ag.key].summary}</div>
							{/if}
						</div>
					{/each}
				</div>

				<!-- Крючок и скрипт -->
				{#if result.hook}
					<div class="mt-4 p-3 bg-indigo-950/40 border border-indigo-800/30 rounded-lg">
						<div class="text-xs text-indigo-400 mb-1">Персональный крючок:</div>
						<div class="text-sm text-white">"{result.hook}"</div>
					</div>
				{/if}
				{#if result.script}
					<div class="mt-3 p-3 bg-gray-800 rounded-lg">
						<div class="text-xs text-gray-500 mb-1">Скрипт захода:</div>
						<div class="text-xs text-gray-300 whitespace-pre-line">{result.script}</div>
					</div>
				{/if}
			</div>

			<!-- Новости -->
			{#if result.news?.length}
				<div class="bg-gray-900 rounded-xl border border-gray-800 p-4">
					<h3 class="text-sm font-medium text-gray-300 mb-3">📰 Свежие новости</h3>
					<div class="space-y-2">
						{#each result.news as n}
							<div class="text-xs">
								<a href={n.url} target="_blank" class="text-indigo-400 hover:underline">{n.title}</a>
								<span class="text-gray-600 ml-2">{n.source} · {n.age_days ?? '?'} дн. назад</span>
								{#if n.is_fresh}<span class="text-green-600 ml-1">🔥</span>{/if}
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Ошибки и таймер -->
			<div class="text-xs text-gray-700 text-right">
				{#if result.timings_ms}Время анализа: {result.timings_ms} мс{/if}
				{#if result.errors?.length}<span class="text-red-800 ml-3">⚠ {result.errors.length} предупреждений</span>{/if}
			</div>

		</div>
	{/if}

	<!-- ── РЕЗУЛЬТАТ: портрет ── -->
	{#if portrait_results}
		{@const ar = portrait_results.agent_review || {}}
		{@const arCompanies = ar.companies || []}
		{@const ref = portrait_results.reference_profile}
		<div class="space-y-3">

			<!-- Эталонная компания (если была задана) -->
			{#if ref}
				<div class="bg-indigo-950/50 border border-indigo-700/50 rounded-xl p-4">
					<div class="text-xs text-indigo-400 mb-1.5 font-semibold">⭐ Эталон для поиска</div>
					<div class="flex items-start justify-between gap-3">
						<div>
							<div class="text-sm font-medium text-white">{ref.name_short || ref.name || '—'}</div>
							<div class="text-xs text-gray-400 mt-0.5">
								ИНН: {ref.inn || '—'} · {ref.city || '—'} · ОКВЭД {ref.okved || '—'}
								{#if ref.okved_name} — {ref.okved_name.slice(0,40)}{/if}
							</div>
							{#if ref.revenue || ref.employees_count}
								<div class="text-xs text-gray-500 mt-0.5">
									{#if ref.revenue}Выручка: {ref.revenue} · {/if}
									{#if ref.employees_count}Сотрудников: {ref.employees_count}{/if}
								</div>
							{/if}
						</div>
						<span class="text-xs px-2 py-0.5 rounded-full bg-green-900/50 text-green-400 flex-shrink-0">Действует</span>
					</div>
					<div class="mt-2 text-xs text-indigo-300">Ищем компании с похожим ОКВЭД, городом, размером и профилем</div>
				</div>
			{/if}

			<!-- Шапка: сколько найдено + критерии -->
			<div class="flex items-center justify-between flex-wrap gap-2">
				<div class="text-sm text-gray-400">
					Найдено: <span class="text-white font-medium">{portrait_results.total ?? 0}</span> компаний
					{#if portrait_results.criteria?.city}
						· <span class="text-indigo-300">{portrait_results.criteria.city}</span>
					{/if}
					{#if portrait_results.criteria?.okved}
						· ОКВЭД <span class="text-indigo-300">{portrait_results.criteria.okved}</span>
					{/if}
				</div>
				{#if portrait_results.errors?.length}
					<span class="text-xs text-red-400">⚠ {portrait_results.errors.length} ошибок</span>
				{/if}
			</div>

			<!-- AI-вывод по всей выборке -->
			{#if ar.summary}
				<div class="bg-indigo-950/40 border border-indigo-800/40 rounded-xl p-4">
					<div class="text-xs text-indigo-400 mb-1 font-semibold">🤖 AI-анализ выборки</div>
					<div class="text-sm text-gray-200">{ar.summary}</div>
				</div>
			{/if}

			<!-- Карточки компаний -->
			{#each (portrait_results.results || []) as company}
				{@const ai = arCompanies.find(x => x.inn === company.inn || x.name === (company.name || company.name_short))}
				{@const fitScore = ai?.fit_score ?? Math.round((company._portrait_match || 0) * 100)}
				{@const verdict = ai?.verdict || (fitScore >= 70 ? 'high' : fitScore >= 45 ? 'medium' : 'low')}
				<div class="bg-gray-900 rounded-xl border {verdict === 'high' ? 'border-green-800/50' : verdict === 'medium' ? 'border-yellow-800/40' : 'border-gray-800'} p-4 hover:border-indigo-700/60 transition-colors">

					<!-- Шапка компании -->
					<div class="flex items-start justify-between gap-3 mb-3">
						<div class="flex-1">
							<div class="flex items-center gap-2 flex-wrap">
								<span class="font-medium text-white">{company.name || company.name_short || '—'}</span>
								<span class="text-xs px-1.5 py-0.5 rounded-full {company.company_status === 'ACTIVE' ? 'bg-green-900/50 text-green-400' : 'bg-gray-800 text-gray-500'}">
									{company.company_status === 'ACTIVE' ? 'Действует' : (company.company_status || '—')}
								</span>
								{#if company._source === 'tavily'}
									<span class="text-xs px-1.5 py-0.5 rounded bg-teal-900/40 text-teal-400">Tavily</span>
								{:else if company._source === 'brave'}
									<span class="text-xs px-1.5 py-0.5 rounded bg-orange-900/40 text-orange-400">Brave</span>
								{/if}
							</div>
							<div class="text-xs text-gray-500 mt-0.5">
								ИНН: {company.inn || '—'} · {company.city || '—'} · {company.okved || ''} {company.okved_name ? '— ' + company.okved_name.slice(0,40) : ''}
							</div>
						</div>
						<!-- Fit score -->
						<div class="text-center flex-shrink-0">
							<div class="text-2xl font-bold {verdict === 'high' ? 'text-green-400' : verdict === 'medium' ? 'text-yellow-400' : 'text-gray-500'}">{fitScore}%</div>
							<div class="text-xs text-gray-500">совпадение</div>
						</div>
					</div>

					<!-- AI-вердикт по компании -->
					{#if ai}
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
							{#if ai.why_fits?.length}
								<div>
									<div class="text-xs text-green-400 mb-1 font-medium">✓ Подходит</div>
									{#each ai.why_fits.slice(0,3) as w}
										<div class="text-xs text-gray-300">· {w}</div>
									{/each}
								</div>
							{/if}
							{#if ai.why_not?.length}
								<div>
									<div class="text-xs text-red-400 mb-1 font-medium">✗ Риски</div>
									{#each ai.why_not.slice(0,2) as w}
										<div class="text-xs text-gray-400">· {w}</div>
									{/each}
								</div>
							{/if}
						</div>
						{#if ai.recommended_product || ai.next_action}
							<div class="flex flex-wrap gap-3 mb-3 text-xs">
								{#if ai.recommended_product}
									<span class="bg-indigo-900/40 text-indigo-300 px-2 py-1 rounded">💼 {ai.recommended_product}</span>
								{/if}
								{#if ai.next_action}
									<span class="bg-gray-800 text-gray-300 px-2 py-1 rounded">→ {ai.next_action}</span>
								{/if}
							</div>
						{/if}
					{/if}

					<!-- Данные компании + кнопка -->
					<div class="flex items-end justify-between gap-3 flex-wrap">
						<div class="text-xs text-gray-500 space-y-0.5">
							{#if company.director}<div>Руководитель: {company.director}</div>{/if}
							{#if company.revenue}<div>Выручка: {company.revenue}</div>{/if}
							{#if company.employees_count}<div>Сотрудников: {company.employees_count}</div>{/if}
							{#if company._matched_by?.length}
								<div class="text-indigo-500">✓ {company._matched_by.join(', ')}</div>
							{/if}
						</div>
						<button
							onclick={() => analyzePortraitItem(company)}
							class="text-xs px-4 py-1.5 rounded-lg bg-indigo-700 hover:bg-indigo-600 text-white transition-colors flex-shrink-0"
						>Полный анализ →</button>
					</div>
				</div>
			{/each}

			{#if portrait_results.results?.length === 0}
				<div class="text-center text-gray-500 py-8">Компании не найдены. Попробуй уточнить портрет или сменить отрасль/регион.</div>
			{/if}
		</div>
	{/if}

	<!-- ── РЕЗУЛЬТАТ: кластер ── -->
	{#if cluster_result}
		{@const groups = cluster_result.groups || {}}
		{@const parents = groups.parents || []}
		{@const subsidiaries = groups.subsidiaries || []}
		{@const siblings = groups.siblings || []}
		{@const person_companies = groups.person_companies || []}
		{@const ips = groups.ips || []}
		{@const persons = cluster_result.persons || []}
		{@const hasAnyRelated = parents.length || subsidiaries.length || siblings.length || person_companies.length || ips.length}

		<div class="space-y-4">
			<!-- Шапка -->
			<div class="text-sm text-gray-400">
				Найдено связей: <span class="text-white font-bold text-base">{cluster_result.total_companies ?? 1}</span> субъектов
				{#if cluster_result.total_revenue_estimate > 0}
					· Оборот группы: <span class="text-green-400">{fmtMoney(cluster_result.total_revenue_estimate)}</span>
				{/if}
			</div>

			<!-- Якорная компания -->
			{#if cluster_result.anchor}
				{@const a = cluster_result.anchor}
				<div class="bg-gray-900 rounded-xl border border-indigo-700/60 p-4">
					<div class="flex items-start justify-between gap-3">
						<div class="flex-1 min-w-0">
							<div class="text-xs text-indigo-400 mb-1 font-medium tracking-wide">⚓ ЯКОРНАЯ КОМПАНИЯ</div>
							<div class="font-semibold text-white">{a.name || '—'}</div>
							<div class="text-xs text-gray-500 mt-1 space-y-0.5">
								<div>ИНН: {a.inn || '—'} · ОГРН: {a.ogrn || '—'}</div>
								{#if a.city}<div>📍 {a.city}</div>{/if}
								{#if a.okved_name || a.okved}<div>ОКВЭД: {a.okved_name || a.okved}</div>{/if}
								{#if a.director}<div>Директор: {a.director}</div>{/if}
								{#if a.website}
									<div>🌐 <a href="{a.website.startsWith('http') ? a.website : 'https://'+a.website}"
										target="_blank" class="text-blue-400 hover:underline">{a.website}</a></div>
								{/if}
							</div>
							{#if (a.founders || []).length}
								<div class="flex flex-wrap gap-1 mt-2">
									{#each (a.founders || []) as f}
										<span class="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-400">
											{f.type === 'LEGAL' ? '🏢' : '👤'} {f.name}{f.share_percent != null ? ` ${f.share_percent}%` : ''}
										</span>
									{/each}
								</div>
							{/if}
						</div>
						<button onclick={() => analyzePortraitItem(a)}
							class="shrink-0 text-xs px-3 py-1.5 rounded-lg bg-indigo-700 hover:bg-indigo-600 text-white transition-colors">
							Анализ →
						</button>
					</div>
				</div>
			{/if}

			<!-- Профили физлиц-учредителей -->
			{#if persons.length}
				<div class="bg-gray-900 rounded-xl border border-blue-900/40 p-4">
					<div class="text-xs font-medium text-blue-400 mb-3">👤 Учредители — физические лица</div>
					<div class="space-y-3">
						{#each persons as p}
							<div class="bg-gray-800 rounded-lg p-3 text-xs">
								<div class="flex items-center gap-2 mb-1">
									<span class="text-gray-200 font-medium">{p.person_name || '—'}</span>
									{#if p.is_disqualified}
										<span class="px-1.5 py-0.5 rounded bg-red-900 text-red-400 text-xs">⛔ Дисквалифицирован</span>
									{/if}
									{#if p.is_mass_founder}
										<span class="px-1.5 py-0.5 rounded bg-yellow-900 text-yellow-400 text-xs">⚠ Массовый учредитель</span>
									{/if}
								</div>
								<div class="text-gray-600">ИНН: {p.person_inn || '—'}</div>
								<div class="flex gap-3 mt-1 text-gray-500">
									{#if p.founder_companies?.length}<span>Учредитель в {p.founder_companies.length} ООО</span>{/if}
									{#if p.director_companies?.length}<span>Директор в {p.director_companies.length} ООО</span>{/if}
									{#if p.ip_list?.length}<span>ИП: {p.ip_list.length}</span>{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Материнские компании (юрлица-учредители) -->
			{#if parents.length}
				<div class="bg-gray-900 rounded-xl border border-orange-900/40 p-4">
					<div class="text-xs font-medium text-orange-400 mb-3">🏛 Материнские компании ({parents.length})</div>
					<div class="space-y-2">
						{#each parents as c}
							<div class="flex items-start justify-between bg-gray-800 rounded-lg p-3 text-xs gap-2">
								<div class="min-w-0">
									<div class="text-gray-200 font-medium">{c.name || '—'}</div>
									<div class="text-gray-500 mt-0.5 flex flex-wrap gap-2">
										{#if c.inn}<span>ИНН: {c.inn}</span>{/if}
										{#if c.city}<span>📍 {c.city}</span>{/if}
										<span class="{c.status === 'ACTIVE' ? 'text-green-600' : 'text-gray-600'}">
											{c.status === 'ACTIVE' ? '● действует' : c.status || ''}
										</span>
									</div>
									<div class="text-orange-700 mt-0.5">{c._relation || ''}</div>
								</div>
								<button onclick={() => analyzePortraitItem(c)}
									class="shrink-0 text-xs px-2 py-1 rounded bg-gray-700 hover:bg-orange-800 text-gray-300 transition-colors">→</button>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Дочерние компании -->
			{#if subsidiaries.length}
				<div class="bg-gray-900 rounded-xl border border-green-900/40 p-4">
					<div class="text-xs font-medium text-green-400 mb-3">🏗 Дочерние компании ({subsidiaries.length})</div>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
						{#each subsidiaries as c}
							<div class="flex items-start justify-between bg-gray-800 rounded-lg p-2 text-xs gap-1">
								<div class="min-w-0">
									<div class="text-gray-200 font-medium truncate">{c.name || c.name_full || '—'}</div>
									<div class="text-gray-500 mt-0.5 flex flex-wrap gap-2">
										{#if c.inn}<span>ИНН: {c.inn}</span>{/if}
										<span class="{c.status === 'ACTIVE' ? 'text-green-600' : 'text-gray-600'}">
											{c.status === 'ACTIVE' ? '● действует' : '○ ' + (c.status || '')}
										</span>
									</div>
								</div>
								{#if c.inn}
									<button onclick={() => analyzePortraitItem(c)}
										class="shrink-0 text-xs px-2 py-0.5 rounded bg-gray-700 hover:bg-green-800 text-gray-300 transition-colors">→</button>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Сестринские компании -->
			{#if siblings.length}
				<div class="bg-gray-900 rounded-xl border border-purple-900/40 p-4">
					<div class="text-xs font-medium text-purple-400 mb-3">🔗 Сестринские компании ({siblings.length})</div>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
						{#each siblings as c}
							<div class="flex items-start justify-between bg-gray-800 rounded-lg p-2 text-xs gap-1">
								<div class="min-w-0">
									<div class="text-gray-200 font-medium truncate">{c.name || '—'}</div>
									<div class="text-gray-500 mt-0.5 flex flex-wrap gap-2">
										{#if c.inn}<span>ИНН: {c.inn}</span>{/if}
										<span class="{c.status === 'ACTIVE' ? 'text-green-600' : 'text-gray-600'}">
											{c.status === 'ACTIVE' ? '● действует' : '○ ' + (c.status || '')}
										</span>
									</div>
									<div class="text-purple-700 mt-0.5 truncate">{c._relation || ''}</div>
								</div>
								{#if c.inn}
									<button onclick={() => analyzePortraitItem(c)}
										class="shrink-0 text-xs px-2 py-0.5 rounded bg-gray-700 hover:bg-purple-800 text-gray-300 transition-colors">→</button>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Другие компании учредителей-физлиц -->
			{#if person_companies.length}
				<div class="bg-gray-900 rounded-xl border border-cyan-900/40 p-4">
					<div class="text-xs font-medium text-cyan-400 mb-3">🔄 Другие компании учредителей ({person_companies.length})</div>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
						{#each person_companies as c}
							<div class="flex items-start justify-between bg-gray-800 rounded-lg p-2 text-xs gap-1">
								<div class="min-w-0">
									<div class="text-gray-200 font-medium truncate">{c.name || c.name_full || '—'}</div>
									<div class="text-gray-500 mt-0.5 flex flex-wrap gap-2">
										{#if c.inn}<span>ИНН: {c.inn}</span>{/if}
										{#if c.city}<span>📍 {c.city}</span>{/if}
										<span class="{c.status === 'ACTIVE' ? 'text-green-600' : 'text-gray-600'}">
											{c.status === 'ACTIVE' ? '● действует' : '○ ' + (c.status || '')}
										</span>
									</div>
									<div class="text-cyan-800 mt-0.5 truncate">{c._relation || ''}</div>
								</div>
								{#if c.inn}
									<button onclick={() => analyzePortraitItem(c)}
										class="shrink-0 text-xs px-2 py-0.5 rounded bg-gray-700 hover:bg-cyan-800 text-gray-300 transition-colors">→</button>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- ИП учредителей -->
			{#if ips.length}
				<div class="bg-gray-900 rounded-xl border border-teal-900/40 p-4">
					<div class="text-xs font-medium text-teal-400 mb-3">💼 Индивидуальные предприниматели ({ips.length})</div>
					<div class="space-y-2">
						{#each ips as ip}
							<div class="bg-gray-800 rounded-lg p-3 text-xs">
								<div class="text-gray-200 font-medium">{ip.name || '—'}</div>
								<div class="text-gray-500 mt-0.5 flex flex-wrap gap-2">
									{#if ip.ogrnip}<span>ОГРНИП: {ip.ogrnip}</span>{/if}
									{#if ip.city}<span>📍 {ip.city}</span>{/if}
									<span class="{ip.status === 'ACTIVE' ? 'text-green-600' : 'text-gray-600'}">
										{ip.status === 'ACTIVE' ? '● действует' : '○ ' + (ip.status || '')}
									</span>
								</div>
								{#if ip.okved}<div class="text-gray-600 mt-0.5 truncate">ОКВЭД: {ip.okved}</div>{/if}
								<div class="text-teal-800 mt-0.5">{ip._relation || ''}</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Нет связей -->
			{#if !hasAnyRelated}
				<div class="text-center py-10 text-gray-600">
					<div class="text-3xl mb-2">🔍</div>
					<div class="text-sm">Связанных субъектов не найдено</div>
					<div class="text-xs mt-1 text-gray-700">Компания не имеет дочерних, материнских или аффилированных структур в ЕГРЮЛ</div>
				</div>
			{/if}

			<!-- Ошибки -->
			{#if cluster_result.errors?.length}
				<details class="mt-2">
					<summary class="text-xs text-gray-700 cursor-pointer">Предупреждения ({cluster_result.errors.length})</summary>
					<div class="text-xs text-gray-700 mt-1">{cluster_result.errors.join(' · ')}</div>
				</details>
			{/if}
		</div>
	{/if}

	<!-- ── Настройки (Ops) ── -->
	{#if show_config && config}
		<div class="mt-6 bg-gray-900 rounded-xl border border-gray-700 p-5">
			<h3 class="text-sm font-medium text-white mb-4">⚙ Настройки лидогенерации</h3>
			<div class="space-y-4">

				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="text-xs text-gray-500 mb-1 block">Минимальный скор для CRM</div>
						<input type="number" bind:value={config.score_threshold_crm} min="0" max="100"
							class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-white" />
					</div>
					<div>
						<div class="text-xs text-gray-500 mb-1 block">Макс. возраст новостей (дней)</div>
						<input type="number" bind:value={config.news_max_age_days} min="30" max="730"
							class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-white" />
					</div>
				</div>

				<div>
					<div class="text-xs text-gray-500 mb-1 block">Дополнение к промпту аналитика</div>
					<textarea bind:value={config.analyst_prompt_extra} rows="2"
						placeholder="Например: акцентируй внимание на строительных компаниях..."
						class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white resize-none"></textarea>
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Дополнение к промпту тех. специалиста</div>
					<textarea bind:value={config.tech_prompt_extra} rows="2"
						placeholder="Например: обращай внимание на наличие Active Directory..."
						class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white resize-none"></textarea>
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Дополнение к промпту маркетолога</div>
					<textarea bind:value={config.marketer_prompt_extra} rows="2"
						placeholder="Например: ищи триггеры связанные с госзакупками..."
						class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white resize-none"></textarea>
				</div>
				<div>
					<div class="text-xs text-gray-500 mb-1 block">Примеры портретов (по одному на строку)</div>
					<textarea
						rows="3"
						value={(config.portrait_intents || []).join('\n')}
						onchange={e => config.portrait_intents = e.target.value.split('\n').filter(Boolean)}
						class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white resize-none"
					></textarea>
				</div>

				<button onclick={saveConfig} disabled={config_saving}
					class="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm transition-colors disabled:opacity-50">
					{config_saving ? 'Сохраняю...' : '💾 Сохранить настройки'}
				</button>
			</div>
		</div>
	{/if}

	<!-- ══════════════════════════════════════════════════════════════════════ -->
	<!-- ── РЕЗУЛЬТАТ: Новости рынка ── -->
	{#if news_result}
		{@const articles = news_result.articles || []}
		{@const agents   = news_result.agents   || {}}

		<div class="space-y-4 mt-2">

			<!-- Шапка -->
			<div class="bg-gray-900 rounded-xl border border-gray-800 p-5">
				<div class="flex items-center justify-between flex-wrap gap-3">
					<div>
						<h2 class="text-base font-semibold text-white">📰 Новости рынка: «{news_result.query}»</h2>
						<p class="text-xs text-gray-500 mt-0.5">
							Найдено: {news_result.total_fresh} статей
							{#if news_result.query_en}
								· EN для NewsAPI: «{news_result.query_en}»
							{/if}
						</p>
						{#if news_result.sources_used}
							{@const s = news_result.sources_used}
							<div class="flex flex-wrap gap-1.5 mt-1.5">
								{#if s.tavily > 0}<span class="text-xs px-2 py-0.5 rounded-full bg-blue-900/40 text-blue-300">Tavily: {s.tavily}</span>{/if}
								{#if s.brave > 0}<span class="text-xs px-2 py-0.5 rounded-full bg-orange-900/40 text-orange-300">Brave: {s.brave}</span>{/if}
								{#if s.newsapi > 0}<span class="text-xs px-2 py-0.5 rounded-full bg-green-900/40 text-green-300">NewsAPI: {s.newsapi}</span>{/if}
								{#if s.tavily === 0 && s.brave === 0 && s.newsapi === 0}
									<span class="text-xs text-yellow-500">⚠ Добавь TAVILY_API_KEY или BRAVE_API_KEY в .env для поиска</span>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- Статьи -->
			{#if articles.length > 0}
				<div class="bg-gray-900 rounded-xl border border-gray-800 p-5">
					<h3 class="text-sm font-semibold text-white mb-3">Свежие публикации</h3>
					<div class="space-y-3">
						{#each articles as a}
							<div class="flex gap-3 p-3 rounded-lg bg-gray-800/60 hover:bg-gray-800 transition-colors group">
								{#if a.image}
									<img src={a.image} alt="" class="w-16 h-16 object-cover rounded-lg flex-shrink-0 bg-gray-700" onerror={(e) => e.currentTarget.style.display='none'} />
								{/if}
								<div class="flex-1 min-w-0">
									<div class="flex items-start gap-2 flex-wrap">
										<a href={a.url} target="_blank" rel="noopener"
											class="text-sm font-medium text-white hover:text-indigo-300 transition-colors leading-snug group-hover:underline flex-1">
											{a.title}
										</a>
										{#if a.is_fresh}
											<span class="text-xs px-1.5 py-0.5 rounded-full bg-green-900/50 text-green-400 flex-shrink-0">🟢 свежая</span>
										{/if}
									</div>
									{#if a.description}
										<p class="text-xs text-gray-400 mt-1 line-clamp-2">{a.description}</p>
									{/if}
									<div class="flex items-center gap-3 mt-1.5 text-xs text-gray-600">
										{#if a.source}<span class="text-gray-500">{a.source}</span>{/if}
										{#if a.age_days != null}
											<span>{a.age_days === 0 ? 'сегодня' : a.age_days + ' дн. назад'}</span>
										{/if}
										{#if a.author}<span class="truncate max-w-[160px]">{a.author}</span>{/if}
									</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{:else}
				<div class="bg-gray-900 rounded-xl border border-gray-800 p-5 text-center text-sm space-y-1.5">
					<div class="text-gray-400">Статьи не найдены через доступные источники.</div>
					<div class="text-xs text-gray-600">
						Для поиска по-русски добавь <code class="text-indigo-400 bg-indigo-950/40 px-1 rounded">TAVILY_API_KEY</code> в .env
						(бесплатно на tavily.com). NewsAPI ищет только англоязычные источники.
					</div>
				</div>
			{/if}

			<!-- AI-агенты -->
			{#if Object.keys(agents).length > 0}
				<div class="bg-gray-900 rounded-xl border border-gray-800 p-5">
					<h3 class="text-sm font-semibold text-white mb-4">🤖 Анализ AI-агентов</h3>
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">

						<!-- Аналитик рынка -->
						{#if agents.market_analyst}
							{@const a = agents.market_analyst}
							<div class="bg-blue-950/30 border border-blue-800/40 rounded-xl p-4">
								<div class="flex items-center justify-between mb-2">
									<span class="text-xs font-semibold text-blue-300">📊 Аналитик рынка</span>
									{#if a.score != null}<span class="text-xs text-blue-400 font-bold">{a.score}/100</span>{/if}
								</div>
								{#if a.error}
									<p class="text-xs text-red-400">⚠ Ошибка: {a.error || 'агент не ответил'}</p>
								{:else}
									{#if a.summary}<p class="text-xs text-gray-300 mb-2">{a.summary}</p>{/if}
									{#if a.key_trends?.length}
										<div class="text-xs text-gray-400 mb-1 font-medium">Тренды:</div>
										<ul class="text-xs text-gray-300 space-y-0.5 mb-2">
											{#each a.key_trends.slice(0,4) as t}<li>• {t}</li>{/each}
										</ul>
									{/if}
									{#if a.growth_areas?.length}
										<div class="flex flex-wrap gap-1">
											{#each a.growth_areas.slice(0,4) as area}
												<span class="text-xs px-2 py-0.5 rounded-full bg-green-900/40 text-green-400">↑ {area}</span>
											{/each}
										</div>
									{/if}
								{/if}
							</div>
						{/if}

						<!-- Технический эксперт -->
						{#if agents.tech_expert}
							{@const a = agents.tech_expert}
							<div class="bg-purple-950/30 border border-purple-800/40 rounded-xl p-4">
								<div class="flex items-center justify-between mb-2">
									<span class="text-xs font-semibold text-purple-300">🔧 Технический эксперт</span>
									{#if a.score != null}<span class="text-xs text-purple-400 font-bold">{a.score}/100</span>{/if}
								</div>
								{#if a.error}
									<p class="text-xs text-red-400">⚠ Ошибка агента: {a.error || 'неизвестная ошибка'}</p>
								{:else}
									{#if a.summary}<p class="text-xs text-gray-300 mb-2">{a.summary}</p>{/if}
									{#if a.hot_technologies?.length}
										<div class="text-xs text-gray-400 mb-1 font-medium">Горячие технологии:</div>
										<div class="flex flex-wrap gap-1 mb-2">
											{#each a.hot_technologies.slice(0,5) as t}
												<span class="text-xs px-2 py-0.5 rounded-full bg-purple-900/40 text-purple-300">🔥 {t}</span>
											{/each}
										</div>
									{/if}
									{#if a.recommended_solutions?.length}
										<div class="text-xs text-gray-400 mb-1 font-medium">Рекомендуемые решения:</div>
										<div class="flex flex-wrap gap-1">
											{#each a.recommended_solutions.slice(0,4) as s}
												<span class="text-xs px-2 py-0.5 rounded-full bg-indigo-900/40 text-indigo-300">{s}</span>
											{/each}
										</div>
									{/if}
								{/if}
							</div>
						{/if}

						<!-- Стратег продаж -->
						{#if agents.sales_strategist}
							{@const a = agents.sales_strategist}
							<div class="bg-orange-950/30 border border-orange-800/40 rounded-xl p-4">
								<div class="flex items-center justify-between mb-2">
									<span class="text-xs font-semibold text-orange-300">💼 Стратег продаж</span>
									{#if a.score != null}<span class="text-xs text-orange-400 font-bold">{a.score}/100</span>{/if}
								</div>
								{#if a.error}
									<p class="text-xs text-red-400">⚠ {a.error}</p>
								{:else}
									{#if a.summary}<p class="text-xs text-gray-300 mb-2">{a.summary}</p>{/if}
									{#if a.sales_opportunities?.length}
										<div class="text-xs text-gray-400 mb-1 font-medium">Возможности:</div>
										<ul class="text-xs text-gray-300 space-y-0.5 mb-2">
											{#each a.sales_opportunities.slice(0,3) as o}<li>• {o}</li>{/each}
										</ul>
									{/if}
									{#if a.target_segments?.length}
										<div class="flex flex-wrap gap-1 mb-2">
											{#each a.target_segments.slice(0,4) as seg}
												<span class="text-xs px-2 py-0.5 rounded-full bg-orange-900/40 text-orange-300">{seg}</span>
											{/each}
										</div>
									{/if}
									{#if a.best_message}
										<div class="text-xs bg-orange-900/20 rounded px-2 py-1.5 text-orange-200 italic">
											💬 «{a.best_message}»
										</div>
									{/if}
								{/if}
							</div>
						{/if}

						<!-- Аналитик рисков -->
						{#if agents.risk_analyst}
							{@const a = agents.risk_analyst}
							<div class="bg-red-950/30 border border-red-800/40 rounded-xl p-4">
								<div class="flex items-center justify-between mb-2">
									<span class="text-xs font-semibold text-red-300">🛡 Аналитик рисков</span>
									{#if a.score != null}<span class="text-xs text-red-400 font-bold">{a.score}/100</span>{/if}
								</div>
								{#if a.error}
									<p class="text-xs text-red-400">⚠ Ошибка: {a.error || 'агент не ответил'}</p>
								{:else}
									{#if a.summary}<p class="text-xs text-gray-300 mb-2">{a.summary}</p>{/if}
									{#if a.threats?.length}
										<div class="text-xs text-gray-400 mb-1 font-medium">Угрозы:</div>
										<ul class="text-xs text-gray-300 space-y-0.5 mb-2">
											{#each a.threats.slice(0,4) as t}<li>⚠ {t}</li>{/each}
										</ul>
									{/if}
									{#if a.action_items?.length}
										<div class="flex flex-wrap gap-1">
											{#each a.action_items.slice(0,3) as item}
												<span class="text-xs px-2 py-0.5 rounded-full bg-red-900/40 text-red-300">{item}</span>
											{/each}
										</div>
									{/if}
								{/if}
							</div>
						{/if}

						<!-- Контент-маркетолог — занимает всю ширину -->
						{#if agents.content_creator}
							{@const a = agents.content_creator}
							<div class="md:col-span-2 bg-teal-950/30 border border-teal-800/40 rounded-xl p-4">
								<div class="flex items-center justify-between mb-2">
									<span class="text-xs font-semibold text-teal-300">✍ Контент-маркетолог</span>
									{#if a.score != null}<span class="text-xs text-teal-400 font-bold">{a.score}/100</span>{/if}
								</div>
								{#if a.error}
									<p class="text-xs text-red-400">⚠ Ошибка: {a.error || 'агент не ответил'}</p>
								{:else}
									{#if a.summary}<p class="text-xs text-gray-300 mb-3">{a.summary}</p>{/if}
									<div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
										{#if a.article_ideas?.length}
											<div>
												<div class="text-xs text-gray-400 mb-1 font-medium">Идеи статей:</div>
												<ul class="text-xs text-gray-300 space-y-0.5">
													{#each a.article_ideas.slice(0,3) as i}<li>• {i}</li>{/each}
												</ul>
											</div>
										{/if}
										{#if a.email_subjects?.length}
											<div>
												<div class="text-xs text-gray-400 mb-1 font-medium">Темы писем:</div>
												<ul class="text-xs text-gray-300 space-y-0.5">
													{#each a.email_subjects.slice(0,3) as s}<li>📧 {s}</li>{/each}
												</ul>
											</div>
										{/if}
										{#if a.webinar_topics?.length}
											<div>
												<div class="text-xs text-gray-400 mb-1 font-medium">Темы вебинаров:</div>
												<ul class="text-xs text-gray-300 space-y-0.5">
													{#each a.webinar_topics.slice(0,3) as t}<li>🎙 {t}</li>{/each}
												</ul>
											</div>
										{/if}
									</div>
									{#if a.linkedin_hooks?.length}
										<div class="mt-2">
											<div class="text-xs text-gray-400 mb-1 font-medium">LinkedIn-крючки:</div>
											<div class="flex flex-wrap gap-1">
												{#each a.linkedin_hooks.slice(0,3) as h}
													<span class="text-xs px-2 py-0.5 rounded-full bg-teal-900/40 text-teal-300">🔗 {h}</span>
												{/each}
											</div>
										</div>
									{/if}
								{/if}
							</div>
						{/if}

					</div>
				</div>
			{/if}

		</div>
	{/if}

{/if}
</div>
