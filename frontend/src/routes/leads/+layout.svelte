<script>
	import { page } from '$app/stores';

	let { children } = $props();

	const tabs = [
		{ href: '/leads/funnel', label: 'Воронка', icon: '📊' },
		{ href: '/leads/list', label: 'Список', icon: '☰' },
		{ href: '/leads/calendar', label: 'Календарь', icon: '📅' },
		{ href: '/leads/tasks', label: 'Задачи', icon: '✓' },
		{ href: '/leads/focus', label: 'Фокус', icon: '🍅' },
		{ href: '/leads/analytics', label: 'Аналитика', icon: '📈' },
	];

	function tabActive(href) {
		const p = $page.url.pathname;
		if (href === '/leads/list') {
			return p === '/leads/list' || p === '/leads' || /^\/leads\/\d+$/.test(p);
		}
		return p === href || p.startsWith(href + '/');
	}
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden">
	<div class="shrink-0 border-b border-gray-800 bg-gray-900/95 px-4 py-2">
		<div class="flex flex-wrap items-center gap-1">
			<span class="text-xs text-gray-500 mr-2 hidden sm:inline">Лиды</span>
			{#each tabs as t}
				<a
					href={t.href}
					class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors
						{tabActive(t.href)
						? 'bg-indigo-600 text-white'
						: 'text-gray-400 hover:text-white hover:bg-gray-800'}"
				>
					<span class="text-xs opacity-80">{t.icon}</span>
					{t.label}
				</a>
			{/each}
		</div>
		<p class="text-[11px] text-gray-600 mt-1.5 px-1">
			Карточка сделки — из списка или воронки. Ссылка /crm ведёт сюда же.
		</p>
	</div>
	<div class="flex-1 flex flex-col min-h-0 overflow-hidden">
		{@render children()}
	</div>
</div>
