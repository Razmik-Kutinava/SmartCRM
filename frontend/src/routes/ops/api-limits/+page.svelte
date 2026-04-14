<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	const API = getApiUrl();

	let stats     = $state([]);
	let live      = $state(null);
	let loading   = $state(true);
	let liveLoading = $state(false);
	let error     = $state('');
	let lastRefresh = $state('');
	let alerts    = $state([]);
	let summary   = $state({ services_total: 0, alerts_total: 0, critical_total: 0, warning_total: 0 });

	async function loadStats() {
		loading = true; error = '';
		try {
			const r = await fetch(`${API}/api/usage/stats`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			stats = d.services || [];
			alerts = d.alerts || [];
			summary = d.summary || { services_total: 0, alerts_total: 0, critical_total: 0, warning_total: 0 };
			lastRefresh = new Date().toLocaleTimeString('ru');
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	async function loadLive() {
		liveLoading = true;
		try {
			const r = await fetch(`${API}/api/usage/live`);
			if (!r.ok) throw new Error(await r.text());
			live = await r.json();
		} catch (e) {
			error = e.message;
		} finally {
			liveLoading = false;
		}
	}

	async function resetService(svc) {
		if (!confirm(`Сбросить счётчик ${svc}?`)) return;
		await fetch(`${API}/api/usage/reset/${svc}`, { method: 'POST' });
		await loadStats();
	}

	async function resetAll() {
		if (!confirm('Сбросить ВСЕ счётчики?')) return;
		await fetch(`${API}/api/usage/reset_all`, { method: 'POST' });
		await loadStats();
	}

	onMount(() => {
		loadStats();
		loadLive();
		const t = setInterval(loadStats, 30_000);
		return () => clearInterval(t);
	});

	function fmtNum(n) {
		if (!n && n !== 0) return '—';
		if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
		if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
		return n.toString();
	}

	function pctColor(pct) {
		if (!pct && pct !== 0) return 'text-gray-500';
		if (pct >= 90) return 'text-red-400';
		if (pct >= 70) return 'text-orange-400';
		if (pct >= 40) return 'text-yellow-400';
		return 'text-green-400';
	}

	function pctBar(pct) {
		if (!pct && pct !== 0) return 'bg-gray-700';
		if (pct >= 90) return 'bg-red-500';
		if (pct >= 70) return 'bg-orange-500';
		if (pct >= 40) return 'bg-yellow-500';
		return 'bg-green-500';
	}

	function keyBadge(status) {
		if (status === 'set') return 'bg-green-900/40 text-green-400';
		if (status === 'dummy') return 'bg-yellow-900/40 text-yellow-400';
		return 'bg-red-900/40 text-red-400';
	}

	function keyLabel(status) {
		if (status === 'set') return '● ключ задан';
		if (status === 'dummy') return '⚠ не задан';
		return '✕ отсутствует';
	}

	function planBadge(plan) {
		if (plan === 'paid') return 'bg-purple-900/40 text-purple-300';
		if (plan === 'local') return 'bg-blue-900/40 text-blue-300';
		return 'bg-gray-800 text-gray-400';
	}

	function fmtDate(iso) {
		if (!iso) return '—';
		try { return new Date(iso).toLocaleString('ru', { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' }); }
		catch { return iso; }
	}

	// Токены для LLM-сервисов
	function isLlm(svc) { return svc === 'groq' || svc === 'ollama'; }

	function usagePct(svc) {
		return svc.pct_day ?? svc.pct_month ?? null;
	}

	function serviceSeverity(svc) {
		const pct = usagePct(svc);
		if (pct !== null && pct >= 90) return 'critical';
		if (pct !== null && pct >= 70) return 'warning';
		if ((svc.errors_today || 0) > 0) return 'warning';
		return 'ok';
	}
</script>

<div class="flex-1 overflow-y-auto bg-gray-950 p-6">

	<!-- Заголовок -->
	<div class="flex items-center justify-between mb-6 flex-wrap gap-3">
		<div>
			<h2 class="text-lg font-semibold text-white">🔑 API Лимиты и использование</h2>
			<p class="text-xs text-gray-500 mt-0.5">
				Счётчики сбрасываются: дневные — каждый день, месячные — каждый месяц.
				{#if lastRefresh}Обновлено: {lastRefresh}{/if}
			</p>
		</div>
		<div class="flex gap-2">
			<button onclick={loadStats}
				class="text-xs px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors">
				↻ Обновить
			</button>
			<button onclick={loadLive} disabled={liveLoading}
				class="text-xs px-3 py-1.5 rounded-lg bg-indigo-900/50 text-indigo-300 hover:bg-indigo-800/50 transition-colors disabled:opacity-50">
				{liveLoading ? '...' : '⚡ Живые данные'}
			</button>
			<button onclick={resetAll}
				class="text-xs px-3 py-1.5 rounded-lg bg-red-900/30 text-red-400 hover:bg-red-900/60 transition-colors">
				🗑 Сбросить всё
			</button>
		</div>
	</div>

	{#if error}
		<div class="bg-red-950 border border-red-800 rounded-lg px-4 py-3 text-sm text-red-300 mb-4">✕ {error}</div>
	{/if}

	<!-- Сводка и ранние предупреждения -->
	<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
		<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
			<div class="text-xs text-gray-500">Сервисов</div>
			<div class="text-lg font-semibold text-white">{summary.services_total || stats.length}</div>
		</div>
		<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
			<div class="text-xs text-gray-500">Всего предупреждений</div>
			<div class="text-lg font-semibold text-yellow-300">{summary.alerts_total || 0}</div>
		</div>
		<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
			<div class="text-xs text-gray-500">Критичные</div>
			<div class="text-lg font-semibold text-red-400">{summary.critical_total || 0}</div>
		</div>
		<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
			<div class="text-xs text-gray-500">Предупреждения</div>
			<div class="text-lg font-semibold text-orange-300">{summary.warning_total || 0}</div>
		</div>
	</div>

	{#if alerts.length > 0}
		<div class="space-y-2 mb-6">
			{#each alerts.slice(0, 6) as a}
				<div class="rounded-lg border px-3 py-2 text-xs
					{a.level === 'critical'
						? 'bg-red-950/60 border-red-800 text-red-300'
						: 'bg-yellow-950/40 border-yellow-800 text-yellow-300'}">
					{a.level === 'critical' ? '⛔' : '⚠'} {a.message}
				</div>
			{/each}
			{#if alerts.length > 6}
				<div class="text-xs text-gray-500">+ ещё {alerts.length - 6} предупреждений</div>
			{/if}
		</div>
	{/if}

	<!-- Живые данные провайдеров -->
	{#if live}
		{@const g  = live.groq   || {}}
		{@const h  = live.hunter || {}}
		{@const ap = live.apollo || {}}
		{@const ch = live.checko || {}}
		{@const chRt = ch.runtime || {}}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">

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
					<div class="text-xs text-gray-500 mt-1">Доступно моделей: {g.models_count}</div>
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
					<div class="text-xs text-gray-500 mt-2">Поиски: {h.searches_used}/{h.searches_used + h.searches_available}</div>
					<div class="w-full bg-gray-700 rounded-full h-1 mt-1">
						<div class="h-1 rounded-full {pctBar(h.searches_used + h.searches_available > 0 ? Math.round(h.searches_used / (h.searches_used + h.searches_available) * 100) : 0)}"
							style="width:{h.searches_used + h.searches_available > 0 ? Math.min(Math.round(h.searches_used / (h.searches_used + h.searches_available) * 100), 100) : 0}%">
						</div>
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

	<!-- Таблица статистики -->
	{#if loading}
		<div class="text-center text-gray-500 py-12">Загружаю статистику...</div>
	{:else if stats.length === 0}
		<div class="text-center text-gray-500 py-12">Нет данных. Начни использовать систему — счётчики появятся здесь.</div>
	{:else}
		<div class="space-y-3">
			{#each stats as s}
				{@const pct = s.pct_day ?? s.pct_month ?? null}
				{@const totalTokensDay = (s.tokens_prompt_today || 0) + (s.tokens_completion_today || 0)}
				{@const totalTokensMonth = (s.tokens_prompt_month || 0) + (s.tokens_completion_month || 0)}
				{@const sev = serviceSeverity(s)}
				<div class="bg-gray-900 rounded-xl border border-gray-800 p-4 hover:border-gray-700 transition-colors">
					<div class="flex items-start gap-4 flex-wrap">

						<!-- Название и статус -->
						<div class="flex-1 min-w-[160px]">
							<div class="flex items-center gap-2 flex-wrap">
								<span class="text-sm font-medium text-white">{s.name}</span>
								<span class="text-xs px-1.5 py-0.5 rounded {planBadge(s.plan)}">{s.plan}</span>
								{#if sev === 'critical'}
									<span class="text-xs px-1.5 py-0.5 rounded bg-red-900/40 text-red-400">критично</span>
								{:else if sev === 'warning'}
									<span class="text-xs px-1.5 py-0.5 rounded bg-yellow-900/40 text-yellow-400">внимание</span>
								{/if}
								{#if s.key_status}
									<span class="text-xs px-1.5 py-0.5 rounded {keyBadge(s.key_status)}">{keyLabel(s.key_status)}</span>
								{/if}
							</div>
							{#if s.last_used}
								<div class="text-xs text-gray-600 mt-0.5">последний вызов: {fmtDate(s.last_used)}</div>
							{:else}
								<div class="text-xs text-gray-700 mt-0.5">не использовался</div>
							{/if}
							{#if s.docs}
								<a href={s.docs} target="_blank" rel="noopener"
									class="text-xs text-indigo-500 hover:text-indigo-400 mt-0.5 block">↗ документация</a>
							{/if}
						</div>

						<!-- Счётчики запросов -->
						<div class="flex gap-6 flex-wrap">
							<div class="text-center">
								<div class="text-lg font-bold text-white">{fmtNum(s.calls_today)}</div>
								<div class="text-xs text-gray-500">сегодня</div>
								{#if s.limit_day_calls}
									<div class="text-xs {pctColor(s.pct_day)} mt-0.5">/ {fmtNum(s.limit_day_calls)}</div>
								{/if}
							</div>
							<div class="text-center">
								<div class="text-lg font-bold text-white">{fmtNum(s.calls_month)}</div>
								<div class="text-xs text-gray-500">месяц</div>
								{#if s.limit_month_calls}
									<div class="text-xs {pctColor(s.pct_month)} mt-0.5">/ {fmtNum(s.limit_month_calls)}</div>
								{/if}
							</div>
							<div class="text-center">
								<div class="text-base font-semibold text-gray-400">{fmtNum(s.calls_total)}</div>
								<div class="text-xs text-gray-600">всего</div>
							</div>
							{#if s.errors_today > 0}
								<div class="text-center">
									<div class="text-base font-semibold text-red-400">{s.errors_today}</div>
									<div class="text-xs text-gray-600">ошибки/день</div>
								</div>
							{/if}
						</div>

						<!-- Токены (только для LLM) -->
						{#if isLlm(s.service)}
							<div class="flex gap-6 flex-wrap border-l border-gray-700 pl-4">
								<div class="text-center">
									<div class="text-sm font-bold text-indigo-300">{fmtNum(totalTokensDay)}</div>
									<div class="text-xs text-gray-500">токенов сегодня</div>
									{#if s.limit_day_tokens}
										<div class="text-xs {pctColor(s.pct_day)} mt-0.5">/ {fmtNum(s.limit_day_tokens)}</div>
									{/if}
								</div>
								<div class="text-center">
									<div class="text-sm font-bold text-indigo-300">{fmtNum(totalTokensMonth)}</div>
									<div class="text-xs text-gray-500">токенов месяц</div>
								</div>
								<div class="text-center">
									<div class="text-xs text-gray-500">prompt</div>
									<div class="text-xs text-gray-400">{fmtNum(s.tokens_prompt_today)}</div>
								</div>
								<div class="text-center">
									<div class="text-xs text-gray-500">completion</div>
									<div class="text-xs text-gray-400">{fmtNum(s.tokens_completion_today)}</div>
								</div>
							</div>
						{/if}

						<!-- Кнопка сброса -->
						<button onclick={() => resetService(s.service)}
							class="ml-auto self-start text-xs px-2 py-1 rounded bg-gray-800 text-gray-500 hover:text-red-400 hover:bg-red-900/20 transition-colors">
							↺
						</button>
					</div>

					<!-- Прогресс-бар если есть лимит -->
					{#if pct !== null}
						<div class="mt-3">
							<div class="flex justify-between text-xs text-gray-600 mb-1">
								<span>{s.reset === 'daily' ? 'использовано сегодня' : 'использовано в месяце'}</span>
								<span class="{pctColor(pct)}">{pct}%</span>
							</div>
							<div class="w-full bg-gray-800 rounded-full h-1.5">
								<div class="h-1.5 rounded-full transition-all {pctBar(pct)}" style="width:{Math.min(pct,100)}%"></div>
							</div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}

</div>
