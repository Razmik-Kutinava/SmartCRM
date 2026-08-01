<script>
	import { apiImportPreview, apiImportLeadsCsv } from '$lib/leadsStorage.js';

	let { open = $bindable(false), onImported = null } = $props();

	let step = $state('file'); // file | mapping | report
	let file = $state(null);
	let dragOver = $state(false);
	let busy = $state(false);
	let error = $state('');
	/** @type {{ headers: string[], rows: string[][], totalRows: number, mapping: Record<string,string>, fields: Array<{id:string,label:string,required:boolean}>, suggestedSource: string } | null} */
	let preview = $state(null);
	/** @type {Record<string, string>} */
	let mapping = $state({});
	let sourceLabel = $state('');
	let mode = $state('upsert');
	/** @type {{ imported: number, updated: number, skipped: number, total_rows: number, errors: string[], error_count: number, source: string | null } | null} */
	let report = $state(null);

	const companyColumn = $derived(String(mapping.company || ''));
	const mappedCount = $derived(Object.values(mapping).filter((v) => String(v || '')).length);
	const rowsWord = $derived(rowsPlural(preview?.totalRows ?? 0));

	function rowsPlural(n) {
		const tail = n % 100;
		if (tail >= 11 && tail <= 14) return 'строк';
		const last = n % 10;
		if (last === 1) return 'строку';
		if (last >= 2 && last <= 4) return 'строки';
		return 'строк';
	}

	function reset() {
		step = 'file';
		file = null;
		preview = null;
		mapping = {};
		sourceLabel = '';
		report = null;
		error = '';
		busy = false;
		dragOver = false;
	}

	function close() {
		open = false;
		reset();
	}

	async function loadPreview(f) {
		if (!f || busy) return;
		file = f;
		busy = true;
		error = '';
		try {
			const data = await apiImportPreview(f);
			preview = data;
			mapping = { ...(data.mapping || {}) };
			sourceLabel = data.suggestedSource || '';
			step = 'mapping';
		} catch (e) {
			error = String(e?.message || e);
		} finally {
			busy = false;
		}
	}

	function onFileInput(e) {
		const f = e.target?.files?.[0];
		if (f) loadPreview(f);
	}

	function onDrop(e) {
		e.preventDefault();
		dragOver = false;
		const f = e.dataTransfer?.files?.[0];
		if (f) loadPreview(f);
	}

	async function submitImport() {
		if (!file || busy) return;
		if (!companyColumn) {
			error = 'Выберите колонку для поля «Компания» — без него лид не создать';
			return;
		}
		busy = true;
		error = '';
		try {
			const clean = Object.fromEntries(
				Object.entries(mapping).filter(([, header]) => String(header || '')),
			);
			const res = await apiImportLeadsCsv(file, mode, sourceLabel.trim(), clean);
			report = res;
			step = 'report';
			onImported?.(res);
		} catch (e) {
			error = String(e?.message || e);
		} finally {
			busy = false;
		}
	}
</script>

