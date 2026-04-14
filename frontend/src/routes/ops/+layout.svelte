<script>
	import { page } from '$app/stores';
	import { getApiUrl } from '$lib/websocket.js';
	import { onMount } from 'svelte';

	let { children } = $props();

	const API = getApiUrl();

	const nav = [
		{ href: '/ops',          label: 'Обзор',      exact: true },
		{ href: '/ops/intents',  label: '🎯 Интенты' },
		{ href: '/ops/voice',    label: '🎙 Голос' },
		{ href: '/ops/agents',       label: '🤖 Агенты'     },
		{ href: '/ops/email-agents', label: '📧 Агенты почты' },
		{ href: '/ops/search',   label: '🔍 Поиск' },
		{ href: '/ops/queue',    label: 'Очередь' },
		{ href: '/ops/stats',    label: 'Статистика' },
		{ href: '/ops/insights', label: 'Инсайты' },
		{ href: '/ops/api-limits', label: '🔑 API Лимиты' },
	];

	function isActive(href, exact) {
		const p = $page.url.pathname;
		if (exact) return p === href || p === href + '/';
		return p === href || p.startsWith(href + '/');
	}

	let queueOpen = $state(0);
	let queueCritical = $state(0);

	async function pollQueue() {
		try {
			const r = await fetch(`${API}/api/ops/queue`);
			const d = await r.json();
			const open = d.open || [];
			queueOpen = open.length;
			queueCritical = open.filter((x) => x.severity === 'critical').length;
		} catch {
			queueOpen = 0;
			queueCritical = 0;
		}
	}

	onMount(() => {
		pollQueue();
		const t = setInterval(pollQueue, 15000);
		return () => clearInterval(t);
	});
</script>

<svelte:head><title>Ops · SmartCRM</title></svelte:head>

<div class="flex-1 flex flex-col overflow-hidden min-h-0">
	<header class="bg-gray-900 border-b border-gray-800 px-6 py-4 shrink-0">
		<div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
			<div>
				<h1 class="text-lg font-semibold text-white">Ops / Качество</h1>
				<p class="text-sm text-gray-400">
					Процессы, трейсы и очередь решений. Критичные задачи: <span class="text-red-400 font-medium">{queueCritical}</span>,
					всего открытых: <span class="text-white font-medium">{queueOpen}</span>
				</p>
			</div>
		</div>

		<nav class="flex flex-wrap gap-1 mt-3">
			{#each nav as item}
				<a
					href={item.href}
					class="px-3 py-1.5 rounded-lg text-sm transition-colors
						{isActive(item.href, item.exact)
						? 'bg-indigo-600 text-white'
						: 'text-gray-400 hover:text-white hover:bg-gray-800'}"
				>
					{item.label}
					{#if item.href === '/ops/queue' && queueCritical > 0}
						<span class="ml-1 text-xs bg-red-600 text-white px-1.5 py-0.5 rounded">{queueCritical}</span>
					{/if}
				</a>
			{/each}
		</nav>
	</header>

	<div class="flex-1 overflow-y-auto min-h-0">
		{@render children()}
	</div>
</div>
