<script>
	import { onMount } from 'svelte';
	import {
		approveLeadHuntCandidate,
		companyLabel,
		fetchLeadHuntCandidates,
		fetchLeadHuntConfig,
		fetchLeadHuntIcp,
		fetchLeadHuntNotifications,
		fetchLeadHuntStatus,
		markLeadHuntNotificationsRead,
		rejectLeadHuntCandidate,
		refreshLeadHuntIcp,
		runLeadHunt,
		saveLeadHuntConfig
	} from '$lib/leadHunt/leadHuntOps.js';

	let cfg = $state(null);
	let status = $state(null);
	let icp = $state(null);
	let candidates = $state([]);
	let notifications = $state([]);
	let loading = $state(true);
	let saving = $state(false);
	let running = $state(false);
	let msg = $state('');
	let err = $state('');

	async function reload() {
		loading = true;
		err = '';
		try {
			cfg = await fetchLeadHuntConfig();
			status = await fetchLeadHuntStatus();
			icp = await fetchLeadHuntIcp();
			const c = await fetchLeadHuntCandidates('pending');
			candidates = c.items || [];
			const n = await fetchLeadHuntNotifications(true);
			notifications = n.items || [];
		} catch (e) {
			err = e.message || 'Ошибка загрузки';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		reload();
		const t = setInterval(
			() => fetchLeadHuntStatus().then((s) => (status = s)).catch(() => {}),
			30000
		);
		return () => clearInterval(t);
	});

	async function save() {
		saving = true;
		msg = '';
		err = '';
		try {
			cfg = await saveLeadHuntConfig(cfg);
			msg = 'Сохранено';
			status = await fetchLeadHuntStatus();
		} catch (e) {
			err = e.message;
		} finally {
			saving = false;
		}
	}

	async function doRun() {
		running = true;
		msg = '';
		err = '';
		try {
			const report = await runLeadHunt();
			msg = `Прогон: ICP v${report.icp_version}, в очередь ${report.candidates_queued || 0}, авто ${report.candidates_approved || 0}`;
			await reload();
		} catch (e) {
			err = e.message;
		} finally {
			running = false;
		}
	}

	async function doRefreshIcp() {
		running = true;
		err = '';
		try {
			await refreshLeadHuntIcp();
			msg = 'ICP обновлён';
			icp = await fetchLeadHuntIcp();
		} catch (e) {
			err = e.message;
		} finally {
			running = false;
		}
	}

	async function approve(id) {
		err = '';
		try {
			const r = await approveLeadHuntCandidate(id);
			msg = `Лид #${r.lead_id} создан`;
			await reload();
		} catch (e) {
			err = e.message;
		}
	}

	async function reject(id) {
		err = '';
		try {
			await rejectLeadHuntCandidate(id, 'отклонено оператором');
			msg = 'Кандидат отклонён';
			await reload();
		} catch (e) {
			err = e.message;
		}
	}

	async function readAllNotif() {
		await markLeadHuntNotificationsRead(true);
		notifications = [];
	}
</script>

