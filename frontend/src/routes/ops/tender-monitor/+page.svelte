<script>
	import { onMount } from 'svelte';
	import {
		emptyWatch,
		fetchTenderMonitorConfig,
		fetchTenderMonitorStatus,
		okpdFromText,
		okpdToText,
		runTenderMonitor,
		saveTenderMonitorConfig
	} from '$lib/tenders/tenderMonitorOps.js';

	let cfg = $state(null);
	let status = $state(null);
	let loading = $state(true);
	let saving = $state(false);
	let running = $state(false);
	let msg = $state('');
	let err = $state('');
	let okpdTexts = $state({});

	async function reload() {
		loading = true;
		err = '';
		try {
			cfg = await fetchTenderMonitorConfig();
			status = await fetchTenderMonitorStatus();
			okpdTexts = {};
			for (const w of cfg.watches || []) {
				okpdTexts[w.id] = okpdToText(w.okpd_codes);
			}
		} catch (e) {
			err = e.message || 'Ошибка загрузки';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		reload();
		const t = setInterval(
			() => fetchTenderMonitorStatus().then((s) => (status = s)).catch(() => {}),
			30000
		);
		return () => clearInterval(t);
	});

	async function save() {
		saving = true;
		msg = '';
		err = '';
		try {
			const payload = {
				...cfg,
				watches: (cfg.watches || []).map((w) => ({
					...w,
					okpd_codes: okpdFromText(okpdTexts[w.id] || '')
				}))
			};
			cfg = await saveTenderMonitorConfig(payload);
			msg = 'Сохранено';
			status = await fetchTenderMonitorStatus();
		} catch (e) {
			err = e.message;
		} finally {
			saving = false;
		}
	}

	async function doRun(dryRun, watchId = null) {
		running = true;
		msg = '';
		err = '';
		try {
			const report = await runTenderMonitor({ watchId, dryRun });
			msg = dryRun
				? `Dry-run: новых ${report.total_new}, в очередь ${report.total_queued}`
				: `Готово: новых ${report.total_new}, в очередь Ops ${report.total_queued}`;
			status = await fetchTenderMonitorStatus();
		} catch (e) {
			err = e.message;
		} finally {
			running = false;
		}
	}

	function addWatch() {
		const w = emptyWatch();
		cfg.watches = [...(cfg.watches || []), w];
		okpdTexts[w.id] = '';
	}

	function removeWatch(i) {
		const w = cfg.watches[i];
		cfg.watches = cfg.watches.filter((_, j) => j !== i);
		if (w?.id) {
			const next = { ...okpdTexts };
			delete next[w.id];
			okpdTexts = next;
		}
	}
</script>

<div class="max-w-4xl mx-auto p-6 space-y-6">
	<h1 class="text-2xl font-bold text-slate-800">Мониторинг тендеров (Тех. спец)</h1>
	<p class="text-slate-600 text-sm">
		Фоновый поиск по ключевым словам и ОКПД2. Новые закупки попадают в
		<a href="/ops/queue" class="text-blue-600 underline">очередь Ops</a>.
	</p>

	{#if loading}
		<p class="text-slate-500">Загрузка…</p>
	{:else if cfg}
		{#if err}<p class="text-red-600 text-sm">{err}</p>{/if}
		{#if msg}<p class="text-green-700 text-sm">{msg}</p>{/if}

		<section class="bg-white border rounded-lg p-4 space-y-3">
			<h2 class="font-semibold">Планировщик</h2>
			<label class="flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={cfg.monitor_enabled} />
				Авто-мониторинг 24/7
			</label>
			<label class="flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={cfg.notify_ops_queue} />
				Уведомлять в Ops-очередь
			</label>
			<label class="text-sm block">
				Интервал (часов):
				<input
					type="number"
					min="1"
					max="168"
					class="border rounded px-2 py-1 w-20 ml-2"
					bind:value={cfg.monitor_interval_hours}
				/>
			</label>
			{#if status}
				<p class="text-xs text-slate-500">
					Правил вкл: {status.enabled_watches} · due: {status.scheduler_due ? 'да' : 'нет'}
					{#if status.scheduler?.last_auto_at}
						· последний авто: {status.scheduler.last_auto_at}
					{/if}
				</p>
			{/if}
		</section>

		<section class="space-y-4">
			<div class="flex justify-between items-center">
				<h2 class="font-semibold">Правила мониторинга</h2>
				<button type="button" class="text-sm text-blue-600" onclick={addWatch}>+ правило</button>
			</div>
			{#each cfg.watches || [] as watch, i}
				<div class="bg-white border rounded-lg p-4 space-y-2">
					<div class="flex gap-2 items-center">
						<input type="checkbox" bind:checked={watch.enabled} />
						<input
							class="border rounded px-2 py-1 flex-1 text-sm"
							placeholder="Название"
							bind:value={watch.name}
						/>
						<button type="button" class="text-red-500 text-sm" onclick={() => removeWatch(i)}
							>удалить</button
						>
					</div>
					<input
						class="border rounded px-2 py-1 w-full text-sm"
						placeholder="Ключевые слова (через пробел)"
						bind:value={watch.keywords}
					/>
					<textarea
						class="border rounded px-2 py-1 w-full text-sm font-mono"
						rows="2"
						placeholder="ОКПД2 — по одному на строку"
						bind:value={okpdTexts[watch.id]}
					></textarea>
					<div class="flex gap-2 flex-wrap text-sm">
						<select class="border rounded px-2 py-1" bind:value={watch.law}>
							<option value="all">44+223</option>
							<option value="44">44-ФЗ</option>
							<option value="223">223-ФЗ</option>
						</select>
						<input
							class="border rounded px-2 py-1 w-24"
							placeholder="Регион"
							bind:value={watch.region}
						/>
					</div>
					<button
						type="button"
						class="text-xs text-slate-600 underline"
						disabled={running}
						onclick={() => doRun(true, watch.id)}>Dry-run этого правила</button
					>
				</div>
			{/each}
		</section>

		<div class="flex gap-3">
			<button
				type="button"
				class="bg-blue-600 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
				disabled={saving}
				onclick={save}>{saving ? '…' : 'Сохранить'}</button
			>
			<button
				type="button"
				class="border px-4 py-2 rounded text-sm disabled:opacity-50"
				disabled={running}
				onclick={() => doRun(true)}>Dry-run все</button
			>
			<button
				type="button"
				class="border border-green-600 text-green-700 px-4 py-2 rounded text-sm disabled:opacity-50"
				disabled={running}
				onclick={() => doRun(false)}>{running ? '…' : 'Запустить сейчас'}</button
			>
		</div>
	{/if}
</div>
