<script>
	import { CONTACT_ROLE_OPTIONS } from '$lib/leads/leadContacts.js';

	/** @type {{ contacts: Array<Record<string, unknown>> }} */
	let { contacts = [] } = $props();

	/** Длинный список сворачиваем — иначе карточка уезжает вниз на 10 контактах. */
	const VISIBLE_LIMIT = 4;
	let expanded = $state(false);
	const hiddenCount = $derived(Math.max(0, contacts.length - VISIBLE_LIMIT));
	const visible = $derived(expanded ? contacts : contacts.slice(0, VISIBLE_LIMIT));

	function roleLabel(role) {
		return CONTACT_ROLE_OPTIONS.find((o) => o.value === role)?.label || role || 'Другое';
	}

	function channelList(values) {
		if (!Array.isArray(values)) return [];
		return values.map((v) => String(v || '').trim()).filter(Boolean);
	}
</script>

<div class="space-y-2" data-testid="lead-contacts-readonly-list">
	<div class="flex items-center justify-between gap-2">
		<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">
			Контакты на лиде
			{#if contacts.length > 0}
				<span class="text-gray-600 font-normal">({contacts.length})</span>
			{/if}
		</div>
	</div>

	{#if contacts.length === 0}
		<p class="text-xs text-gray-600 italic rounded-lg border border-dashed border-gray-800 px-3 py-2">
			Контактов нет — синк из Битрикс или добавьте ниже.
		</p>
	{:else}
		<ul class="space-y-2">
			{#each visible as c, idx (c.id || idx)}
				{@const phones = channelList(c.phones)}
				{@const emails = channelList(c.emails)}
				<li
					class="rounded-lg border px-3 py-2.5 text-sm
						{c.role === 'lpr' ? 'border-emerald-800/70 bg-emerald-950/15' : 'border-gray-800 bg-gray-950/40'}"
				>
					<div class="flex flex-wrap items-center gap-x-2 gap-y-1">
						<span class="font-medium text-gray-100">{c.name || 'Без имени'}</span>
						<span class="text-[10px] px-1.5 py-px rounded bg-gray-800 text-gray-400">{roleLabel(c.role)}</span>
					</div>
					{#if c.position}
						<div class="text-xs text-gray-500 mt-0.5">{c.position}</div>
					{/if}
					{#if phones.length}
						<div class="text-xs text-gray-400 mt-1">
							<span class="text-gray-600">Тел.:</span>
							{phones.join(' · ')}
						</div>
					{/if}
					{#if emails.length}
						<div class="text-xs text-gray-400 mt-0.5">
							<span class="text-gray-600">Email:</span>
							{emails.join(' · ')}
						</div>
					{/if}
				</li>
			{/each}
		</ul>
		{#if hiddenCount > 0 || expanded}
			<button
				type="button"
				class="w-full text-[11px] py-1 rounded border border-gray-800 text-gray-400 hover:text-gray-200 hover:border-gray-700"
				onclick={() => (expanded = !expanded)}
				data-testid="lead-contacts-readonly-toggle"
			>
				{expanded ? 'Свернуть' : `Показать все (${contacts.length})`}
			</button>
		{/if}
	{/if}
</div>