<div class="max-w-4xl mx-auto p-6 space-y-6">
	<h1 class="text-2xl font-bold text-slate-800">Автопоиск лидов (Lead Hunt)</h1>
	<p class="text-slate-600 text-sm">
		Фоновый цикл: ICP из выигранных сделок → поиск по портрету → очередь на одобрение → CRM.
		<a href="/ops/queue" class="text-blue-600 underline">Очередь Ops</a>
	</p>

	{#if loading}
		<p class="text-slate-500">Загрузка…</p>
	{:else if cfg}
		{#if err}<p class="text-red-600 text-sm">{err}</p>{/if}
		{#if msg}<p class="text-green-700 text-sm">{msg}</p>{/if}

		<section class="bg-white border rounded-lg p-4 space-y-3">
			<h2 class="font-semibold">Планировщик</h2>
			<label class="flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={cfg.hunt_enabled} />
				Включить автопоиск
			</label>
			<div class="grid grid-cols-2 gap-3 text-sm">
				<label>
					Интервал (ч)
					<input type="number" class="border rounded px-2 py-1 w-full mt-1" bind:value={cfg.hunt_interval_hours} min="1" max="168" />
				</label>
				<label>
					Кандидатов за прогон
					<input type="number" class="border rounded px-2 py-1 w-full mt-1" bind:value={cfg.candidates_per_run} min="1" max="20" />
				</label>
				<label>
					Мин. скор %
					<input type="number" class="border rounded px-2 py-1 w-full mt-1" bind:value={cfg.min_score_threshold} min="0" max="100" />
				</label>
				<label>
					Won-лидов в ICP
					<input type="number" class="border rounded px-2 py-1 w-full mt-1" bind:value={cfg.won_sample_limit} min="1" max="200" />
				</label>
			</div>
			<label class="flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={cfg.notify_ops_queue} />
				Уведомления в Ops-очередь
			</label>
			<label class="flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={cfg.autosave_above_threshold} />
				Сразу в CRM (без очереди)
			</label>
			<div class="flex gap-2">
				<button class="px-3 py-1.5 bg-indigo-600 text-white rounded text-sm disabled:opacity-50" disabled={saving} onclick={save}>
					{saving ? '…' : 'Сохранить'}
				</button>
				<button class="px-3 py-1.5 bg-slate-700 text-white rounded text-sm disabled:opacity-50" disabled={running} onclick={doRun}>
					{running ? '…' : 'Запустить сейчас'}
				</button>
				<button class="px-3 py-1.5 border rounded text-sm disabled:opacity-50" disabled={running} onclick={doRefreshIcp}>
					Обновить ICP
				</button>
			</div>
		</section>

		{#if status}
			<section class="bg-slate-50 border rounded-lg p-4 text-sm space-y-1">
				<p>Фаза: <strong>{status.phase}</strong> · ICP v{status.icp_version ?? '—'} · в очереди: {status.pending_candidates ?? 0}</p>
				<p>Непрочитанных уведомлений: {status.notifications_unread ?? 0}</p>
				{#if status.last_run}
					<p class="text-slate-600">
						Последний прогон: {status.last_run.trigger}, кандидатов {status.last_run.candidates_found ?? 0}
					</p>
				{/if}
			</section>
		{/if}

		{#if icp?.current}
			<section class="bg-white border rounded-lg p-4">
				<h2 class="font-semibold mb-2">Текущий ICP</h2>
				<p class="text-sm text-slate-700">{icp.current.portrait_text || icp.current.base_portrait}</p>
				{#if icp.current.city || icp.current.industry}
					<p class="text-xs text-slate-500 mt-1">{icp.current.city} · {icp.current.industry}</p>
				{/if}
			</section>
		{/if}

		<section class="bg-white border rounded-lg p-4">
			<div class="flex justify-between items-center mb-3">
				<h2 class="font-semibold">Кандидаты (pending)</h2>
				<span class="text-sm text-slate-500">{candidates.length}</span>
			</div>
			{#if candidates.length === 0}
				<p class="text-sm text-slate-500">Очередь пуста</p>
			{:else}
				<ul class="space-y-2">
					{#each candidates as c}
						<li class="border rounded p-3 flex flex-wrap justify-between gap-2 items-start">
							<div>
								<p class="font-medium">{companyLabel(c)}</p>
								<p class="text-xs text-slate-500">Скор {c.score}% · ИНН {c.company?.inn || '—'}</p>
							</div>
							<div class="flex gap-2">
								<button class="text-sm px-2 py-1 bg-emerald-600 text-white rounded" onclick={() => approve(c.id)}>В CRM</button>
								<button class="text-sm px-2 py-1 border rounded" onclick={() => reject(c.id)}>Отклонить</button>
							</div>
						</li>
					{/each}
				</ul>
			{/if}
		</section>

		{#if notifications.length > 0}
			<section class="bg-amber-50 border border-amber-200 rounded-lg p-4">
				<div class="flex justify-between items-center mb-2">
					<h2 class="font-semibold text-sm">Новые уведомления</h2>
					<button class="text-xs underline" onclick={readAllNotif}>Прочитать все</button>
				</div>
				<ul class="text-sm space-y-1">
					{#each notifications as n}
						<li>{n.title}</li>
					{/each}
				</ul>
			</section>
		{/if}
	{/if}
</div>
