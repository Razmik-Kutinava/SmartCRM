<script>
	import { onMount } from 'svelte';
	import {
		docUrlsFromText,
		docUrlsToText,
		emptyVendor,
		fetchVendorCrawlConfig,
		fetchVendorCrawlStatus,
		runVendorCrawl,
		saveVendorCrawlConfig
	} from '$lib/ops/vendorCrawlOps.js';

	let cfg = $state(null);
	let status = $state(null);
	let loading = $state(true);
	let saving = $state(false);
	let running = $state(false);
	let msg = $state('');
	let err = $state('');

	async function reload() {
		loading = true;
		err = '';
		try {
			cfg = await fetchVendorCrawlConfig();
			status = await fetchVendorCrawlStatus();
		} catch (e) {
			err = e.message || 'Ошибка загрузки';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		reload();
		const t = setInterval(() => fetchVendorCrawlStatus().then((s) => (status = s)).catch(() => {}), 30000);
		return () => clearInterval(t);
	});

	async function save() {
		saving = true;
		msg = '';
		err = '';
		try {
			cfg = await saveVendorCrawlConfig(cfg);
			msg = 'Сохранено';
			status = await fetchVendorCrawlStatus();
		} catch (e) {
			err = e.message;
		} finally {
			saving = false;
		}
	}

	async function doRun(dryRun, vendorId = null) {
		running = true;
		msg = '';
		err = '';
		try {
			const report = await runVendorCrawl({ vendorId, dryRun });
			const st = report.stats || {};
			msg = dryRun
				? `Dry-run: ${report.total_chunks} чанков (HTML ${st.pages_html_ok || 0}, PDF ${st.pages_pdf_ok || 0}, отбр. качество ${st.quality_rejected || 0})`
				: `Готово: ${report.total_chunks} чанков (HTML ${st.pages_html_ok || 0}, PDF ${st.pages_pdf_ok || 0})`;
			status = await fetchVendorCrawlStatus();
		} catch (e) {
			err = e.message;
		} finally {
			running = false;
		}
	}

	function addVendor() {
		cfg.vendors = [...(cfg.vendors || []), emptyVendor()];
	}

	function removeVendor(i) {
		cfg.vendors = cfg.vendors.filter((_, j) => j !== i);
	}
</script>

<svelte:head><title>Краулинг вендоров · Ops</title></svelte:head>

