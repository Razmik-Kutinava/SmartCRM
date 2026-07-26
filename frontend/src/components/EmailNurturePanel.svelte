<script>
	import {
		previewNurtureLlm,
		startNurtureLlm,
		testNurtureSend,
		fetchNurtureChains,
	} from '$lib/emailStorage.js';
	import {
		NURTURE_TOUCH_COUNTS,
		NURTURE_PRODUCT_PRESETS,
		NURTURE_CHAIN_TYPES,
		DEFAULT_TEST_EMAIL,
		nurturePayloadBase,
		firstEmailForTest,
	} from '$lib/email/nurtureTouchLogic.js';
	import { isIndustryEmpty } from '$lib/leads/industryCatalog.js';
	import { openLeadIndustryModal } from '$lib/leads/leadIndustryUi.js';

	let {
		accounts = [],
		leads = [],
		error = $bindable(''),
		success = $bindable(''),
		initialLeadId = null,
		lockLead = false,
		compact = false,
	} = $props();

	let accountId = $state(null);
	let leadId = $state(null);
	let touchCount = $state(3);
	let chainType = $state('new');
	let product = $state(NURTURE_PRODUCT_PRESETS[0]);
	let productCustom = $state('');
	let themeMode = $state('marketer');
	let senderName = $state('Иван Б.');
	let senderEmail = $state(DEFAULT_TEST_EMAIL);
	let subjectTemplate = $state('{{company}} — {{product}} · касание {{n}}');
	let bodyTemplate = $state('');
	let testEmail = $state(DEFAULT_TEST_EMAIL);
	let preview = $state(null);
	let previewEmails = $state([]);
	let chains = $state([]);
	let busy = $state('');
	let localLeadPatch = $state(null);

	const productValue = $derived(
		product === '__custom__' ? (productCustom || '').trim() : product
	);

	const selectedLead = $derived.by(() => {
		const fromList = leads.find((l) => l.id === leadId) ?? null;
		if (!fromList) return localLeadPatch;
		return localLeadPatch ? { ...fromList, ...localLeadPatch } : fromList;
	});

	function runWithIndustry(fn) {
		const lead = selectedLead;
		if (!leadId || !lead) {
			error = 'Выбери лида';
			return;
		}
		if (isIndustryEmpty(lead.industry)) {
			openLeadIndustryModal(lead, {
				onSaved: (saved) => {
					localLeadPatch = saved;
					fn();
				},
			});
			return;
		}
		fn();
	}

	$effect(() => {
		if (initialLeadId != null) leadId = initialLeadId;
	});

	$effect(() => {
		if (leadId) loadHistory();
	});

	async function loadHistory() {
		try {
			chains = await fetchNurtureChains(leadId || undefined);
		} catch {
			chains = [];
		}
	}

	async function onPreview() {
		if (!leadId || !productValue) {
			error = 'Выбери лида и продукт';
			return;
		}
		runWithIndustry(async () => {
			error = '';
			success = '';
			busy = 'preview';
			try {
				const base = nurturePayloadBase({
					leadId,
					product: productValue,
					touchCount,
					chainType,
					senderName,
					senderEmail,
					themeMode,
					subjectTemplate,
					bodyTemplate,
				});
				const r = await previewNurtureLlm(base);
				preview = r.marketer;
				previewEmails = r.emails || [];
				success = r.has_rag
					? 'Превью готово (RAG подключён)'
					: 'Превью готово (без RAG — только общие формулировки)';
			} catch (e) {
				error = e?.message || String(e);
			} finally {
				busy = '';
			}
		});
	}

	async function onTestIb() {
		const em = firstEmailForTest(previewEmails);
		if (!accountId || !em) {
			error = 'Сначала сгенерируй превью';
			return;
		}
		busy = 'test';
		error = '';
		try {
			await testNurtureSend({
				account_id: accountId,
				to_email: testEmail,
				subject: em.subject,
				body: em.body,
			});
			success = `Тест отправлен на ${testEmail}`;
		} catch (e) {
			error = e?.message || String(e);
		} finally {
			busy = '';
		}
	}

	async function onLaunch(sendNow) {
		if (!leadId || !accountId || !productValue) {
			error = 'Лид, аккаунт и продукт обязательны';
			return;
		}
		if (!previewEmails.length) {
			error = 'Сначала сгенерируй превью';
			return;
		}
		busy = 'launch';
		error = '';
		try {
			const base = nurturePayloadBase({
				leadId,
				product: productValue,
				touchCount,
				chainType,
				senderName,
				senderEmail,
				themeMode,
				subjectTemplate,
				bodyTemplate,
			});
			const r = await startNurtureLlm({
				...base,
				account_id: accountId,
				emails: previewEmails,
				send_now: sendNow,
			});
			success = sendNow
				? `Цепочка #${r.chain?.id} запущена, отправлено: ${r.process_due?.emails_sent ?? 0}`
				: `Цепочка #${r.chain?.id} создана (отправка по расписанию)`;
			await loadHistory();
		} catch (e) {
			error = e?.message || String(e);
		} finally {
			busy = '';
		}
	}
