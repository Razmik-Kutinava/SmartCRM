<script>
	import {
		PASSPORT_SECTIONS,
		formatPassportMoney,
		formatPassportStatus,
		passportActivityTypes,
		passportBranches,
		passportConnections,
		passportDebts,
		passportDirector,
		passportLicenses,
		passportReliability,
		passportSource,
		passportTaxes,
	} from '$lib/leads/leadPassport.js';

	/** @type {{ lead: Record<string, unknown> | null }} */
	let { lead = null } = $props();

	const src = $derived(passportSource(lead));
	const co = $derived(src.co);
	const fin = $derived(src.fin);
	const tech = $derived(src.tech);
	const risks = $derived(co.risk_flags || {});
	const reliability = $derived(passportReliability(co, fin));
	const activities = $derived(passportActivityTypes(co, lead));
	const branches = $derived(passportBranches(co));
	const connections = $derived(passportConnections(co));
	const licenses = $derived(passportLicenses(co, fin));
	const director = $derived(passportDirector(lead, co));
	const taxes = $derived(passportTaxes(fin));
	const debts = $derived(passportDebts(fin));

	function countFor(id) {
		const n = {
			contacts: (co.phones?.length || 0) + (co.emails?.length || 0),
			activities: activities.length,
			founders: co.founders?.length || 0,
			connections: connections.length,
			licenses: licenses.length,
			fedresurs: fin.fedresurs_count || 0,
			contracts: fin.contracts_count || 0,
			inspections: fin.inspection_count || 0,
			arbitration: fin.arbitration_count || 0,
			debts: debts.length,
			vacancies: (co.vacancies || []).length,
			history: (co.change_history || co.history || []).length,
			tech: tech.count || tech.all?.length || 0,
		}[id];
		return n > 0 ? n : null;
	}

	function websiteHref(w) {
		const s = String(w || '').replace(/^https?:\/\//, '');
		return s ? `https://${s}` : '#';
	}
</script>

<div class="space-y-4" data-testid="lead-passport">
	<p class="text-xs text-gray-500">
		Паспорт клиента — источник правды по компании. Данные из Checko и обогащения; пустые разделы заполняются по кнопке ✨.
	</p>

	<nav class="flex flex-wrap gap-1.5 pb-2 border-b border-gray-800" data-testid="lead-passport-nav">
		{#each PASSPORT_SECTIONS as sec}
			{@const cnt = countFor(sec.id)}
			<a
				href="#passport-{sec.id}"
				class="text-[11px] px-2 py-1 rounded-full border border-gray-800 bg-gray-950 text-gray-400 hover:text-white hover:border-gray-600 transition-colors"
			>
				{sec.label}{#if cnt}<span class="text-indigo-400 ml-0.5">{cnt}</span>{/if}
			</a>
		{/each}
	</nav>

	<!-- Общая информация -->
	<section id="passport-general" class="passport-section" data-testid="passport-section-general">
		<h3 class="passport-title">Общая информация</h3>
		<div class="passport-grid">
			{#each [
				['Компания', lead?.company],
				['Краткое название', co.name_short],
				['Статус', formatPassportStatus(co.status)],
				['Дата регистрации', co.registration_date],
				['Адрес', co.address || lead?.city],
				['Город', co.city || lead?.city],
				['Сотрудников', co.employees_count ?? lead?.employees],
				['МСП', co.smb_category],
				['Тип управления', co.management_type],
				['Отрасль (CRM)', lead?.industry],
			].filter(([, v]) => v != null && v !== '' && v !== '—') as [label, value]}
				<div class="passport-row"><span class="passport-label">{label}</span><span class="passport-value">{value}</span></div>
			{/each}
		</div>
		{#if !lead?.company && !co.address}
			<p class="passport-empty">Нет данных</p>
		{/if}
	</section>

	<!-- Надёжность -->
	<section id="passport-reliability" class="passport-section" data-testid="passport-section-reliability">
		<h3 class="passport-title">Надёжность</h3>
		<div class="flex items-center gap-3 mb-2">
			<span class="text-2xl font-bold text-white">{reliability.score}</span>
			<span class="text-sm text-gray-400">/ 100</span>
			<span class="text-xs px-2 py-0.5 rounded-full {reliability.score >= 70 ? 'bg-emerald-900/50 text-emerald-300' : reliability.score >= 40 ? 'bg-amber-900/50 text-amber-300' : 'bg-red-900/50 text-red-300'}">{reliability.tier}</span>
		</div>
		{#if reliability.flags.length}
			<ul class="text-xs text-gray-400 space-y-1">
				{#each reliability.flags as f}<li>· {f}</li>{/each}
			</ul>
		{:else}
			<p class="text-xs text-gray-500">Критичных рисков не выявлено по имеющимся данным.</p>
		{/if}
	</section>

	<!-- Реквизиты -->
	<section id="passport-requisites" class="passport-section" data-testid="passport-section-requisites">
		<h3 class="passport-title">Реквизиты</h3>
		<div class="passport-grid">
			{#each [['ИНН', lead?.inn], ['ОГРН', lead?.ogrn], ['КПП', co.kpp], ['Дата ОГРН', co.registration_date]].filter(([, v]) => v) as [label, value]}
				<div class="passport-row"><span class="passport-label">{label}</span><span class="passport-value font-mono">{value}</span></div>
			{/each}
		</div>
		{#if !lead?.inn}<p class="passport-empty">Укажите ИНН или обогатите карточку (✨)</p>{/if}
	</section>

	<!-- Контакты -->
	<section id="passport-contacts" class="passport-section" data-testid="passport-section-contacts">
		<h3 class="passport-title">Контакты {#if countFor('contacts')}<span class="text-gray-500 font-normal">({countFor('contacts')})</span>{/if}</h3>
		<div class="space-y-1.5 text-sm">
			{#if lead?.website && lead.website !== '—'}
				<div class="passport-row"><span class="passport-label">Сайт</span><a href={websiteHref(lead.website)} target="_blank" rel="noopener" class="text-indigo-400 hover:underline text-xs">{lead.website}</a></div>
			{/if}
			{#each co.phones || [] as ph}
				<div class="passport-row"><span class="passport-label">Телефон</span><a href="tel:{ph}" class="text-green-400 font-mono text-xs">{ph}</a></div>
			{/each}
			{#each co.emails || [] as em}
				<div class="passport-row"><span class="passport-label">Email</span><span class="text-gray-300 font-mono text-xs">{em}</span></div>
			{/each}
		</div>
		{#if !countFor('contacts') && (!lead?.website || lead.website === '—')}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Виды деятельности -->
	<section id="passport-activities" class="passport-section" data-testid="passport-section-activities">
		<h3 class="passport-title">Виды деятельности {#if activities.length}<span class="text-gray-500 font-normal">({activities.length})</span>{/if}</h3>
		{#if activities.length}
			{#each activities as a}
				<div class="text-xs py-1 border-b border-gray-800/80">
					<span class="text-indigo-400 font-mono">{a.code}</span>
					{#if a.primary}<span class="ml-1 text-[10px] text-emerald-500">основной</span>{/if}
					{#if a.name}<div class="text-gray-400 mt-0.5">{a.name}</div>{/if}
				</div>
			{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Финансы -->
	<section id="passport-financials" class="passport-section" data-testid="passport-section-financials">
		<h3 class="passport-title">Финансовая отчётность {fin.finance_year ? `(${fin.finance_year} г.)` : ''}</h3>
		{#if fin.revenue || fin.profit}
			<div class="passport-grid">
				{#each [['Выручка', fin.revenue], ['Прибыль', fin.profit], ['Активы', fin.assets], ['Расходы', fin.expense], ['Кред. задолж.', fin.debt]].filter(([, v]) => v != null) as [l, v]}
					<div class="passport-row"><span class="passport-label">{l}</span><span class="passport-value">{formatPassportMoney(v)}</span></div>
				{/each}
			</div>
			{#if fin.revenue_series?.length}
				<div class="mt-2 flex flex-wrap gap-3 text-xs text-gray-500">
					{#each fin.revenue_series as [yr, rev]}<span>{yr}: <span class="text-gray-300">{formatPassportMoney(rev)}</span></span>{/each}
				</div>
			{/if}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Налоги -->
	<section id="passport-taxes" class="passport-section" data-testid="passport-section-taxes">
		<h3 class="passport-title">Налоги и сборы</h3>
		{#if taxes.length}
			{#each taxes as [l, v]}<div class="passport-row text-sm"><span class="passport-label">{l}</span><span class="passport-value">{v}</span></div>{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Руководитель -->
	<section id="passport-director" class="passport-section" data-testid="passport-section-director">
		<h3 class="passport-title">Руководитель</h3>
		{#if director}
			<div class="text-sm"><span class="text-white">{director.name}</span>{#if director.post}<span class="text-gray-500 ml-2">· {director.post}</span>{/if}</div>
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Учредители -->
	<section id="passport-founders" class="passport-section" data-testid="passport-section-founders">
		<h3 class="passport-title">Учредитель {#if co.founders?.length}<span class="text-gray-500 font-normal">({co.founders.length})</span>{/if}</h3>
		{#if co.founders?.length}
			{#each co.founders as f}
				<div class="flex justify-between text-xs py-1 border-b border-gray-800/80">
					<span class="text-gray-300">{f.name}</span>
					<span class="text-gray-600 shrink-0 ml-2">{f.type === 'LEGAL' ? '🏢' : '👤'} {f.share_percent != null ? `${f.share_percent}%` : ''}{#if f.inn} · {f.inn}{/if}</span>
				</div>
			{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Филиалы -->
	<section id="passport-branches" class="passport-section" data-testid="passport-section-branches">
		<h3 class="passport-title">Филиалы {#if branches.length}<span class="text-gray-500 font-normal">({co.branch_count ?? branches.length})</span>{/if}</h3>
		{#if branches.length}
			{#each branches as b}
				<div class="text-xs py-1"><span class="text-gray-300">{b.name}</span>{#if b.address}<div class="text-gray-600">{b.address}</div>{/if}</div>
			{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Связи -->
	<section id="passport-connections" class="passport-section" data-testid="passport-section-connections">
		<h3 class="passport-title">Связи {#if connections.length}<span class="text-indigo-400 font-normal">({connections.length})</span>{/if}</h3>
		{#if connections.length}
			<div class="space-y-2">
				{#each connections as c}
					<div class="rounded-lg border border-purple-900/30 bg-gray-950/80 p-3 text-xs space-y-1">
						<div class="text-gray-200 font-medium">{c.name}</div>
						<div class="text-gray-500 flex flex-wrap gap-x-3 gap-y-0.5">
							{#if c.inn}<span>ИНН <span class="text-gray-400 font-mono">{c.inn}</span></span>{/if}
							{#if c.ogrn}<span>ОГРН <span class="text-gray-400 font-mono">{c.ogrn}</span></span>{/if}
							{#if c.status}<span>{c.status}</span>{/if}
						</div>
						{#if c.okved}<div class="text-gray-600">ОКВЭД: {c.okved}</div>{/if}
						{#if c.address}<div class="text-gray-600">{c.address}</div>{/if}
						<div class="text-purple-400/80">{c.relation}</div>
					</div>
				{/each}
			</div>
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Лицензии -->
	<section id="passport-licenses" class="passport-section" data-testid="passport-section-licenses">
		<h3 class="passport-title">Лицензии {#if licenses.length}<span class="text-gray-500 font-normal">({licenses.length})</span>{/if}</h3>
		{#if licenses.length}
			{#each licenses as lic}<div class="text-xs text-gray-400 py-0.5">· {lic}</div>{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Федресурс -->
	<section id="passport-fedresurs" class="passport-section" data-testid="passport-section-fedresurs">
		<h3 class="passport-title">Федресурс {#if fin.fedresurs_count}<span class="text-orange-400 font-normal">({fin.fedresurs_count})</span>{/if}</h3>
		{#if fin.fedresurs_messages?.length}
			{#each fin.fedresurs_messages as m}
				<div class="text-xs py-1 border-b border-gray-800"><span class="text-orange-400">{m.type}</span> · {m.date}{#if m.text}<div class="text-gray-500 line-clamp-2">{m.text}</div>{/if}</div>
			{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Госзакупки -->
	<section id="passport-contracts" class="passport-section" data-testid="passport-section-contracts">
		<h3 class="passport-title">Госзакупки {#if fin.contracts_count}<span class="text-green-400 font-normal">({fin.contracts_count})</span>{/if}</h3>
		{#if fin.contracts?.length}
			{#each fin.contracts as c}
				<div class="text-xs py-1 border-b border-gray-800"><div class="text-gray-300">{c.subject || c.number}</div><div class="text-green-400">{formatPassportMoney(c.amount)} · {c.date}</div></div>
			{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Проверки -->
	<section id="passport-inspections" class="passport-section" data-testid="passport-section-inspections">
		<h3 class="passport-title">Проверки и КНМ {#if fin.inspection_count}<span class="text-gray-500 font-normal">({fin.inspection_count})</span>{/if}</h3>
		{#if fin.inspections?.length}
			{#each fin.inspections as i}
				<div class="text-xs py-1 border-b border-gray-800"><div class="text-gray-400">{i.authority}</div><div class="text-gray-600">{i.date}{#if i.violations} · Нарушения{/if}</div></div>
			{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Арбитраж -->
	<section id="passport-arbitration" class="passport-section" data-testid="passport-section-arbitration">
		<h3 class="passport-title">Арбитражные дела {#if fin.arbitration_count}<span class="text-yellow-400 font-normal">({fin.arbitration_count})</span>{/if}</h3>
		{#if fin.arbitration_cases?.length}
			{#each fin.arbitration_cases as c}
				<div class="text-xs py-1 border-b border-gray-800"><span class="text-gray-400">{c.number}</span>{#if c.amount}<span class="text-yellow-400 ml-2">{formatPassportMoney(c.amount)}</span>{/if}</div>
			{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Долги -->
	<section id="passport-debts" class="passport-section" data-testid="passport-section-debts">
		<h3 class="passport-title">Долги</h3>
		{#if debts.length}
			{#each debts as d}
				<div class="text-xs py-1 flex justify-between gap-2 border-b border-gray-800"><span class="text-gray-400">{d.label}</span><span class="text-red-400 shrink-0">{formatPassportMoney(d.amount)}{#if d.date} · {d.date}{/if}</span></div>
			{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Вакансии -->
	<section id="passport-vacancies" class="passport-section" data-testid="passport-section-vacancies">
		<h3 class="passport-title">Вакансии</h3>
		{#if co.vacancies?.length}
			{#each co.vacancies as v}<div class="text-xs text-gray-400 py-0.5">{v.title || v}</div>{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- История -->
	<section id="passport-history" class="passport-section" data-testid="passport-section-history">
		<h3 class="passport-title">История изменений</h3>
		{#if co.change_history?.length || co.history?.length}
			{#each co.change_history || co.history as h}
				<div class="text-xs py-1 text-gray-400">{h.date || ''} {h.text || h}</div>
			{/each}
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>

	<!-- Технологии (из Checko/лидогена) -->
	<section id="passport-tech" class="passport-section" data-testid="passport-section-tech">
		<h3 class="passport-title">Технологии {#if tech.count}<span class="text-gray-500 font-normal">({tech.count})</span>{/if}</h3>
		{#if tech.crm?.length}<div class="text-xs text-indigo-400 mb-1">CRM: {tech.crm.join(', ')}</div>{/if}
		{#if tech.all?.length}
			<div class="flex flex-wrap gap-1">{#each tech.all as t}<span class="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">{t}</span>{/each}</div>
		{:else}<p class="passport-empty">Нет данных</p>{/if}
	</section>
</div>

<style>
	.passport-section {
		scroll-margin-top: 5rem;
		@apply bg-gray-950 rounded-xl border border-gray-800 p-4;
	}
	.passport-title {
		@apply text-sm font-medium text-gray-300 mb-3;
	}
	.passport-grid {
		@apply grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5 text-sm;
	}
	.passport-row {
		@apply flex justify-between gap-2;
	}
	.passport-label {
		@apply text-gray-500 shrink-0 text-xs;
	}
	.passport-value {
		@apply text-gray-300 text-right text-xs;
	}
	.passport-empty {
		@apply text-xs text-gray-600 italic;
	}
</style>