<div class="p-6 max-w-4xl space-y-6 text-gray-200">
	<div>
		<h2 class="text-xl font-semibold text-white">Краулинг вендоров → RAG тех. спеца</h2>
		<p class="text-sm text-gray-400 mt-1">
			Сайты вендоров в базу знаний <code class="text-indigo-300">tech_specialist</code>. Фон: проверка раз в час, прогон по интервалу.
		</p>
	</div>

	{#if loading}
		<p class="text-gray-500">Загрузка…</p>
	{:else if !cfg}
		<p class="text-red-400">{err || 'Нет конфига'}</p>
	{:else}
		{#if msg}<p class="text-emerald-400 text-sm">{msg}</p>{/if}
		{#if err}<p class="text-red-400 text-sm">{err}</p>{/if}

		<section class="bg-gray-900 border border-gray-800 rounded-lg p-4 space-y-3">
			<h3 class="font-medium text-white">Автозапуск</h3>
			<label class="flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={cfg.auto_crawl_enabled} />
				Включить фоновый краулинг (enabled-вендоры)
			</label>
			<label class="block text-sm">
				Интервал (часов)
				<input
					type="number"
					min="1"
					max="720"
					bind:value={cfg.auto_crawl_interval_hours}
					class="mt-1 w-32 px-2 py-1 rounded bg-gray-800 border border-gray-700"
				/>
			</label>
			{#if status}
				<p class="text-xs text-gray-500">
					Включено вендоров: {status.enabled_vendors} ·
					{#if status.scheduler?.last_auto_at}
						Последний авто: {status.scheduler.last_auto_at}
						({status.scheduler.last_auto_ok ? 'OK' : 'fail'})
					{:else}
						Авто ещё не запускался
					{/if}
				</p>
			{/if}
		</section>

		<section class="space-y-3">
			<div class="flex justify-between items-center">
				<h3 class="font-medium text-white">Вендоры</h3>
				<button type="button" class="text-sm text-indigo-400 hover:text-indigo-300" onclick={addVendor}>
					+ Добавить
				</button>
			</div>
			{#each cfg.vendors as v, i}
				<div class="bg-gray-900 border border-gray-800 rounded-lg p-4 space-y-2" data-testid="vendor-row-{i}">
					<div class="flex flex-wrap gap-3 items-center">
						<label class="flex items-center gap-2 text-sm">
							<input type="checkbox" bind:checked={v.enabled} />
							Вкл
						</label>
						<input
							placeholder="id"
							bind:value={v.id}
							class="px-2 py-1 rounded bg-gray-800 border border-gray-700 text-sm w-28"
						/>
						<input
							placeholder="Название"
							bind:value={v.name}
							class="flex-1 min-w-[120px] px-2 py-1 rounded bg-gray-800 border border-gray-700 text-sm"
						/>
						<button
							type="button"
							class="text-xs text-red-400"
							onclick={() => removeVendor(i)}
						>Удалить</button>
					</div>
					<input
						placeholder="Главная https://..."
						bind:value={v.seed_url}
						class="w-full px-2 py-1 rounded bg-gray-800 border border-gray-700 text-sm"
					/>
					<label class="block text-xs text-gray-400">
						Ссылки на доки / продукты (по одной на строку)
						<textarea
							rows="3"
							class="mt-1 w-full px-2 py-1 rounded bg-gray-800 border border-gray-700 text-sm font-mono"
							value={docUrlsToText(v.doc_urls)}
							oninput={(e) => {
								v.doc_urls = docUrlsFromText(e.currentTarget.value);
							}}
						></textarea>
					</label>
					<div class="flex flex-wrap gap-4 text-sm items-center">
						<label>HTML стр. <input type="number" min="0" max="200" bind:value={v.max_pages} class="w-16 ml-1 px-1 rounded bg-gray-800 border border-gray-700" /></label>
						<label>PDF лимит <input type="number" min="0" max="50" bind:value={v.max_pdf_pages} class="w-14 ml-1 px-1 rounded bg-gray-800 border border-gray-700" /></label>
						<label>глубина <input type="number" min="0" max="4" bind:value={v.max_depth} class="w-12 ml-1 px-1 rounded bg-gray-800 border border-gray-700" /></label>
						<label class="flex items-center gap-1 text-xs">
							<input type="checkbox" bind:checked={v.use_sitemap} />
							sitemap
						</label>
						<label class="flex items-center gap-1 text-xs">
							<input type="checkbox" bind:checked={v.search_pdfs} />
							поиск PDF (site:домен)
						</label>
						<label class="flex items-center gap-1 text-xs" title="Chromium: PDF за JS-кнопками на SPA">
							<input type="checkbox" bind:checked={v.use_playwright} />
							Playwright SPA
						</label>
						<button
							type="button"
							disabled={running}
							class="text-indigo-400 hover:text-indigo-300 disabled:opacity-50"
							onclick={() => doRun(false, v.id)}
						>Запустить</button>
					</div>
				</div>
			{/each}
		</section>

		<div class="flex flex-wrap gap-2">
			<button
				type="button"
				disabled={saving}
				class="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm disabled:opacity-50"
				onclick={save}
			>{saving ? 'Сохранение…' : 'Сохранить конфиг'}</button>
			<button
				type="button"
				disabled={running}
				class="px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-sm disabled:opacity-50"
				onclick={() => doRun(true)}
			>Dry-run все</button>
			<button
				type="button"
				disabled={running}
				class="px-4 py-2 rounded-lg bg-emerald-800 text-sm disabled:opacity-50"
				onclick={() => doRun(false)}
			>Запустить все enabled</button>
		</div>

		{#if status?.last_run}
			<section class="bg-gray-900 border border-gray-800 rounded-lg p-4 text-sm">
				<h3 class="font-medium text-white mb-2">Последний прогон</h3>
				<p class="text-gray-400">{status.last_run.generated_at} · чанков: {status.last_run.total_chunks}</p>
				{#if status.last_run.stats}
					<p class="text-xs text-gray-500 mt-1">
						HTML OK: {status.last_run.stats.pages_html_ok} · PDF OK: {status.last_run.stats.pages_pdf_ok} ·
						поиск PDF: {status.last_run.stats.pdf_search_found ?? 0} ·
						Playwright: {status.last_run.stats.playwright_pdf_found ?? 0} ·
						отбр. качество: {status.last_run.stats.quality_rejected ?? 0} ·
						мусор URL: {status.last_run.stats.filtered_junk}
					</p>
				{/if}
			</section>
		{/if}
	{/if}
</div>