</script>

<div
	class="flex-1 overflow-y-auto min-h-0 {compact ? 'px-4 py-3' : 'px-5 py-4'} space-y-5"
	data-testid="nurture-touch-panel"
>
	<div class="grid gap-5 {compact ? 'grid-cols-1' : 'lg:grid-cols-[2fr_1fr]'}">
		<div class="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
			<p class="text-xs text-gray-400 uppercase tracking-wide font-semibold">
				{compact ? 'Касания' : 'Точечные касания · 1 лид'}
			</p>

			<select bind:value={accountId} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5 text-sm text-white" data-testid="nurture-account">
				<option value={null}>Аккаунт отправки…</option>
				{#each accounts as a (a.id)}
					<option value={a.id}>{a.name} ({a.username})</option>
				{/each}
			</select>

			{#if lockLead && leadId}
				<div
					class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5 text-sm text-white"
					data-testid="nurture-lead-locked"
				>
					{selectedLead?.company || `Лид #${leadId}`}
					{#if selectedLead?.industry && !isIndustryEmpty(selectedLead.industry)}
						<span class="text-gray-500"> · {selectedLead.industry}</span>
						{#if selectedLead.industryVerified}
							<span class="text-emerald-500 text-[10px]" title="Отрасль проверена"> ✓</span>
						{/if}
					{:else}
						<span class="text-amber-500 text-xs"> · укажи отрасль</span>
					{/if}
					{#if selectedLead?.productsOwned?.length}
						<span class="block text-[11px] text-gray-500 mt-1">Уже купили: {selectedLead.productsOwned.join(', ')}</span>
					{/if}
				</div>
			{:else}
				<select bind:value={leadId} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5 text-sm text-white" data-testid="nurture-lead">
					<option value={null}>Лид…</option>
					{#each leads as l (l.id)}
						<option value={l.id}>{l.company} · {l.industry || '—'}</option>
					{/each}
				</select>
			{/if}

			<div class="grid grid-cols-2 gap-2">
				<select bind:value={touchCount} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white">
					{#each NURTURE_TOUCH_COUNTS as n}<option value={n}>{n} касаний</option>{/each}
				</select>
				<select bind:value={product} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white">
					{#each NURTURE_PRODUCT_PRESETS as p}<option value={p}>{p}</option>{/each}
					<option value="__custom__">Свой продукт…</option>
				</select>
			</div>
			{#if product === '__custom__'}
				<input bind:value={productCustom} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2 text-sm text-white" placeholder="Название продукта" />
			{/if}

			<select bind:value={chainType} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2 text-sm text-white" data-testid="nurture-chain-type">
				{#each NURTURE_CHAIN_TYPES as t (t.id)}
					<option value={t.id}>{t.label} — {t.hint}</option>
				{/each}
			</select>

			<div class="flex gap-4 text-sm text-gray-300">
				<label class="flex items-center gap-2"><input type="radio" bind:group={themeMode} value="marketer" class="accent-indigo-500" /> Маркетолог (LLM)</label>
				<label class="flex items-center gap-2"><input type="radio" bind:group={themeMode} value="manual" class="accent-indigo-500" /> Свои шаблоны</label>
			</div>

			{#if themeMode === 'manual'}
				<input bind:value={subjectTemplate} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2 text-sm text-white" placeholder={'Тема: {{company}} — {{product}} · {{n}}'} />
				<textarea bind:value={bodyTemplate} class="w-full h-24 rounded-xl bg-gray-950 border border-gray-800 px-4 py-2 text-sm text-white resize-none" placeholder={'Текст… {{greeting}} {{company}} {{product}} {{sender}}'}></textarea>
			{/if}

			<div class="grid grid-cols-2 gap-2">
				<input bind:value={senderName} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="Подпись: имя" />
				<input bind:value={senderEmail} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="email подписи" />
			</div>

			<button type="button" onclick={onPreview} disabled={!!busy} class="w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50" data-testid="nurture-preview">
				{busy === 'preview' ? '…' : '1. Сгенерировать превью'}
			</button>

			<div class="flex gap-2">
				<input bind:value={testEmail} class="flex-1 rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="Тест email" />
				<button type="button" onclick={onTestIb} disabled={!!busy} class="rounded-xl bg-gray-700 px-4 py-2 text-sm text-white hover:bg-gray-600 disabled:opacity-50" data-testid="nurture-test-ib">
					2. Тест
				</button>
			</div>

			<div class="flex gap-2">
				<button type="button" onclick={() => onLaunch(false)} disabled={!!busy} class="flex-1 rounded-xl bg-gray-700 px-4 py-2.5 text-sm text-white hover:bg-gray-600 disabled:opacity-50">3a. Запуск (по дням)</button>
				<button type="button" onclick={() => onLaunch(true)} disabled={!!busy} class="flex-1 rounded-xl bg-green-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-green-500 disabled:opacity-50" data-testid="nurture-launch-now">3b. Отправить сейчас</button>
			</div>
		</div>

		<div class="space-y-4">
			{#if preview}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-4 text-xs text-gray-300 space-y-2" data-testid="nurture-preview-block">
					<p><span class="text-gray-500">Профиль:</span> {typeof preview.buyer_profile === 'string' ? preview.buyer_profile : JSON.stringify(preview.buyer_profile)}</p>
					{#if preview.attack_surface}<p><span class="text-gray-500">Attack surface:</span> {typeof preview.attack_surface === 'string' ? preview.attack_surface : JSON.stringify(preview.attack_surface)}</p>{/if}
				</div>
			{/if}
			{#if previewEmails.length}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-4 max-h-64 overflow-y-auto space-y-3" data-testid="nurture-emails-preview">
					{#each previewEmails as em, i}
						<div class="border-b border-gray-800 pb-2 text-xs">
							<p class="text-indigo-300 font-medium">{i + 1}. {em.subject}</p>
							<p class="text-gray-400 mt-1 whitespace-pre-wrap">{(em.body || '').slice(0, 280)}…</p>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	{#if !compact}
	<div class="bg-gray-900 border border-gray-800 rounded-2xl p-5">
		<p class="text-xs text-gray-400 uppercase font-semibold mb-3">История цепочек</p>
		{#if chains.length}
			<table class="w-full text-left text-xs text-gray-300" data-testid="nurture-history-table">
				<thead class="text-gray-500"><tr><th class="pb-2">ID</th><th class="pb-2">Лид</th><th class="pb-2">Статус</th><th class="pb-2">Шаги</th></tr></thead>
				<tbody>
					{#each chains as c (c.id)}
						<tr class="border-t border-gray-800">
							<td class="py-2">{c.id}</td>
							<td class="py-2">{c.leadCompany || c.leadId}</td>
							<td class="py-2">{c.status}</td>
							<td class="py-2">{c.stepsSent}/{c.stepsTotal}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{:else}
			<p class="text-sm text-gray-500">Нет цепочек</p>
		{/if}
	</div>
	{:else if chains.length}
		<div class="px-4 pb-3 text-xs text-gray-500" data-testid="nurture-history-compact">
			Активных цепочек по лиду: {chains.length}
			{#each chains.slice(0, 3) as c (c.id)}
				<span class="ml-2 text-gray-400">#{c.id} {c.status} ({c.stepsSent}/{c.stepsTotal})</span>
			{/each}
		</div>
	{/if}
</div>
