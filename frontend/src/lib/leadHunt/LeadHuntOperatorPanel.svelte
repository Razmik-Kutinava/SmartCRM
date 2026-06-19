<script>
	import {
		approveLeadHuntAbove,
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

	let { theme = 'ops' } = $props();
	const dark = theme === 'leadgen';

	let cfg = $state(null);
	let status = $state(null);
	let icp = $state(null);
	let candidates = $state([]);
	let notifications = $state([]);
	let loading = $state(true);
	let saving = $state(false);
	let running = $state(false);
	let bulk = $state(false);
	let msg = $state('');
	let err = $state('');

	function fmtRun(run) {
		if (!run) return '—';
		const at = run.at ? new Date(run.at).toLocaleString('ru-RU') : '';
		return `${run.trigger || 'auto'} · найдено ${run.candidates_found ?? 0} · в очередь ${run.candidates_queued ?? 0}${at ? ` · ${at}` : ''}`;
	}

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

	$effect(() => {
		reload();
	});

	async function save() {
		saving = true;
		msg = '';
		err = '';
		try {
			cfg = await saveLeadHuntConfig(cfg);
			msg = 'Настройки сохранены';
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
			msg = `Прогон: ICP v${report.icp_version}, в очередь ${report.candidates_queued || 0}`;
			await reload();
		} catch (e) {
			err = e.message;
		} finally {
			running = false;
		}
	}

	async function doApproveAll() {
		bulk = true;
		msg = '';
		err = '';
		try {
			const r = await approveLeadHuntAbove(70);
			msg = `Одобрено ${r.approved_count || 0} кандидатов (≥70%)`;
			await reload();
		} catch (e) {
			err = e.message;
		} finally {
			bulk = false;
		}
	}

	async function approve(id) {
		err = '';
		try {
			const r = await approveLeadHuntCandidate(id);
			msg = `Лид #${r.lead_id} в CRM`;
			await reload();
		} catch (e) {
			err = e.message;
		}
	}

	async function reject(id) {
		err = '';
		try {
			await rejectLeadHuntCandidate(id, 'отклонено оператором');
			msg = 'Отклонено';
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

<div class="space-y-5" data-testid="lead-hunt-operator-panel">
	{#if loading}
		<p class="text-sm opacity-60">Загрузка…</p>
	{:else if cfg}
		{#if err}<p class="text-red-400 text-sm">{err}</p>{/if}
		{#if msg}<p class="text-green-400 text-sm">{msg}</p>{/if}

		<section
			class="rounded-xl border p-4 space-y-3 {dark
				? 'bg-gray-900 border-gray-800'
				: 'bg-white border-slate-200'}"
		>
			<h2 class="font-semibold text-sm">Авто-охота</h2>
			<label class="flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={cfg.hunt_enabled} data-testid="lead-hunt-toggle-enabled" />
				Включить автопоиск
			</label>
			<div class="grid grid-cols-2 gap-3 text-sm">
				<label>
					Интервал (ч)
					<input
						type="number"
						class="border rounded px-2 py-1 w-full mt-1 {dark ? 'bg-gray-950 border-gray-700' : ''}"
						bind:value={cfg.hunt_interval_hours}
						min="1"
						max="168"
						data-testid="lead-hunt-interval"
					/>
				</label>
				<label>
					Мин. скор %
					<input
						type="number"
						class="border rounded px-2 py-1 w-full mt-1 {dark ? 'bg-gray-950 border-gray-700' : ''}"
						bind:value={cfg.min_score_threshold}
						min="0"
						max="100"
					/>
				</label>
			</div>
			<div class="flex flex-wrap gap-2">
				<button
					type="button"
					class="px-3 py-1.5 bg-indigo-600 text-white rounded text-sm disabled:opacity-50"
					disabled={saving}
					onclick={save}
					data-testid="lead-hunt-save"
				>
					{saving ? '…' : 'Сохранить'}
				</button>
				<button
					type="button"
					class="px-3 py-1.5 bg-slate-700 text-white rounded text-sm disabled:opacity-50"
					disabled={running}
					onclick={doRun}
					data-testid="lead-hunt-run-now"
				>
					{running ? '…' : 'Запустить сейчас'}
				</button>
				<button
					type="button"
					class="px-3 py-1.5 bg-emerald-700 text-white rounded text-sm disabled:opacity-50"
					disabled={bulk || candidates.length === 0}
					onclick={doApproveAll}
					data-testid="lead-hunt-approve-all-70"
				>
					{bulk ? '…' : 'Одобрить всех ≥70'}
				</button>
			</div>
		</section>

		{#if status}
			<section
				class="rounded-xl border p-4 text-sm space-y-1 {dark
					? 'bg-gray-900/60 border-gray-800 text-gray-300'
					: 'bg-slate-50 border-slate-200'}"
				data-testid="lead-hunt-last-run"
			>
				<p>
					Статус: <strong>{status.hunt_enabled ? 'вкл' : 'выкл'}</strong>
					· интервал {status.hunt_interval_hours}ч
					· в очереди <strong>{status.pending_candidates ?? 0}</strong>
				</p>
				<p class="opacity-80">Последний прогон: {fmtRun(status.last_run)}</p>
				{#if status.scheduler?.last_auto_at}
					<p class="text-xs opacity-60">Авто: {status.scheduler.last_auto_at}</p>
				{/if}
			</section>
		{/if}

		<section
			class="rounded-xl border p-4 {dark ? 'bg-gray-900 border-gray-800' : 'bg-white border-slate-200'}"
			data-testid="lead-hunt-queue-section"
		>
			<div class="flex justify-between items-center mb-3">
				<h2 class="font-semibold text-sm">Очередь кандидатов</h2>
				<span class="text-xs opacity-60">{candidates.length} pending</span>
			</div>
			{#if candidates.length === 0}
				<p class="text-sm opacity-60">Очередь пуста</p>
			{:else}
				<ul class="space-y-2">
					{#each candidates as c}
						<li
							class="border rounded p-3 flex flex-wrap justify-between gap-2 items-start {dark
								? 'border-gray-700'
								: 'border-slate-200'}"
						>
							<div>
								<p class="font-medium">{companyLabel(c)}</p>
								<p class="text-xs opacity-70">
									Скор {c.score}% · ИНН {c.inn || '—'}
									{#if c.summary}· {c.summary.slice(0, 80)}{/if}
								</p>
							</div>
							<div class="flex gap-2">
								<button
									type="button"
									class="text-xs px-2 py-1 bg-emerald-700 text-white rounded"
									onclick={() => approve(c.id)}
								>
									В CRM
								</button>
								<button
									type="button"
									class="text-xs px-2 py-1 border rounded opacity-80"
									onclick={() => reject(c.id)}
								>
									Отклонить
								</button>
							</div>
						</li>
					{/each}
				</ul>
			{/if}
		</section>

		{#if notifications.length > 0}
			<section class="rounded-xl border border-amber-700/50 bg-amber-950/30 p-4">
				<div class="flex justify-between items-center mb-2">
					<h2 class="font-semibold text-sm">Уведомления</h2>
					<button type="button" class="text-xs underline" onclick={readAllNotif}>Прочитать все</button>
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
