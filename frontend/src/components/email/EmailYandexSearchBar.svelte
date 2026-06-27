<script>
	import {
		EMAIL_FILTER_CHIPS,
		EMAIL_FOLDER_FILTER_OPTIONS,
		createEmptySearchFilters,
	} from '$lib/email/emailListLogic.js';

	let {
		searchQuery = $bindable(''),
		searchFilters = $bindable(createEmptySearchFilters()),
		onSearch = () => {},
	} = $props();

	let openPanel = $state(null);

	function toggleChip(key) {
		if (key === 'attachments') {
			searchFilters = { ...searchFilters, attachments: !searchFilters.attachments };
			onSearch();
			return;
		}
		openPanel = openPanel === key ? null : key;
	}

	function applyPanel() {
		openPanel = null;
		onSearch();
	}

	function clearFilters() {
		searchFilters = createEmptySearchFilters();
		searchQuery = '';
		openPanel = null;
		onSearch();
	}

	function hasActiveFilters() {
		return (
			searchFilters.attachments ||
			searchFilters.dateFrom ||
			searchFilters.dateTo ||
			searchFilters.folderKey ||
			searchFilters.from ||
			searchFilters.to ||
			searchFilters.unreadOnly
		);
	}
</script>

<div class="px-5 pt-4 pb-2 flex-shrink-0 bg-white border-b border-gray-100" data-testid="email-yandex-search">
	<div class="flex items-center gap-3">
		<div class="relative flex-1">
			<input
				bind:value={searchQuery}
				onkeydown={(e) => e.key === 'Enter' && onSearch()}
				class="w-full rounded-full bg-gray-100 border-0 pl-4 pr-10 py-2.5 text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#ffdb4d]/80"
				placeholder="Поиск"
				data-testid="email-search-input"
			/>
			{#if searchQuery}
				<button
					type="button"
					class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700"
					onclick={() => { searchQuery = ''; onSearch(); }}
					aria-label="Очистить"
				>×</button>
			{/if}
		</div>
		<button
			type="button"
			class="text-sm font-medium text-gray-900 hover:text-[#0066cc] px-1"
			onclick={onSearch}
			data-testid="email-search-submit"
		>Найти</button>
	</div>

	<div class="flex flex-wrap items-center gap-2 mt-3 relative">
		{#each EMAIL_FILTER_CHIPS as chip (chip.key)}
			<button
				type="button"
				class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors
					{(chip.key === 'attachments' && searchFilters.attachments) || openPanel === chip.key
						? 'bg-gray-900 text-white'
						: 'bg-gray-100 text-gray-800 hover:bg-gray-200'}"
				onclick={() => toggleChip(chip.key)}
				data-testid="filter-chip-{chip.key}"
			>
				{#if chip.icon === 'attach'}
					<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" /></svg>
				{:else if chip.icon === 'calendar'}
					<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="4" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></svg>
				{:else if chip.icon === 'folder'}
					<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" /></svg>
				{:else if chip.icon === 'from' || chip.icon === 'to'}
					<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
				{/if}
				{chip.label}
			</button>
		{/each}
		{#if hasActiveFilters() || searchQuery}
			<button type="button" class="text-xs text-[#0066cc] hover:underline ml-1" onclick={clearFilters}>Сбросить</button>
		{/if}
	</div>

	{#if openPanel === 'date'}
		<div class="mt-3 p-3 rounded-xl bg-gray-50 border border-gray-200 flex flex-wrap gap-3 items-end">
			<label class="text-xs text-gray-600">С <input type="date" bind:value={searchFilters.dateFrom} class="block mt-1 rounded-lg border border-gray-300 px-2 py-1 text-sm" /></label>
			<label class="text-xs text-gray-600">По <input type="date" bind:value={searchFilters.dateTo} class="block mt-1 rounded-lg border border-gray-300 px-2 py-1 text-sm" /></label>
			<button type="button" class="px-3 py-1.5 rounded-lg bg-gray-900 text-white text-xs" onclick={applyPanel}>Применить</button>
		</div>
	{:else if openPanel === 'folder'}
		<div class="mt-3 p-3 rounded-xl bg-gray-50 border border-gray-200">
			<select bind:value={searchFilters.folderKey} class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" onchange={applyPanel}>
				{#each EMAIL_FOLDER_FILTER_OPTIONS as opt (opt.key)}
					<option value={opt.key}>{opt.label}</option>
				{/each}
			</select>
		</div>
	{:else if openPanel === 'from'}
		<div class="mt-3 p-3 rounded-xl bg-gray-50 border border-gray-200 flex gap-2">
			<input bind:value={searchFilters.from} placeholder="email или имя" class="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
			<button type="button" class="px-3 py-1.5 rounded-lg bg-gray-900 text-white text-xs" onclick={applyPanel}>Применить</button>
		</div>
	{:else if openPanel === 'to'}
		<div class="mt-3 p-3 rounded-xl bg-gray-50 border border-gray-200 flex gap-2">
			<input bind:value={searchFilters.to} placeholder="email получателя" class="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
			<button type="button" class="px-3 py-1.5 rounded-lg bg-gray-900 text-white text-xs" onclick={applyPanel}>Применить</button>
		</div>
	{:else if openPanel === 'more'}
		<div class="mt-3 p-3 rounded-xl bg-gray-50 border border-gray-200 space-y-2">
			<label class="flex items-center gap-2 text-sm text-gray-700">
				<input type="checkbox" bind:checked={searchFilters.unreadOnly} class="rounded" disabled title="Скоро: нужен is_read в API" />
				Только непрочитанные <span class="text-xs text-gray-400">(скоро)</span>
			</label>
			<button type="button" class="px-3 py-1.5 rounded-lg bg-gray-900 text-white text-xs" onclick={applyPanel}>Применить</button>
		</div>
	{/if}
</div>