{#if open}
	<div class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/70 p-4 sm:p-8">
		<button type="button" class="fixed inset-0 cursor-default" aria-label="Закрыть" onclick={close}></button>
		<div
			class="relative w-full max-w-3xl rounded-2xl border border-gray-800 bg-gray-950 shadow-2xl"
			data-testid="leads-import-modal"
		>
			<div class="flex items-center justify-between border-b border-gray-800 px-5 py-3.5">
				<div>
					<h2 class="text-base font-semibold text-white">Импорт базы лидов</h2>
					<p class="mt-0.5 text-xs text-gray-500">
						{step === 'file' ? 'Шаг 1 из 3 — файл' : step === 'mapping' ? 'Шаг 2 из 3 — колонки и имя базы' : 'Шаг 3 из 3 — отчёт'}
					</p>
				</div>
				<button
					type="button"
					class="h-8 w-8 rounded-lg text-gray-500 hover:bg-gray-800 hover:text-white"
					aria-label="Закрыть"
					onclick={close}
				>✕</button>
			</div>

			<div class="px-5 py-4">
				{#if error}
					<p class="mb-3 rounded-lg border border-red-900 bg-red-950/60 px-3 py-2 text-sm text-red-300" data-testid="leads-import-error">
						{error}
					</p>
				{/if}

				{#if step === 'file'}
					<div
						role="button"
						tabindex="0"
						class="flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors
							{dragOver ? 'border-indigo-500 bg-indigo-950/30' : 'border-gray-700 hover:border-gray-600'}"
						data-testid="leads-import-dropzone"
						ondragover={(e) => { e.preventDefault(); dragOver = true; }}
						ondragleave={() => { dragOver = false; }}
						ondrop={onDrop}
						onclick={() => document.querySelector('[data-testid="leads-import-file"]')?.click()}
						onkeydown={(e) => { if (e.key === 'Enter') document.querySelector('[data-testid="leads-import-file"]')?.click(); }}
					>
						<span class="text-3xl">📥</span>
						<p class="text-sm text-gray-300">{busy ? 'Читаю файл…' : 'Перетащите файл сюда или нажмите, чтобы выбрать'}</p>
						<p class="text-xs text-gray-600">Excel (.xlsx, .xlsm) или CSV · до 8 МБ · первая строка — заголовки</p>
					</div>
					<input
						type="file"
						accept=".csv,.txt,.xlsx,.xlsm,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
						class="hidden"
						data-testid="leads-import-file"
						onchange={onFileInput}
					/>
				{:else if step === 'mapping' && preview}
					<div class="mb-3 flex flex-wrap items-end gap-3">
						<label class="min-w-[14rem] flex-1">
							<span class="mb-1 block text-[10px] uppercase tracking-wider text-gray-600">Имя базы</span>
							<input
								bind:value={sourceLabel}
								class="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-200 placeholder-gray-600"
								placeholder="Например: Excel клиенты 2026"
								data-testid="leads-import-source"
							/>
						</label>
						<label class="min-w-[10rem]">
							<span class="mb-1 block text-[10px] uppercase tracking-wider text-gray-600">Дубли</span>
							<select
								bind:value={mode}
								class="w-full rounded-lg border border-gray-700 bg-gray-900 px-2 py-2 text-xs text-gray-200"
								data-testid="leads-import-mode"
							>
								<option value="upsert">Обновлять совпадения</option>
								<option value="skip">Пропускать совпадения</option>
							</select>
						</label>
						<p class="pb-2 text-xs text-gray-500">
							{file?.name} · строк: <span class="text-gray-300">{preview.totalRows}</span> · сопоставлено полей: {mappedCount}
						</p>
					</div>

					<div class="max-h-64 overflow-y-auto rounded-xl border border-gray-800" data-testid="leads-import-mapping">
						<table class="w-full text-xs">
							<thead class="sticky top-0 bg-gray-900 text-gray-500">
								<tr>
									<th class="px-3 py-2 text-left font-medium">Поле лида</th>
									<th class="px-3 py-2 text-left font-medium">Колонка файла</th>
									<th class="px-3 py-2 text-left font-medium">Пример</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-800/60">
								{#each preview.fields as f (f.id)}
									{@const colIndex = preview.headers.indexOf(mapping[f.id])}
									<tr class="hover:bg-gray-900/60">
										<td class="px-3 py-1.5 text-gray-300">
											{f.label}{#if f.required}<span class="ml-1 text-red-400">*</span>{/if}
										</td>
										<td class="px-3 py-1.5">
											<select
												bind:value={mapping[f.id]}
												class="w-full rounded border border-gray-700 bg-gray-900 px-2 py-1 text-gray-200
													{f.required && !mapping[f.id] ? 'border-red-700' : ''}"
												data-testid="leads-import-map-{f.id}"
											>
												<option value="">— не импортировать —</option>
												{#each preview.headers as h, i (h + i)}
													<option value={h}>{h || `Колонка ${i + 1}`}</option>
												{/each}
											</select>
										</td>
										<td class="max-w-[12rem] truncate px-3 py-1.5 text-gray-600">
											{colIndex >= 0 ? (preview.rows[0]?.[colIndex] ?? '') : ''}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else if step === 'report' && report}
					<div class="space-y-3" data-testid="leads-import-report">
						<div class="grid grid-cols-3 gap-3">
							<div class="rounded-xl border border-green-900 bg-green-950/40 px-3 py-2">
								<p class="text-[10px] uppercase tracking-wider text-green-600">Добавлено</p>
								<p class="text-lg font-semibold text-green-300">{report.imported}</p>
							</div>
							<div class="rounded-xl border border-gray-800 bg-gray-900 px-3 py-2">
								<p class="text-[10px] uppercase tracking-wider text-gray-600">Обновлено</p>
								<p class="text-lg font-semibold text-gray-200">{report.updated}</p>
							</div>
							<div class="rounded-xl border border-amber-900/70 bg-amber-950/30 px-3 py-2">
								<p class="text-[10px] uppercase tracking-wider text-amber-700">Пропущено</p>
								<p class="text-lg font-semibold text-amber-300">{report.skipped}</p>
							</div>
						</div>
						<p class="text-xs text-gray-500">
							База: <span class="text-gray-300">{report.source || '—'}</span> · строк в файле: {report.total_rows}
						</p>
						{#if report.error_count > 0}
							<div class="rounded-xl border border-red-900/70 bg-red-950/30 px-3 py-2">
								<p class="text-xs text-red-300">Ошибки: {report.error_count}</p>
								<ul class="mt-1 max-h-32 space-y-0.5 overflow-y-auto text-[11px] text-red-400/90">
									{#each report.errors || [] as line, i (i)}
										<li>{line}</li>
									{/each}
								</ul>
							</div>
						{/if}
					</div>
				{/if}
			</div>

			<div class="flex items-center justify-between gap-2 border-t border-gray-800 px-5 py-3">
				<button
					type="button"
					class="px-3 py-2 text-xs text-gray-500 hover:text-gray-300"
					onclick={step === 'mapping' ? reset : close}
				>{step === 'mapping' ? '← Другой файл' : 'Закрыть'}</button>
				{#if step === 'mapping'}
					<button
						type="button"
						disabled={busy || !companyColumn}
						class="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
						data-testid="leads-import-submit"
						onclick={submitImport}
					>{busy ? 'Импортирую…' : `Импортировать ${preview?.totalRows ?? 0} ${rowsWord}`}</button>
				{:else if step === 'report'}
					<button
						type="button"
						class="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
						data-testid="leads-import-done"
						onclick={close}
					>Готово</button>
				{/if}
			</div>
		</div>
	</div>
{/if}
