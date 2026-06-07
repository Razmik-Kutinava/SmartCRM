<script>
	import { getApiUrl } from '$lib/websocket.js';
	const API = getApiUrl();

	// ── Вкладки верхнего уровня ──────────────────────────────────────────────
	const TABS = [
		{ id: 'search',   label: 'Поиск тендеров',  icon: '◎' },
		{ id: 'my',       label: 'Мои тендеры',      icon: '◆' },
		{ id: 'archive',  label: 'Архив',             icon: '◈' },
	];
	let tab = $state('search');

	// ── Фильтры поиска ────────────────────────────────────────────────────────
	let search_mode = $state('tenders'); // tenders | plans
	let f_keywords  = $state('');
	let f_law       = $state('all');    // all | 44 | 223
	let f_budget_from = $state('');
	let f_budget_to   = $state('');
	let f_date_from   = $state('');
	let f_date_to     = $state('');
	let f_region    = $state('');
	let f_okpd      = $state('');
	let f_plan_inn  = $state('');
	let f_plan_year = $state(new Date().getFullYear());

	// ── Состояние поиска ──────────────────────────────────────────────────────
	let loading     = $state(false);
	let error       = $state('');
	let results     = $state([]);
	let searched    = $state(false);
	/** Подсказки Мои-Закупки (ОКПД-2 / КТРУ) с бэкенда */
	let classifiers = $state(null);

	// ── Выбранный тендер (правая панель) ──────────────────────────────────────
	let selected    = $state(null);
	let detail_tab  = $state('doc');   // doc | files | tender_agent | tech_agent

	// ── Загрузка файлов ───────────────────────────────────────────────────────
	let uploaded_files = $state([]);
	let upload_loading = $state(false);

	// ── Агенты ────────────────────────────────────────────────────────────────
	let tender_analysis = $state(null);
	let tech_analysis   = $state(null);
	let agent_loading   = $state(false);

	// ── Mock-данные для демонстрации UI ───────────────────────────────────────
	const MOCK_RESULTS = [
		{
			id: '0373100080526000001',
			title: 'Поставка программного обеспечения для мониторинга ИТ-инфраструктуры',
			customer: 'ФГБУ «Центр информационных технологий»',
			law: '44-ФЗ',
			budget: 4200000,
			deadline: '2026-05-10',
			published: '2026-04-12',
			region: 'Москва',
			okpd: '62.01.29',
			source: 'ЕИС',
			status: 'active',
			relevance: 97,
			url: 'https://zakupki.gov.ru/epz/order/notice/ea44/view/common-info.html?regNumber=0373100080526000001',
			description: 'Закупка включает поставку лицензий ПО для мониторинга серверной инфраструктуры, сетевых устройств и приложений. Требуется поддержка SNMP, WMI, агентный и безагентный мониторинг.',
			doc_md: null,
		},
		{
			id: '0348100003226000042',
			title: 'Оказание услуг технической поддержки системы управления ИТ-активами (ITAM)',
			customer: 'АО «Государственная транспортная корпорация»',
			law: '223-ФЗ',
			budget: 1850000,
			deadline: '2026-04-28',
			published: '2026-04-10',
			region: 'Санкт-Петербург',
			okpd: '62.02.30',
			source: 'ЕИС',
			status: 'active',
			relevance: 91,
			url: '#',
			description: 'Техническая поддержка, обновление и развитие ITAM-системы. Требуется опыт работы с решениями класса ITSM/ITAM не менее 3 лет.',
			doc_md: null,
		},
		{
			id: '0160200005026000018',
			title: 'Поставка и внедрение системы защиты информации (SIEM)',
			customer: 'ГКУ «Управление информационных технологий Краснодарского края»',
			law: '44-ФЗ',
			budget: 9700000,
			deadline: '2026-05-20',
			published: '2026-04-09',
			region: 'Краснодар',
			okpd: '62.01.21',
			source: 'ЕИС',
			status: 'active',
			relevance: 85,
			url: '#',
			description: 'Требуется поставка, установка, настройка и ввод в эксплуатацию SIEM-системы. ПО должно быть включено в реестр российского ПО. Интеграция с Active Directory, Syslog.',
			doc_md: null,
		},
	];

	const MOCK_TENDER_ANALYSIS = `## Анализ тендера — Тендерный специалист

**Вердикт: Участвовать ✅**

### Ключевые параметры
| Параметр | Значение |
|---|---|
| НМЦ | 4 200 000 ₽ |
| Закон | 44-ФЗ |
| Срок подачи | 10 мая 2026 |
| Регион | Москва |
| Способ закупки | Электронный аукцион |

### Риски
- ⚠️ Короткий срок подачи — 28 дней с даты публикации
- ⚠️ Требуется лицензия ФСТЭК (уточнить наличие)
- ✅ Нет требования о местонахождении поставщика

### Требования к участнику
- Опыт аналогичных поставок (контракты на сумму не менее 20% НМЦ)
- Наличие партнёрского статуса вендора
- Обеспечение заявки: 3% от НМЦ = **126 000 ₽**

### Подводные камни
- Техническое задание содержит специфичные требования к версии ПО — необходимо уточнить у вендора совместимость
- Критерий «цена/качество» — возможен демпинг со стороны конкурентов

### Рекомендация
Участие целесообразно. Запросить у технического специалиста подтверждение соответствия продукта ТЗ.`;

	const MOCK_TECH_ANALYSIS = `## Анализ тендера — Технический специалист

**Продукт: ManageEngine OpManager** ✅

### Соответствие техническим требованиям

| Требование из ТЗ | Наш продукт | Статус |
|---|---|---|
| Мониторинг серверов (Windows/Linux) | OpManager | ✅ Полное |
| SNMP v1/v2c/v3 | OpManager | ✅ Полное |
| Агентный мониторинг | OpManager Agent | ✅ Есть |
| Безагентный мониторинг | OpManager | ✅ Есть |
| Dashboard и отчёты | OpManager | ✅ Полное |
| Реестр российского ПО | — | ⚠️ Уточнить |
| API интеграция | REST API | ✅ Полное |

### Рекомендуемая конфигурация
- **ManageEngine OpManager Standard** — до 500 устройств
- Лицензия: годовая подписка или бессрочная
- Стоимость для нас: ~1 800 000 ₽ (маржа ~57%)

### Что нужно уточнить
1. Статус реестра Минцифры — критично для 44-ФЗ
2. Версия продукта под требование ТЗ (12.x или 13.x)
3. Наличие сертификата ФСТЭК

### Документы для заявки
- Карточка продукта (есть в базе)
- Сертификат соответствия
- Письмо от вендора о партнёрстве`;

	// ── Поиск ─────────────────────────────────────────────────────────────────
	async function search() {
		if (search_mode === 'tenders' && !f_keywords.trim()) {
			error = 'Введите ключевые слова';
			return;
		}
		if (search_mode === 'plans' && !f_keywords.trim() && !f_plan_inn.trim()) {
			error = 'Для планов укажите ИНН или ключевые слова';
			return;
		}
		error = '';
		loading = true;
		searched = false;
		selected = null;
		classifiers = null;
		try {
			const endpoint = search_mode === 'plans' ? '/api/tenders/plans/search' : '/api/tenders/search';
			const params = new URLSearchParams(
				search_mode === 'plans'
					? {
						kwords: f_keywords,
						org_inn: f_plan_inn,
						fz: f_law,
						...(f_plan_year && { year: String(f_plan_year) }),
						...(f_budget_from && { price_min: f_budget_from }),
						...(f_budget_to && { price_max: f_budget_to }),
						...(f_region && { region: f_region }),
						page: '1',
					}
					: {
						q: f_keywords,
						law: f_law,
						...(f_budget_from && { price_min: f_budget_from }),
						...(f_budget_to && { price_max: f_budget_to }),
						...(f_date_from && { date_start: f_date_from }),
						...(f_date_to && { date_end: f_date_to }),
						...(f_region && { region: f_region }),
						...(f_okpd.trim() && { okpd: f_okpd.trim() }),
						page: '1',
					}
			);

			const response = await fetch(`${API}${endpoint}?${params}`);
			if (!response.ok) {
				const err = await response.json();
				throw new Error(err.detail || 'Ошибка при поиске');
			}

			const data = await response.json();
			results = (data.tenders || []).map((item) => ({
				...item,
				title: item.title || item.name || '',
				url: item.url || item.external_url || item.inner_url || '#',
			}));
			classifiers = search_mode === 'tenders' ? (data.classifiers ?? null) : null;
			searched = true;

			if (results.length === 0) {
				error = search_mode === 'plans'
					? 'Планы закупок не найдены. Попробуйте изменить критерии поиска.'
					: 'Тендеры не найдены. Попробуйте изменить критерии поиска.';
			}
		} catch (e) {
			error = 'Ошибка поиска: ' + e.message;
			results = [];
		} finally {
			loading = false;
		}
	}

	function searchKey(e) { if (e.key === 'Enter') search(); }

	function selectTender(t) {
		selected = t;
		detail_tab = 'doc';
		tender_analysis = null;
		tech_analysis = null;
		uploaded_files = [];
	}

	// ── Загрузка файлов ───────────────────────────────────────────────────────
	async function handleFileUpload(e) {
		const files = Array.from(e.target.files || []);
		if (!files.length) return;
		upload_loading = true;
		await new Promise(r => setTimeout(r, 600));
		uploaded_files = [...uploaded_files, ...files.map(f => ({
			name: f.name,
			size: f.size,
			status: 'ready',
		}))];
		upload_loading = false;
		e.target.value = '';
	}

	// ── Запуск агентов ────────────────────────────────────────────────────────
	async function runTenderAgent() {
		if (!selected) return;
		agent_loading = true;
		tender_analysis = null;
		detail_tab = 'tender_agent';
		await new Promise(r => setTimeout(r, 1400));
		tender_analysis = MOCK_TENDER_ANALYSIS;
		agent_loading = false;
	}

	async function runTechAgent() {
		if (!selected) return;
		agent_loading = true;
		tech_analysis = null;
		detail_tab = 'tech_agent';
		await new Promise(r => setTimeout(r, 1200));
		tech_analysis = MOCK_TECH_ANALYSIS;
		agent_loading = false;
	}

	// ── Утилиты ───────────────────────────────────────────────────────────────
	function fmtMoney(n) {
		if (!n) return '—';
		return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(n);
	}

	function fmtDate(s) {
		if (!s) return '—';
		const d = new Date(s);
		return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
	}

	function relevanceColor(n) {
		if (n >= 90) return 'text-green-400 bg-green-900/40';
		if (n >= 75) return 'text-yellow-400 bg-yellow-900/40';
		return 'text-gray-400 bg-gray-800';
	}

	function daysLeft(s) {
		if (!s) return null;
		const diff = Math.ceil((new Date(s) - new Date()) / 86400000);
		return diff;
	}

	function fmtFileSize(b) {
		if (b < 1024) return b + ' B';
		if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
		return (b/1048576).toFixed(1) + ' MB';
	}
