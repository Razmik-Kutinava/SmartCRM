<script>
	import { CONTACT_ROLE_OPTIONS, isLprContactComplete } from '$lib/leads/leadContacts.js';

	/**
	 * @type {{
	 *   contacts: Array<Record<string, string>>,
	 *   onChange: (contacts: Array<Record<string, string>>) => void,
	 *   onSave: () => void,
	 *   saving?: boolean,
	 * }}
	 */
	let { contacts, onChange, onSave, saving = false } = $props();

	/** Длинный список форм сворачиваем — иначе до кнопки сохранения не долистать. */
	const VISIBLE_LIMIT = 4;
	let expanded = $state(false);
	const hiddenCount = $derived(Math.max(0, contacts.length - VISIBLE_LIMIT));
	const visible = $derived(expanded ? contacts : contacts.slice(0, VISIBLE_LIMIT));

	function updateRow(idx, field, value) {
		const next = contacts.map((c, i) => (i === idx ? { ...c, [field]: value } : c));
		onChange(next);
	}

	function newContactId() {
		// crypto.randomUUID есть только в secure context (https / localhost);
		// по сети через IP остаётся фолбэк, поэтому к времени добавляем случайный хвост.
		return (
			globalThis.crypto?.randomUUID?.() ||
			`c${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
		);
	}

	function addContact(role = 'other') {
		// Новая форма всегда в конце — если список свёрнут, раскрываем, иначе её не видно.
		expanded = true;
		onChange([
			...contacts,
			{
				id: newContactId(),
				name: '',
				role,
				position: '',
				phonesText: '',
				emailsText: '',
				messengersText: '',
			},
		]);
	}

	function removeContact(idx) {
		onChange(contacts.filter((_, i) => i !== idx));
	}

	function markLpr(idx) {
		const next = contacts.map((c, i) => ({
			...c,
			role: i === idx ? 'lpr' : c.role === 'lpr' ? 'other' : c.role,
		}));
		onChange(next);
	}
</script>

<div class="space-y-3" data-testid="lead-contacts-panel">
	<div class="flex items-center justify-between gap-2">
		<div>
			<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Контакты</div>
			<p class="text-[10px] text-gray-600 mt-0.5">ЛПР с именем, должностью и каналом связи закрывает шаг квалификации.</p>
		</div>
		<button
			type="button"
			class="text-[11px] px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 shrink-0"
			onclick={() => addContact('other')}
		>+ контакт</button>
	</div>

	{#if contacts.length === 0}
		<div class="rounded-lg border border-dashed border-gray-700 p-3 text-xs text-gray-500">
			Нет контактов.
			<button type="button" class="text-indigo-400 hover:underline ml-1" onclick={() => addContact('lpr')}>Добавить ЛПР</button>
		</div>
	{:else}
		{#each visible as row, idx (row.id)}
			{@const lprDone = isLprContactComplete(row)}
			<div
				class="rounded-lg border p-3 space-y-2 text-sm
					{row.role === 'lpr' && lprDone ? 'border-emerald-800/80 bg-emerald-950/20' : 'border-gray-800 bg-gray-950/40'}"
			>
				<div class="flex items-center justify-between gap-2">
					<select
						value={row.role}
						onchange={(e) => updateRow(idx, 'role', e.currentTarget.value)}
						class="text-xs bg-gray-900 border border-gray-700 rounded px-2 py-1 text-gray-200"
					>
						{#each CONTACT_ROLE_OPTIONS as opt}
							<option value={opt.value}>{opt.label}</option>
						{/each}
					</select>
					<div class="flex items-center gap-2">
						{#if row.role === 'lpr' && lprDone}
							<span class="text-[10px] text-emerald-400 font-medium">ЛПР ✓</span>
						{:else if row.role !== 'lpr'}
							<button type="button" class="text-[10px] text-indigo-400 hover:underline" onclick={() => markLpr(idx)}>→ ЛПР</button>
						{/if}
						<button type="button" class="text-[10px] text-gray-500 hover:text-red-400" onclick={() => removeContact(idx)} aria-label="Удалить">✕</button>
					</div>
				</div>
				<label class="block">
					<span class="text-gray-500 text-xs">ФИО</span>
					<input
						value={row.name}
						oninput={(e) => updateRow(idx, 'name', e.currentTarget.value)}
						class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
					/>
				</label>
				<label class="block">
					<span class="text-gray-500 text-xs">Должность</span>
					<input
						value={row.position}
						oninput={(e) => updateRow(idx, 'position', e.currentTarget.value)}
						class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
					/>
				</label>
				<label class="block">
					<span class="text-gray-500 text-xs">Телефоны (по строке)</span>
					<textarea
						value={row.phonesText}
						oninput={(e) => updateRow(idx, 'phonesText', e.currentTarget.value)}
						rows="2"
						class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-xs resize-y font-mono"
					></textarea>
				</label>
				<label class="block">
					<span class="text-gray-500 text-xs">Email (по строке)</span>
					<textarea
						value={row.emailsText}
						oninput={(e) => updateRow(idx, 'emailsText', e.currentTarget.value)}
						rows="2"
						class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-xs resize-y font-mono"
					></textarea>
				</label>
				<label class="block">
					<span class="text-gray-500 text-xs">Мессенджеры (Telegram, WhatsApp…)</span>
					<textarea
						value={row.messengersText}
						oninput={(e) => updateRow(idx, 'messengersText', e.currentTarget.value)}
						rows="2"
						placeholder="telegram:@user"
						class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-xs resize-y"
					></textarea>
				</label>
			</div>
		{/each}
		{#if hiddenCount > 0 || expanded}
			<button
				type="button"
				class="w-full text-[11px] py-1 rounded border border-gray-800 text-gray-400 hover:text-gray-200 hover:border-gray-700"
				onclick={() => (expanded = !expanded)}
				data-testid="lead-contacts-panel-toggle"
			>
				{expanded ? 'Свернуть' : `Показать все (${contacts.length})`}
			</button>
		{/if}
	{/if}

	<button
		type="button"
		disabled={saving}
		onclick={onSave}
		class="w-full py-1.5 rounded-lg text-xs font-medium bg-cyan-900/50 hover:bg-cyan-800/60 text-cyan-100 disabled:opacity-50"
	>
		{saving ? 'Сохранение…' : 'Сохранить контакты'}
	</button>
</div>
