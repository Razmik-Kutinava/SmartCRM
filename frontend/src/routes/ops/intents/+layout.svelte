<script>
	import { page } from '$app/stores';
	let { children } = $props();

	const nav = [
		{ href: '/ops/intents/traces',    label: 'Трейсы' },
		{ href: '/ops/intents/improve',   label: 'Улучшение' },
		{ href: '/ops/intents/import',    label: '📥 Импорт' },
		{ href: '/ops/intents/eval',      label: 'Eval' },
		{ href: '/ops/intents/scenarios', label: 'Сценарии' },
		{ href: '/ops/intents/history',   label: 'История' },
	];

	function isActive(href) {
		const p = $page.url.pathname;
		return p === href || p.startsWith(href + '/');
	}
</script>

<div class="flex flex-col h-full">
	<!-- Подзаголовок раздела -->
	<div class="border-b border-gray-800 px-6 py-3 bg-gray-900/50">
		<div class="flex items-center gap-2 mb-2">
			<span class="text-xs text-indigo-400 font-medium uppercase tracking-wider">🎯 Интенты / Hermes</span>
			<span class="text-xs text-gray-600">— распознавание команд, few-shot промпт, eval точности</span>
		</div>
		<nav class="flex flex-wrap gap-1">
			{#each nav as item}
				<a href={item.href}
					class="px-3 py-1 rounded-lg text-sm transition-colors
						{isActive(item.href)
							? 'bg-indigo-600/80 text-white'
							: 'text-gray-400 hover:text-white hover:bg-gray-800'}">
					{item.label}
				</a>
			{/each}
		</nav>
	</div>

	<div class="flex-1 overflow-y-auto min-h-0">
		{@render children()}
	</div>
</div>
