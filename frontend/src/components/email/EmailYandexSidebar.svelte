<script>
	import {
		EMAIL_NAV_MAIN,
		EMAIL_NAV_CUSTOM,
		EMAIL_NAV_SYSTEM,
		EMAIL_NAV_SMARTCRM,
	} from '$lib/email/emailListLogic.js';

	let {
		activeFolder = $bindable('inbox'),
		folderCount = () => 0,
		accounts = [],
		filterAccountId = $bindable(''),
		syncLoading = false,
		onCompose = () => {},
		onSync = () => {},
		onSettings = () => {},
		onFolderChange = () => {},
		onAccountFilterChange = () => {},
	} = $props();

	function selectFolder(key) {
		activeFolder = key;
		onFolderChange(key);
	}
</script>

<aside
	class="flex flex-col w-56 flex-shrink-0 border-r border-black/5 email-yandex-sidebar"
	data-testid="email-yandex-sidebar"
>
	<div class="px-4 pt-5 pb-3">
		<h1 class="text-xl font-bold text-gray-900 tracking-tight">Почта</h1>
	</div>

	<div class="px-3 pb-3 flex items-center gap-2">
		<button
			type="button"
			class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl bg-[#ffdb4d] hover:bg-[#ffcc00] text-sm font-semibold text-gray-900 shadow-sm transition-colors"
			onclick={onCompose}
			data-testid="email-compose-btn"
		>
			<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M12 20h9" /><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
			</svg>
			Написать
		</button>
		<button
			type="button"
			class="w-10 h-10 flex items-center justify-center rounded-2xl bg-white/70 hover:bg-white text-gray-700 border border-black/5 transition-colors disabled:opacity-50"
			title="Синхронизировать"
			disabled={syncLoading || !accounts.length}
			onclick={onSync}
			data-testid="email-sync-btn"
		>
			{#if syncLoading}
				<span class="text-xs">…</span>
			{:else}
				<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
					<path d="M3 3v5h5" /><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
					<path d="M16 16h5v5" />
				</svg>
			{/if}
		</button>
	</div>

	<nav class="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
		{#each EMAIL_NAV_MAIN as item (item.key)}
			{@const cnt = item.showCount ? folderCount(item.key) : 0}
			<button
				type="button"
				class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm text-left transition-colors
					{activeFolder === item.key ? 'bg-white/90 shadow-sm font-medium text-gray-900' : 'text-gray-800 hover:bg-white/50'}"
				onclick={() => selectFolder(item.key)}
				data-testid="nav-folder-{item.key}"
			>
				<span class="w-5 h-5 flex items-center justify-center opacity-70">
					{#if item.icon === 'inbox'}
						<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-6l-2 3H10l-2-3H2" /><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" /></svg>
					{:else if item.icon === 'star'}
						<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
					{:else}
						<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" /></svg>
					{/if}
				</span>
				<span class="flex-1">{item.label}</span>
				{#if cnt > 0}
					<span class="text-xs text-gray-500 tabular-nums">{cnt > 9999 ? '9999+' : cnt}</span>
				{/if}
			</button>
		{/each}

		<div class="pt-4 pb-1 px-3 flex items-center justify-between">
			<span class="text-sm font-medium text-gray-700 flex items-center gap-1.5">
				<svg class="w-4 h-4 opacity-60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" /></svg>
				Мои папки
			</span>
			<button type="button" class="text-gray-500 hover:text-gray-800 p-0.5" title="Настройки почты" onclick={onSettings}>
				<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14" /></svg>
			</button>
		</div>

		{#each EMAIL_NAV_CUSTOM as item (item.key)}
			{@const cnt = item.showCount ? folderCount(item.key) : 0}
			<button
				type="button"
				class="w-full flex items-center gap-2.5 pl-8 pr-3 py-1.5 rounded-xl text-sm text-left transition-colors
					{activeFolder === item.key ? 'bg-white/90 shadow-sm font-medium text-gray-900' : 'text-gray-700 hover:bg-white/50'}"
				onclick={() => selectFolder(item.key)}
				data-testid="nav-folder-{item.key}"
			>
				<span class="flex-1 {item.key === 'mailing' ? 'text-gray-500' : ''}">{item.label}</span>
				{#if cnt > 0}
					<span class="text-xs text-gray-500 tabular-nums">{cnt}</span>
				{/if}
			</button>
		{/each}

		<div class="pt-3 space-y-0.5">
			{#each EMAIL_NAV_SYSTEM as item (item.key)}
				<button
					type="button"
					class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm text-left transition-colors
						{item.disabled ? 'text-gray-400 cursor-not-allowed' : activeFolder === item.key ? 'bg-white/90 shadow-sm font-medium text-gray-900' : 'text-gray-800 hover:bg-white/50'}"
					disabled={item.disabled}
					onclick={() => !item.disabled && selectFolder(item.key)}
					data-testid="nav-folder-{item.key}"
				>
					<span class="w-5 h-5 flex items-center justify-center opacity-70">
						{#if item.icon === 'sent'}
							<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></svg>
						{:else if item.icon === 'trash'}
							<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /></svg>
						{:else if item.icon === 'spam'}
							<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="m4.9 4.9 14.2 14.2" /></svg>
						{:else}
							<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" /></svg>
						{/if}
					</span>
					<span class="flex-1">{item.label}</span>
				</button>
			{/each}
		</div>

		<div class="pt-4 pb-1 px-3">
			<span class="text-xs text-gray-500 uppercase tracking-wider">SmartCRM</span>
		</div>
		{#each EMAIL_NAV_SMARTCRM as item (item.key)}
			<button
				type="button"
				class="w-full flex items-center gap-2.5 pl-6 pr-3 py-1.5 rounded-xl text-sm text-left transition-colors
					{activeFolder === item.key ? 'bg-white/90 shadow-sm font-medium text-gray-900' : 'text-gray-700 hover:bg-white/50'}"
				onclick={() => selectFolder(item.key)}
				data-testid="nav-{item.key}"
			>
				<span class="flex-1">{item.label}</span>
			</button>
		{/each}
	</nav>

	{#if accounts.length > 1}
		<div class="px-3 pb-2">
			<select
				class="w-full rounded-xl bg-white/70 border border-black/5 px-2 py-1.5 text-xs text-gray-800"
				bind:value={filterAccountId}
				onchange={onAccountFilterChange}
			>
				<option value="">Все ящики</option>
				{#each accounts as a (a.id)}
					<option value={String(a.id)}>{a.username}</option>
				{/each}
			</select>
		</div>
	{/if}

	<div class="px-4 py-3 border-t border-black/5 text-xs text-gray-600">
		{#if accounts.length}
			<div class="font-medium truncate text-gray-800">{accounts[0].username}</div>
			<button type="button" class="mt-1 text-[#0066cc] hover:underline" onclick={onSettings}>Настройки</button>
		{:else}
			<button type="button" class="text-[#0066cc] hover:underline" onclick={onSettings}>Подключить почту</button>
		{/if}
	</div>
</aside>

<style>
	.email-yandex-sidebar {
		background: linear-gradient(165deg, #fff5e8 0%, #fdebd2 35%, #f9e4c8 70%, #f5dcc0 100%);
	}
</style>