</script>

<div class="flex flex-col h-full overflow-hidden">

	<!-- ── Заголовок страницы ── -->
	<div class="px-6 py-4 border-b border-gray-800 shrink-0 flex items-center justify-between">
		<div>
			<h1 class="text-lg font-semibold text-white">Тендерный специалист</h1>
			<p class="text-xs text-gray-500 mt-0.5">Поиск, анализ и сопровождение тендеров 44-ФЗ / 223-ФЗ</p>
		</div>
		<div class="flex gap-1 bg-gray-900 rounded-lg p-1">
			{#each TABS as t}
				<button
					onclick={() => tab = t.id}
					class="px-3 py-1.5 rounded-md text-xs font-medium transition-all
						{tab === t.id ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}"
				>
					<span class="mr-1.5 opacity-70">{t.icon}</span>{t.label}
				</button>
			{/each}
		</div>
	</div>

	<!-- ── Контент ── -->
	{#if tab === 'search'}
	<div class="flex flex-1 overflow-hidden">

		<!-- ── Левая панель: фильтры ── -->
		<div class="w-64 shrink-0 border-r border-gray-800 overflow-y-auto flex flex-col bg-gray-900/40">
			<div class="px-4 py-4 space-y-4">

				<div class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Фильтры</div>

				<div>
					<div class="text-xs text-gray-500 mb-1 block">Режим поиска</div>
					<div class="flex gap-1">
						<button
							onclick={() => search_mode = 'tenders'}
							class="flex-1 py-1 text-xs rounded-md border transition-all
								{search_mode === 'tenders'
									? 'bg-indigo-600 border-indigo-500 text-white'
									: 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600 hover:text-white'}"
						>Тендеры</button>
						<button
							onclick={() => search_mode = 'plans'}
							class="flex-1 py-1 text-xs rounded-md border transition-all
								{search_mode === 'plans'
									? 'bg-indigo-600 border-indigo-500 text-white'
									: 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600 hover:text-white'}"
						>Планы закупок</button>
					</div>
				</div>

				<!-- Ключевые слова -->
				<div>
					<label class="text-xs text-gray-500 mb-1 block">
						{search_mode === 'plans' ? 'Ключевые слова плана (опционально)' : 'Ключевые слова'}
					</label>
					<textarea
						bind:value={f_keywords}
						onkeydown={searchKey}
						rows="3"
						placeholder={search_mode === 'plans'
							? 'План на год, CRM, серверы, ИБ...'
							: 'Мониторинг, SIEM, ManageEngine...'}
						class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none focus:border-indigo-500 resize-none"
					></textarea>
				</div>

				{#if search_mode === 'plans'}
					<div>
						<label class="text-xs text-gray-500 mb-1 block">ИНН заказчика (опционально)</label>
						<input
							bind:value={f_plan_inn}
							type="text"
							placeholder="7707083893"
							class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-3 py-1.5 placeholder-gray-600 focus:outline-none focus:border-indigo-500"
						/>
					</div>
					<div>
						<label class="text-xs text-gray-500 mb-1 block">Год плана</label>
						<input
							bind:value={f_plan_year}
							type="number"
							min="2018"
							max="2100"
							class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
						/>
					</div>
				{/if}

				<!-- Закон -->
				<div>
					<label class="text-xs text-gray-500 mb-1 block">Закон о закупках</label>
					<div class="flex gap-1">
						{#each [['all','Все'],['44','44-ФЗ'],['223','223-ФЗ']] as [v,l]}
							<button
								onclick={() => f_law = v}
								class="flex-1 py-1 text-xs rounded-md border transition-all
									{f_law === v
										? 'bg-indigo-600 border-indigo-500 text-white'
										: 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600 hover:text-white'}"
							>{l}</button>
						{/each}
					</div>
				</div>

				<!-- Бюджет -->
				<div>
					<label class="text-xs text-gray-500 mb-1 block">НМЦ, ₽</label>
					<div class="flex gap-2">
						<input bind:value={f_budget_from} type="number" placeholder="от" class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-1.5 placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
						<input bind:value={f_budget_to}   type="number" placeholder="до" class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-1.5 placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
					</div>
				</div>

				<!-- Дата подачи -->
				{#if search_mode === 'tenders'}
					<div>
						<label class="text-xs text-gray-500 mb-1 block">Срок подачи</label>
						<div class="space-y-1.5">
							<input bind:value={f_date_from} type="date" class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-1.5 focus:outline-none focus:border-indigo-500" />
							<input bind:value={f_date_to}   type="date" class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-1.5 focus:outline-none focus:border-indigo-500" />
						</div>
					</div>
				{/if}

				<!-- Регион -->
				<div>
					<label class="text-xs text-gray-500 mb-1 block">Регион</label>
					<input bind:value={f_region} type="text" placeholder="Москва, СПб..." class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-3 py-1.5 placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
				</div>

				<!-- ОКПД2 -->
				{#if search_mode === 'tenders'}
					<div>
						<label class="text-xs text-gray-500 mb-1 block">ОКПД2</label>
						<input bind:value={f_okpd} type="text" placeholder="62.01, 62.02..." class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-3 py-1.5 placeholder-gray-600 focus:outline-none focus:border-indigo-500" />
					</div>
				{/if}

				<!-- Кнопка поиска -->
				<button
					onclick={search}
					disabled={loading}
					class="w-full py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-all"
				>
					{#if loading}
						<span class="animate-spin inline-block mr-1">⟳</span> Ищу...
					{:else}
						{search_mode === 'plans' ? '◎ Найти планы закупок' : '◎ Найти тендеры'}
					{/if}
				</button>

				{#if error}
					<div class="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-2">{error}</div>
				{/if}

			</div>
		</div>

		<!-- ── Центральная панель: список результатов ── -->
		<div class="w-80 shrink-0 border-r border-gray-800 overflow-y-auto flex flex-col">

			{#if !searched && !loading}
				<div class="flex flex-col items-center justify-center h-full text-center px-6 py-12">
					<div class="text-4xl mb-4 opacity-20">◎</div>
					<div class="text-sm text-gray-500">Введите ключевые слова и нажмите «Найти тендеры»</div>
					<div class="text-xs text-gray-600 mt-2">Поиск по 44-ФЗ, 223-ФЗ, ЕИС и другим источникам</div>
				</div>

			{:else if loading}
				<div class="flex flex-col items-center justify-center h-full">
					<div class="text-2xl animate-spin mb-3 text-indigo-400">⟳</div>
					<div class="text-sm text-gray-400">Ищу релевантные тендеры...</div>
					<div class="text-xs text-gray-600 mt-1">Проверяю ЕИС, фильтрую мусор</div>
				</div>

			{:else if results.length === 0}
				<div class="flex flex-col items-center justify-center h-full px-6 text-center">
					<div class="text-3xl mb-3 opacity-20">✕</div>
					<div class="text-sm text-gray-400">Ничего не найдено</div>
					<div class="text-xs text-gray-600 mt-1">Попробуйте изменить ключевые слова</div>
				</div>

			{:else}
				<div class="px-3 py-3 border-b border-gray-800 flex items-center justify-between shrink-0">
					<span class="text-xs text-gray-400">Найдено: <span class="text-white font-medium">{results.length}</span></span>
					<span class="text-xs text-gray-600">по релевантности</span>
				</div>

				{#if classifiers && (classifiers.okpd2 || classifiers.ktru_search || classifiers.error)}
					<div class="mx-3 mb-2 p-3 rounded-lg bg-gray-800/60 border border-gray-700/80 text-xs space-y-1.5 shrink-0">
						<div class="text-gray-400 font-medium">Мои-Закупки · справочники</div>
						{#if classifiers.error}
							<div class="text-red-400">{classifiers.error}</div>
						{/if}
						{#if classifiers.okpd2?.name}
							<div class="text-gray-300">
								<span class="text-gray-500">ОКПД-2:</span>
								{classifiers.okpd2.code || ''} — {classifiers.okpd2.name}
							</div>
						{/if}
						{#if classifiers.ktru_search?.results?.length}
							<div class="text-gray-500">Примеры КТРУ по запросу:</div>
							<ul class="list-disc pl-4 text-gray-400 space-y-0.5">
								{#each classifiers.ktru_search.results.slice(0, 5) as row}
									<li>{row.code} — {row.name || row.shortname || '—'}</li>
								{/each}
							</ul>
						{/if}
					</div>
				{/if}

				<div class="flex-1 overflow-y-auto divide-y divide-gray-800/60">
					{#each results as t}
						<button
							onclick={() => selectTender(t)}
							class="w-full text-left px-4 py-3.5 transition-all hover:bg-gray-800/50
								{selected?.id === t.id ? 'bg-indigo-900/30 border-l-2 border-indigo-500' : 'border-l-2 border-transparent'}"
						>
							<!-- Заголовок -->
							<div class="text-xs text-gray-200 font-medium leading-snug line-clamp-2 mb-2">{t.title}</div>

							<!-- Заказчик -->
							<div class="text-xs text-gray-500 truncate mb-2">{t.customer}</div>

							<!-- Метки -->
							<div class="flex flex-wrap gap-1.5 mb-2">
								<span class="text-xs px-1.5 py-0.5 rounded bg-indigo-900/60 text-indigo-300 font-medium">{t.law}</span>
								<span class="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">{t.source}</span>
								{#if t.region}
									<span class="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-500">{t.region}</span>
								{/if}
							</div>

							<!-- Бюджет и срок -->
							<div class="flex items-center justify-between">
								<span class="text-xs text-emerald-400 font-medium">{fmtMoney(t.budget)}</span>
								<div class="flex items-center gap-2">
									{#if daysLeft(t.deadline) !== null}
										<span class="text-xs {daysLeft(t.deadline) <= 7 ? 'text-red-400' : daysLeft(t.deadline) <= 14 ? 'text-yellow-400' : 'text-gray-500'}">
											{daysLeft(t.deadline) > 0 ? `${daysLeft(t.deadline)} д.` : 'Истёк'}
										</span>
									{/if}
									<span class="text-xs px-1.5 py-0.5 rounded font-medium {relevanceColor(t.relevance)}">{t.relevance}%</span>
								</div>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>

		<!-- ── Правая панель: детали тендера ── -->
		<div class="flex-1 overflow-hidden flex flex-col min-w-0">

			{#if !selected}
				<div class="flex flex-col items-center justify-center h-full text-center px-8">
					<div class="text-5xl mb-4 opacity-10">◆</div>
					<div class="text-sm text-gray-500">Выберите тендер из списка</div>
					<div class="text-xs text-gray-600 mt-2">Здесь будет подробная информация, документы и анализ агентов</div>
				</div>

			{:else}
				<!-- Шапка тендера -->
				<div class="px-6 py-4 border-b border-gray-800 shrink-0">
					<div class="flex items-start justify-between gap-4">
						<div class="flex-1 min-w-0">
							<div class="text-sm font-medium text-white leading-snug mb-1">{selected.title}</div>
							<div class="text-xs text-gray-400">{selected.customer}</div>
						</div>
						<div class="flex gap-2 shrink-0">
							<a href={selected.url} target="_blank" rel="noopener"
								class="text-xs px-2.5 py-1.5 rounded-lg bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition-all">
								↗ ЕИС
							</a>
						</div>
					</div>

					<!-- Ключевые цифры -->
					<div class="flex gap-4 mt-3">
						<div class="text-center">
							<div class="text-sm font-semibold text-emerald-400">{fmtMoney(selected.budget)}</div>
							<div class="text-xs text-gray-600">НМЦ</div>
						</div>
						<div class="text-center">
							<div class="text-sm font-semibold {daysLeft(selected.deadline) <= 7 ? 'text-red-400' : 'text-white'}">{fmtDate(selected.deadline)}</div>
							<div class="text-xs text-gray-600">Срок подачи</div>
						</div>
						<div class="text-center">
							<div class="text-sm font-semibold text-indigo-300">{selected.law}</div>
							<div class="text-xs text-gray-600">Закон</div>
						</div>
						<div class="text-center">
							<div class="text-sm font-semibold {relevanceColor(selected.relevance).split(' ')[0]}">{selected.relevance}%</div>
							<div class="text-xs text-gray-600">Релевантность</div>
						</div>
					</div>

					<!-- Вкладки деталей -->
					<div class="flex gap-1 mt-4">
						{#each [
							['doc', '📄 Описание'],
							['files', '📎 Документы' + (uploaded_files.length ? ` (${uploaded_files.length})` : '')],
							['tender_agent', '🎯 Тенд. спец'],
							['tech_agent', '⚙️ Тех. спец'],
						] as [id, label]}
							<button
								onclick={() => detail_tab = id}
								class="px-3 py-1 text-xs rounded-lg transition-all
									{detail_tab === id ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}"
							>{label}</button>
						{/each}
					</div>
				</div>

				<!-- Тело вкладки -->
				<div class="flex-1 overflow-y-auto px-6 py-5">

					<!-- Описание -->
					{#if detail_tab === 'doc'}
						{#if selected.doc_md}
							<div class="prose prose-sm prose-invert max-w-none">
								<pre class="text-xs text-gray-300 whitespace-pre-wrap font-sans">{selected.doc_md}</pre>
							</div>
						{:else}
							<div class="space-y-4">
								<div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
									<div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Краткое описание</div>
									<p class="text-sm text-gray-300 leading-relaxed">{selected.description}</p>
								</div>

								<div class="grid grid-cols-2 gap-3">
									<div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
										<div class="text-xs text-gray-500 mb-1">Опубликован</div>
										<div class="text-sm text-gray-200">{fmtDate(selected.published)}</div>
									</div>
									<div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
										<div class="text-xs text-gray-500 mb-1">ОКПД2</div>
										<div class="text-sm text-gray-200">{selected.okpd || '—'}</div>
									</div>
									<div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
										<div class="text-xs text-gray-500 mb-1">Регион</div>
										<div class="text-sm text-gray-200">{selected.region || '—'}</div>
									</div>
									<div class="bg-gray-900 rounded-xl p-4 border border-gray-800">
										<div class="text-xs text-gray-500 mb-1">Источник</div>
										<div class="text-sm text-gray-200">{selected.source}</div>
									</div>
								</div>

								<div class="bg-amber-900/20 border border-amber-800/40 rounded-xl p-4">
									<div class="text-xs text-amber-400 font-medium mb-1">Документация тендера</div>
									<div class="text-xs text-amber-300/70">Загрузите документы во вкладке «Документы» для полного анализа агентами</div>
								</div>
							</div>
						{/if}

					<!-- Документы -->
					{:else if detail_tab === 'files'}
						<div class="space-y-4">
							<!-- Зона загрузки -->
							<label class="block cursor-pointer">
								<div class="border-2 border-dashed border-gray-700 hover:border-indigo-500 rounded-xl p-8 text-center transition-all">
									<div class="text-2xl mb-2 opacity-40">📎</div>
									<div class="text-sm text-gray-400">Перетащите или нажмите для загрузки</div>
									<div class="text-xs text-gray-600 mt-1">PDF, DOCX, XLSX — тендерная документация, ТЗ, проекты контрактов</div>
									{#if upload_loading}
										<div class="mt-3 text-xs text-indigo-400 animate-pulse">Загружаю...</div>
									{/if}
								</div>
								<input type="file" multiple accept=".pdf,.docx,.doc,.xlsx,.xls" onchange={handleFileUpload} class="hidden" />
							</label>

							<!-- Список файлов -->
							{#if uploaded_files.length > 0}
								<div class="space-y-2">
									<div class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Загруженные файлы</div>
									{#each uploaded_files as f}
										<div class="flex items-center justify-between bg-gray-900 rounded-lg px-4 py-3 border border-gray-800">
											<div class="flex items-center gap-3">
												<span class="text-lg">
													{f.name.endsWith('.pdf') ? '📄' : f.name.endsWith('.docx') || f.name.endsWith('.doc') ? '📝' : '📊'}
												</span>
												<div>
													<div class="text-xs text-gray-200">{f.name}</div>
													<div class="text-xs text-gray-600">{fmtFileSize(f.size)}</div>
												</div>
											</div>
											<span class="text-xs text-green-400">✓ готов</span>
										</div>
									{/each}
								</div>

								<div class="flex gap-2">
									<button onclick={runTenderAgent}
										class="flex-1 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-all">
										🎯 Запустить тендерного спеца
									</button>
									<button onclick={runTechAgent}
										class="flex-1 py-2 bg-purple-700 hover:bg-purple-600 text-white text-xs font-medium rounded-lg transition-all">
										⚙️ Запустить тех. спеца
									</button>
								</div>
							{:else}
								<div class="text-xs text-gray-600 text-center py-4">Файлы не загружены</div>
							{/if}
						</div>

					<!-- Тендерный специалист -->
					{:else if detail_tab === 'tender_agent'}
						{#if agent_loading}
							<div class="flex flex-col items-center justify-center h-48">
								<div class="text-2xl animate-spin mb-3 text-indigo-400">⟳</div>
								<div class="text-sm text-gray-400">Тендерный специалист анализирует...</div>
							</div>
						{:else if tender_analysis}
							<div class="bg-gray-900 rounded-xl p-5 border border-gray-800">
								<pre class="text-xs text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">{tender_analysis}</pre>
							</div>
						{:else}
							<div class="flex flex-col items-center justify-center h-48 text-center">
								<div class="text-3xl mb-3 opacity-20">🎯</div>
								<div class="text-sm text-gray-400 mb-4">Тендерный специалист готов к анализу</div>
								<button onclick={runTenderAgent}
									class="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-all">
									Запустить анализ
								</button>
							</div>
						{/if}

					<!-- Технический специалист -->
					{:else if detail_tab === 'tech_agent'}
						{#if agent_loading}
							<div class="flex flex-col items-center justify-center h-48">
								<div class="text-2xl animate-spin mb-3 text-purple-400">⟳</div>
								<div class="text-sm text-gray-400">Технический специалист анализирует...</div>
							</div>
						{:else if tech_analysis}
							<div class="bg-gray-900 rounded-xl p-5 border border-gray-800">
								<pre class="text-xs text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">{tech_analysis}</pre>
							</div>
						{:else}
							<div class="flex flex-col items-center justify-center h-48 text-center">
								<div class="text-3xl mb-3 opacity-20">⚙️</div>
								<div class="text-sm text-gray-400 mb-1">Технический специалист</div>
								<div class="text-xs text-gray-600 mb-4">Сопоставит требования ТЗ с продуктами из базы знаний</div>
								<button onclick={runTechAgent}
									class="px-6 py-2 bg-purple-700 hover:bg-purple-600 text-white text-sm font-medium rounded-lg transition-all">
									Запустить анализ
								</button>
							</div>
						{/if}
					{/if}

				</div>
			{/if}
		</div>

	</div>

	<!-- ── Мои тендеры ── -->
	{:else if tab === 'my'}
		<div class="flex flex-col items-center justify-center h-full text-center px-8">
			<div class="text-5xl mb-4 opacity-10">◆</div>
			<div class="text-sm text-gray-500">Здесь будут тендеры, которые вы сохранили для работы</div>
			<div class="text-xs text-gray-600 mt-2">Функция в разработке</div>
		</div>

	<!-- ── Архив ── -->
	{:else if tab === 'archive'}
		<div class="flex flex-col items-center justify-center h-full text-center px-8">
			<div class="text-5xl mb-4 opacity-10">◈</div>
			<div class="text-sm text-gray-500">История участия в тендерах и результаты</div>
			<div class="text-xs text-gray-600 mt-2">Функция в разработке</div>
		</div>
	{/if}

</div>
