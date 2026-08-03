<script>
	import { submitRawInbox, rawInboxFromLead } from '../lib/leads/rawInbox.js';

	let {
		lead = null,
		onApplied = async (_lead) => {}
	} = $props();

	let text = $state('');
	let busy = $state(false);
	let error = $state('');
	let lastSummary = $state('');
	let open = $state(false);

	const inbox = $derived(rawInboxFromLead(lead));
	const chunkCount = $derived(inbox.chunks.length);

	async function submit() {
		error = '';
		lastSummary = '';
		const payload = text.trim();
		if (!payload || !lead?.id) {
			error = 'Вставьте текст';
			return;
		}
		busy = true;
		try {
			const out = await submitRawInbox(lead.id, payload);
			lastSummary = out.summary || '';
			text = '';
			open = true;
			if (out.lead) await onApplied(out.lead);
		} catch (e) {
			error = e?.message || String(e);
		} finally {
			busy = false;
		}
	}
</script>

<div class="rounded-xl border border-gray-800 bg-gray-950/60 p-3 space-y-2" data-testid="lead-raw-inbox">
	<button
		type="button"
		class="w-full flex items-center justify-between text-left"
		onclick={() => (open = !open)}
		data-testid="lead-raw-inbox-toggle"
	>
		<span class="text-xs font-medium text-gray-300">Сырьё → поля</span>
		<span class="text-[10px] text-gray-500">
			{chunkCount ? `${chunkCount} куск.` : 'пусто'} · {open ? '▾' : '▸'}
		</span>
	</button>

	{#if open}
		<textarea
			class="w-full min-h-[88px] rounded-lg bg-gray-900 border border-gray-800 text-sm text-gray-200 p-2 placeholder:text-gray-600"
			placeholder="Вставь переписку, визитку, выгрузку… Разберём телефоны, ИНН, контакты."
			bind:value={text}
			disabled={busy}
			data-testid="lead-raw-inbox-input"
		></textarea>
		<div class="flex items-center gap-2">
			<button
				type="button"
				class="px-3 py-1.5 text-xs rounded-lg bg-indigo-700 text-white disabled:opacity-50"
				onclick={submit}
				disabled={busy || !text.trim()}
				data-testid="lead-raw-inbox-submit"
			>
				{busy ? 'Разбор…' : 'Разобрать и заполнить'}
			</button>
			{#if error}
				<span class="text-xs text-red-400" data-testid="lead-raw-inbox-error">{error}</span>
			{/if}
		</div>
		{#if lastSummary}
			<pre class="text-[11px] text-emerald-300/90 whitespace-pre-wrap bg-gray-900/80 rounded-lg p-2 border border-emerald-900/40" data-testid="lead-raw-inbox-summary">{lastSummary}</pre>
		{:else if inbox.brief}
			<pre class="text-[11px] text-gray-400 whitespace-pre-wrap bg-gray-900/50 rounded-lg p-2 max-h-28 overflow-y-auto" data-testid="lead-raw-inbox-brief">{inbox.brief}</pre>
		{/if}
		{#if chunkCount}
			<details class="text-[10px] text-gray-500">
				<summary class="cursor-pointer hover:text-gray-300">Куски ({chunkCount})</summary>
				<ul class="mt-1 space-y-1 max-h-32 overflow-y-auto">
					{#each inbox.chunks as c (c.id || c.created_at)}
						<li class="border border-gray-800 rounded px-2 py-1 truncate" title={c.preview || ''}>
							{(c.preview || '').slice(0, 120) || `${c.chars || 0} симв.`}
						</li>
					{/each}
				</ul>
			</details>
		{/if}
	{/if}
</div>
