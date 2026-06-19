<script>
	import {
		approveLeadHuntQueue,
		fetchLeadHuntQueue,
		rejectLeadHuntQueue
	} from '$lib/leadHunt/leadHuntOps.js';

	let { compact = false } = $props();

	let items = $state([]);
	let loading = $state(true);
	let msg = $state('');
	let err = $state('');
	let nurtureOn = $state(false);

	async function reload() {
		loading = true;
		err = '';
		try {
			const data = await fetchLeadHuntQueue('pending');
			items = data.items || [];
		} catch (e) {
			err = e.message || 'Ошибка загрузки';
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		reload();
	});

	async function approve(id) {
		err = '';
		try {
			const r = await approveLeadHuntQueue(id, { start_nurture: nurtureOn });
			msg = nurtureOn && r.nurture?.chain_id
				? `Лид #${r.lead_id}, nurture #${r.nurture.chain_id}`
				: `Лид #${r.lead_id} в CRM`;
			await reload();
		} catch (e) {
			err = e.message;
		}
	}

	async function reject(id) {
		err = '';
		try {
			await rejectLeadHuntQueue(id);
			msg = 'Отклонено';
			await reload();
		} catch (e) {
			err = e.message;
		}
	}
</script>

<section class="rounded-xl border p-4 {compact ? 'bg-slate-900/60 border-slate-700' : 'bg-amber-950/40 border-amber-800/50'}">
	<div class="flex flex-wrap items-center justify-between gap-2 mb-3">
		<h2 class="font-semibold text-sm {compact ? 'text-white' : 'text-amber-100'}">
			🎯 Найдено агентами (Lead Hunt)
		</h2>
		<a href="/ops/lead-hunt" class="text-xs underline opacity-80">Настройки</a>
	</div>

	{#if !compact}
		<label class="flex items-center gap-2 text-xs text-amber-200/80 mb-2">
			<input type="checkbox" bind:checked={nurtureOn} />
			Запустить nurture при одобрении
		</label>
	{/if}

	{#if err}<p class="text-red-400 text-xs mb-2">{err}</p>{/if}
	{#if msg}<p class="text-green-400 text-xs mb-2">{msg}</p>{/if}

	{#if loading}
		<p class="text-xs opacity-60">Загрузка…</p>
	{:else if items.length === 0}
		<p class="text-xs opacity-60">Очередь пуста</p>
	{:else}
		<ul class="space-y-2">
			{#each items as it}
				<li class="rounded-lg border border-white/10 p-3 text-sm">
					<p class="font-medium">{it.company} · {it.score}%</p>
					<p class="text-xs opacity-70 mt-1 line-clamp-2">{it.summary || '—'}</p>
					<div class="flex gap-2 mt-2">
						<button
							type="button"
							class="text-xs px-2 py-1 rounded bg-emerald-700 text-white"
							onclick={() => approve(it.id)}
						>
							В CRM
						</button>
						<button
							type="button"
							class="text-xs px-2 py-1 rounded border border-white/20"
							onclick={() => reject(it.id)}
						>
							Отклонить
						</button>
					</div>
				</li>
			{/each}
		</ul>
	{/if}
</section>
