<script>
	import {
		previewCampaignSegment,
		previewCampaignLlm,
		testCampaignSend,
		createCampaign,
		fetchEmailCampaigns,
	} from '$lib/emailStorage.js';
	import {
		NURTURE_PRODUCT_PRESETS,
		DEFAULT_TEST_EMAIL,
		buildSegmentFilters,
		campaignPreviewPayload,
		campaignLaunchPayload,
		firstExample,
	} from '$lib/email/campaignSegmentLogic.js';
	import { fetchLeadIndustries } from '$lib/leads/industryCatalog.js';

	let { accounts = [], error = $bindable(''), success = $bindable('') } = $props();

	let accountId = $state(null);
	let stage = $state('all');
	let minScore = $state(50);
	let industry = $state('');
	let industryVerified = $state(false);
	let industryOptions = $state([]);
	let withoutIndustry = $state(null);
	let city = $state('');
	let search = $state('');
	let product = $state(NURTURE_PRODUCT_PRESETS[0]);
	let productCustom = $state('');
	let themeMode = $state('marketer');
	let senderName = $state('Иван Б.');
	let senderEmail = $state(DEFAULT_TEST_EMAIL);
	let subjectTemplate = $state('{{company}} — {{product}}');
	let bodyTemplate = $state('{{greeting}}\n\nПредлагаем {{product}} для {{company}}.\n\n{{sender}}');
	let campaignName = $state('');
	let testEmail = $state(DEFAULT_TEST_EMAIL);
	let segmentCount = $state(null);
	let preview = $state(null);
	let examples = $state([]);
	let approved = $state(false);
	let campaigns = $state([]);
	let busy = $state('');

	const productValue = $derived(product === '__custom__' ? (productCustom || '').trim() : product);
	const filterState = $derived({
		stage,
		minScore,
		industry,
		industryVerified,
		city,
		search,
		product: productValue,
		senderName,
		senderEmail,
		themeMode,
		subjectTemplate,
		bodyTemplate,
		accountId,
		campaignName,
	});

	async function loadIndustryOptions() {
		try {
			industryOptions = await fetchLeadIndustries();
		} catch {
			industryOptions = [];
		}
	}

	async function loadHistory() {
		try {
			campaigns = await fetchEmailCampaigns();
		} catch {
			campaigns = [];
		}
	}

	async function onCountPreview() {
		busy = 'count';
		error = '';
		try {
			const r = await previewCampaignSegment(buildSegmentFilters(filterState));
			segmentCount = r.count;
			withoutIndustry = r.withoutIndustry ?? null;
		} catch (e) {
			error = e?.message || String(e);
		} finally {
			busy = '';
		}
	}

	async function onLlmPreview() {
		if (!productValue) { error = 'Укажи продукт'; return; }
		busy = 'preview';
		error = '';
		approved = false;
		try {
			const r = await previewCampaignLlm(campaignPreviewPayload(filterState));
			preview = r;
			examples = r.examples || [];
			segmentCount = r.count;
			withoutIndustry = r.withoutIndustry ?? null;
			success = r.has_rag ? '3 примера готовы (RAG)' : '3 примера готовы';
		} catch (e) {
			error = e?.message || String(e);
		} finally {
			busy = '';
		}
	}

	async function onTestIb() {
		const ex = firstExample(examples);
		if (!accountId || !ex) { error = 'Сначала сгенерируй превью'; return; }
		busy = 'test';
		try {
			await testCampaignSend({ account_id: accountId, to_email: testEmail, subject: ex.subject, body: ex.body });
			success = `Тест на ${testEmail}`;
		} catch (e) {
			error = e?.message || String(e);
		} finally {
			busy = '';
		}
	}

	async function onApproveAndSend() {
		if (!preview || !accountId) { error = 'Превью и аккаунт обязательны'; return; }
		if (!approved) { error = 'Подтверди 3 примера'; return; }
		busy = 'send';
		error = '';
		try {
			const r = await createCampaign(campaignLaunchPayload(filterState, preview));
			success = `Отправлено: ${r.sentCount ?? 0} из ${preview.count}`;
			await loadHistory();
		} catch (e) {
			error = e?.message || String(e);
		} finally {
			busy = '';
		}
	}

	$effect(() => {
		loadHistory();
		loadIndustryOptions();
	});
</script>

