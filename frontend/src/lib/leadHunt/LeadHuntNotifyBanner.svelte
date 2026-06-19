<script>
	import { onMount } from 'svelte';
	import {
		fetchLeadHuntNotifications,
		markLeadHuntNotificationsRead
	} from '$lib/leadHunt/leadHuntOps.js';

	let { compact = false } = $props();

	let unread = $state(0);
	let latest = $state(null);
	let dismissed = $state(false);

	async function poll() {
		try {
			const data = await fetchLeadHuntNotifications(true);
			unread = data.unread ?? (data.items || []).length;
			latest = (data.items || [])[0] || null;
			if (unread > 0) dismissed = false;
		} catch {
			unread = 0;
			latest = null;
		}
	}

	async function markRead() {
		await markLeadHuntNotificationsRead(true);
		unread = 0;
		latest = null;
		dismissed = true;
	}

	onMount(() => {
		poll();
		const t = setInterval(poll, 20000);
		return () => clearInterval(t);
	});
</script>

{#if unread > 0 && !dismissed}
	<div
		class="mb-3 rounded-lg border px-4 py-3 flex flex-wrap items-center justify-between gap-2
			{compact
			? 'bg-amber-950/50 border-amber-700/60 text-amber-100'
			: 'bg-amber-900/40 border-amber-600/50 text-amber-50'}"
		role="status"
		data-testid="lead-hunt-notify-banner"
	>
		<div class="text-sm">
			<span class="font-medium">🎯 Lead Hunt:</span>
			{unread} новых кандидатов
			{#if latest}
				<span class="opacity-80">· {latest.title}</span>
			{/if}
		</div>
		<div class="flex gap-2">
			<a href="/ops/lead-hunt" class="text-xs underline opacity-90">Открыть</a>
			<button type="button" class="text-xs px-2 py-0.5 rounded bg-amber-800/80" onclick={markRead}>
				Прочитано
			</button>
			<button type="button" class="text-xs opacity-60" onclick={() => (dismissed = true)}>✕</button>
		</div>
	</div>
{/if}