<div class="flex-1 overflow-y-auto min-h-0 px-5 py-4 space-y-5" data-testid="campaign-mass-panel">
	<div class="grid gap-5 lg:grid-cols-[2fr_1fr]">
		<div class="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
			<p class="text-xs text-gray-400 uppercase font-semibold">Массовая рассылка · сегмент</p>
			<select bind:value={accountId} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5 text-sm text-white" data-testid="campaign-account">
				<option value={null}>Аккаунт…</option>
				{#each accounts as a (a.id)}<option value={a.id}>{a.name} ({a.username})</option>{/each}
			</select>
			<input bind:value={campaignName} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2 text-sm text-white" placeholder="Название кампании" />
			<div class="grid grid-cols-2 gap-2">
				<select bind:value={stage} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white">
					<option value="all">Все этапы</option>
					<option value="Новый">Новый</option>
					<option value="Квалифицирован">Квалифицирован</option>
					<option value="Переговоры">Переговоры</option>
					<option value="КП отправлено">КП отправлено</option>
				</select>
				<input type="number" bind:value={minScore} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="Min score" />
			</div>
			<div class="grid grid-cols-2 gap-2">
				<select bind:value={industry} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" data-testid="campaign-industry">
					<option value="">Все отрасли</option>
					{#each industryOptions as opt (opt)}<option value={opt}>{opt}</option>{/each}
				</select>
				<input bind:value={city} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="Город" />
			</div>
			<label class="flex items-center gap-2 text-xs text-gray-400">
				<input type="checkbox" bind:checked={industryVerified} class="accent-indigo-500" data-testid="campaign-industry-verified" />
				Только лиды с проверенной отраслью
			</label>
			<input bind:value={search} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="Поиск (компания, контакт…)" />
			<button type="button" onclick={onCountPreview} disabled={!!busy} class="text-xs text-indigo-400 hover:underline text-left">1. Сколько лидов в сегменте?</button>
			{#if segmentCount != null}
				<p class="text-xs text-gray-500" data-testid="campaign-segment-count">
					Лидов: {segmentCount}
					{#if withoutIndustry != null && withoutIndustry > 0}
						<span class="text-amber-500/90"> · без отрасли: {withoutIndustry}</span>
					{/if}
				</p>
			{/if}
			<select bind:value={product} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white">
				{#each NURTURE_PRODUCT_PRESETS as p}<option value={p}>{p}</option>{/each}
				<option value="__custom__">Свой продукт…</option>
			</select>
			{#if product === '__custom__'}<input bind:value={productCustom} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="Продукт" />{/if}
			<div class="flex gap-4 text-sm text-gray-300">
				<label class="flex items-center gap-2"><input type="radio" bind:group={themeMode} value="marketer" class="accent-indigo-500" /> Маркетолог</label>
				<label class="flex items-center gap-2"><input type="radio" bind:group={themeMode} value="manual" class="accent-indigo-500" /> Свой шаблон</label>
			</div>
			{#if themeMode === 'manual'}
				<input bind:value={subjectTemplate} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" />
				<textarea bind:value={bodyTemplate} class="w-full h-20 rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white resize-none"></textarea>
			{/if}
			<div class="grid grid-cols-2 gap-2">
				<input bind:value={senderName} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="Подпись" />
				<input bind:value={senderEmail} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="email подписи" />
			</div>
			<button type="button" onclick={onLlmPreview} disabled={!!busy} class="w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50" data-testid="campaign-preview-llm">2. Маркетолог → 3 примера</button>
			<div class="flex gap-2">
				<input bind:value={testEmail} class="flex-1 rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" />
				<button type="button" onclick={onTestIb} disabled={!!busy} class="rounded-xl bg-gray-700 px-4 py-2 text-sm text-white" data-testid="campaign-test-ib">3. Тест ib@</button>
			</div>
			<label class="flex items-center gap-2 text-sm text-gray-300">
				<input type="checkbox" bind:checked={approved} class="accent-indigo-500" data-testid="campaign-approve" />
				Подтверждаю 3 примера — можно слать сегменту
			</label>
			<button type="button" onclick={onApproveAndSend} disabled={!!busy || !approved} class="w-full rounded-xl bg-green-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-green-500 disabled:opacity-50" data-testid="campaign-send-now">4. Отправить кампанию</button>
		</div>
		<div class="space-y-3">
			{#if preview?.marketer}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-4 text-xs text-gray-300 space-y-1" data-testid="campaign-marketer-block">
					{#if preview.marketer.segment_insight}<p><span class="text-gray-500">Сегмент:</span> {preview.marketer.segment_insight}</p>{/if}
					{#if preview.marketer.product_fit}<p><span class="text-gray-500">Fit:</span> {preview.marketer.product_fit}</p>{/if}
					{#if preview.marketer.summary}<p>{preview.marketer.summary}</p>{/if}
				</div>
			{/if}
			{#each examples as ex, i}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-4 text-xs" data-testid="campaign-example-{i}">
					<p class="text-indigo-300 font-medium">{i + 1}. {ex.company} — {ex.subject}</p>
					<p class="text-gray-400 mt-1 whitespace-pre-wrap line-clamp-6">{(ex.body || '').slice(0, 320)}</p>
				</div>
			{/each}
		</div>
	</div>
	<div class="bg-gray-900 border border-gray-800 rounded-2xl p-5">
		<p class="text-xs text-gray-400 uppercase font-semibold mb-3">История кампаний</p>
		{#if campaigns.length}
			<table class="w-full text-left text-xs text-gray-300" data-testid="campaign-history-table">
				<thead class="text-gray-500"><tr><th class="pb-2">ID</th><th class="pb-2">Название</th><th class="pb-2">Статус</th><th class="pb-2">Отправлено</th></tr></thead>
				<tbody>
					{#each campaigns as c (c.id)}
						<tr class="border-t border-gray-800">
							<td class="py-2">{c.id}</td>
							<td class="py-2">{c.name}</td>
							<td class="py-2">{c.status}</td>
							<td class="py-2">{c.sentCount}/{c.leadIds?.length ?? 0}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{:else}<p class="text-sm text-gray-500">Нет кампаний</p>{/if}
	</div>
</div>
