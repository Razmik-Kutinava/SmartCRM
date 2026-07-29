<script>
	/**
	 * Вкладка Клиент → Карточка (Апрув 1: каркас порядка блоков).
	 * Паспорт — отдельная вкладка, сюда не входит.
	 */
	import LeadContactsPanel from './LeadContactsPanel.svelte';
	import LeadContactsReadonlyList from './LeadContactsReadonlyList.svelte';
	import LeadBitrixExtraPanel from './LeadBitrixExtraPanel.svelte';
	import LeadScoreAdvisoryPanel from './LeadScoreAdvisoryPanel.svelte';
	import { formatDealAmountLabel } from '$lib/leads/leadCardMoney.js';
	import { isIndustryEmpty } from '$lib/leads/industryCatalog.js';
	import { cardAddressFromLead, cardOkvedLineFromLead } from '$lib/leads/leadClientCardMeta.js';

	let {
		lead,
		detailsDraft = $bindable(),
		contactsDraft = $bindable(),
		moneyAmountStr = $bindable(''),
		moneyPaidStr = $bindable(''),
		industryOptions = [],
		detailsSaving = false,
		contactsSaving = false,
		moneySaving = false,
		onSaveDetails,
		onSaveContacts,
		onSaveMoney,
		onOpenIndustry,
		onWriteEmail,
		onOpenAgents,
	} = $props();

	let extraOpen = $state(false);
	let researchOpen = $state(false);

	const addressLine = $derived(cardAddressFromLead(lead));
	const okvedLine = $derived(cardOkvedLineFromLead(lead));
	const webResearch = $derived(lead?.checko?.analyses?.web_research || null);
</script>

<div class="min-w-0" data-testid="lead-card-overview-card">
	<div class="space-y-5 min-w-0" data-testid="lead-card-overview-center">
		<!-- 1. Компания -->
		<section class="space-y-2" data-testid="lead-card-section-company">
			<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Компания</div>
			<label class="block text-sm">
				<span class="text-gray-500 text-xs">Организация</span>
				<input
					bind:value={detailsDraft.company}
					class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
					data-testid="lead-card-company"
				/>
			</label>
			<label class="block text-sm">
				<span class="text-gray-500 text-xs">Город</span>
				<input
					bind:value={detailsDraft.city}
					class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
					data-testid="lead-card-city"
				/>
			</label>
			{#if addressLine}
				<div class="text-sm" data-testid="lead-card-address-readonly">
					<span class="text-gray-500 text-xs">Адрес (из паспорта / Checko)</span>
					<div class="mt-0.5 text-gray-300 text-sm">{addressLine}</div>
				</div>
			{/if}
		</section>

		<!-- 2. Контакты -->
		<section class="space-y-2 text-sm" data-testid="lead-card-section-contacts">
			<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Контакты</div>
			<LeadContactsReadonlyList contacts={lead?.contacts || []} />
			<LeadContactsPanel
				contacts={contactsDraft}
				onChange={(c) => {
					contactsDraft = c;
				}}
				onSave={onSaveContacts}
				saving={contactsSaving}
			/>
		</section>

		<!-- 3. Сайт -->
		<section class="space-y-2" data-testid="lead-card-section-website">
			<label class="block text-sm">
				<span class="text-gray-500 text-xs">Сайт / домен</span>
				<input
					bind:value={detailsDraft.website}
					class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
					placeholder="например ridan.ru"
					data-testid="lead-card-website"
				/>
			</label>
			<p class="text-[11px] text-gray-600">Проверка «живой / мёртвый» — в следующем апруве.</p>
		</section>

		<!-- 4. Отрасль / ОКВЭД -->
		<section class="space-y-2" data-testid="lead-card-section-industry">
			<label class="block text-sm">
				<span class="text-gray-500 text-xs">Отрасль</span>
				<div class="flex gap-1 mt-0.5">
					<input
						list="lead-card-industries"
						bind:value={detailsDraft.industry}
						class="flex-1 bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
						data-testid="lead-card-industry"
					/>
					{#if lead?.industryVerified}
						<span class="shrink-0 px-1.5 py-1 text-[10px] rounded bg-emerald-900/50 text-emerald-300" title="Проверено">✓</span>
					{/if}
				</div>
				<datalist id="lead-card-industries">
					{#each industryOptions as opt (opt)}<option value={opt}></option>{/each}
				</datalist>
				{#if isIndustryEmpty(lead?.industry)}
					<button
						type="button"
						class="mt-1 text-[11px] text-amber-400 hover:underline"
						onclick={onOpenIndustry}
						data-testid="lead-industry-prompt"
					>Указать отрасль</button>
				{/if}
			</label>
			{#if okvedLine}
				<div class="text-sm" data-testid="lead-card-okved-readonly">
					<span class="text-gray-500 text-xs">ОКВЭД</span>
					<div class="mt-0.5 text-gray-300 text-sm">{okvedLine}</div>
				</div>
			{:else}
				<p class="text-[11px] text-gray-600" data-testid="lead-card-okved-empty">
					ОКВЭД появится после обогащения / исследования (апрув 4).
				</p>
			{/if}
		</section>

		<!-- 5. Сотрудники -->
		<section class="space-y-2" data-testid="lead-card-section-employees">
			<label class="block text-sm">
				<span class="text-gray-500 text-xs">Сотрудники</span>
				<input
					bind:value={detailsDraft.employees}
					class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
					data-testid="lead-card-employees"
				/>
			</label>
		</section>

		<!-- 6. Обороты с нами -->
		<section class="space-y-2" data-testid="lead-card-section-turnover">
			<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Обороты с нами</div>
			{#if formatDealAmountLabel(lead)}
				<div class="text-sm text-gray-300" data-testid="lead-card-deal-amount-panel">
					<span class="text-gray-500 text-xs">Сумма (Битрикс)</span>
					<div class="text-amber-200/90 font-medium mt-0.5">{formatDealAmountLabel(lead)}</div>
					<p class="text-[11px] text-gray-600 mt-0.5">Источник: Битрикс</p>
				</div>
			{/if}
			<div class="text-xs text-gray-500 uppercase tracking-wide font-medium pt-1">В рублях (менеджер)</div>
			<div class="space-y-2 text-sm">
				<label class="block">
					<span class="text-gray-500 text-xs">Сумма договора / сделки</span>
					<input
						type="text"
						inputmode="decimal"
						bind:value={moneyAmountStr}
						class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
						placeholder="например 1250000"
					/>
				</label>
				<label class="block">
					<span class="text-gray-500 text-xs">Оплачено</span>
					<input
						type="text"
						inputmode="decimal"
						bind:value={moneyPaidStr}
						class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
						placeholder="0"
					/>
				</label>
				<label class="block">
					<span class="text-gray-500 text-xs">Уже купили (по строке)</span>
					<textarea
						bind:value={detailsDraft.productsOwnedText}
						rows="2"
						class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm resize-y"
						placeholder="MaxPatrol VM&#10;OpManager"
						data-testid="lead-card-products-owned"
					></textarea>
				</label>
				<button
					type="button"
					disabled={moneySaving}
					onclick={onSaveMoney}
					class="w-full py-1.5 rounded-lg text-xs font-medium bg-emerald-900/60 hover:bg-emerald-800/70 text-emerald-100 disabled:opacity-50"
				>
					{moneySaving ? 'Сохранение…' : 'Сохранить суммы'}
				</button>
			</div>
		</section>

		<!-- 7. Выводы агентов (placeholder до апрува 5) -->
		<section class="space-y-2" data-testid="lead-card-section-agents">
			<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Выводы агентов</div>
			<div class="rounded-lg border border-dashed border-gray-800 bg-gray-950/40 px-3 py-3 text-sm text-gray-500">
				<p data-testid="lead-card-agents-placeholder">
					После запуска в плитке «Агенты» выводы появятся здесь (апрув 5).
				</p>
				{#if onOpenAgents}
					<button
						type="button"
						class="mt-2 text-[11px] text-indigo-400 hover:underline"
						onclick={onOpenAgents}
						data-testid="lead-card-open-agents"
					>Открыть агентов</button>
				{/if}
			</div>
		</section>

		<!-- Сохранить карточку + доп. поля -->
		<section class="space-y-2 text-sm" data-testid="lead-card-section-save">
			{#if lead?.email && lead.email !== '—'}
				<button
					type="button"
					class="text-xs text-indigo-400 hover:text-indigo-300 text-left"
					onclick={() => onWriteEmail?.(lead.email)}
				>✉ Написать на {lead.email}</button>
			{/if}
			<button
				type="button"
				disabled={detailsSaving}
				onclick={onSaveDetails}
				class="w-full py-1.5 rounded-lg text-xs font-medium bg-indigo-900/60 hover:bg-indigo-800/70 text-indigo-100 disabled:opacity-50"
			>
				{detailsSaving ? 'Сохранение…' : 'Сохранить карточку'}
			</button>
			<button
				type="button"
				class="flex w-full items-center justify-between text-left text-xs text-gray-500 hover:text-gray-300"
				onclick={() => {
					extraOpen = !extraOpen;
				}}
				aria-expanded={extraOpen}
				data-testid="lead-card-extra-toggle"
			>
				<span>Дополнительно (скоринг, бюджет, заметка…)</span>
				<span class="text-[10px]">{extraOpen ? '▲' : '▼'}</span>
			</button>
			{#if extraOpen}
				<div class="space-y-2 border border-gray-800 rounded-lg p-3" data-testid="lead-card-extra-fields">
					<label class="block">
						<span class="text-gray-500 text-xs">Скоринг (0–100, временно ручной)</span>
						<input
							bind:value={detailsDraft.scoreStr}
							inputmode="numeric"
							class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
						/>
					</label>
					<label class="block">
						<span class="text-gray-500 text-xs">Бюджет (текст)</span>
						<input
							bind:value={detailsDraft.budget}
							class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
						/>
					</label>
					<label class="block">
						<span class="text-gray-500 text-xs">Следующий звонок</span>
						<input
							bind:value={detailsDraft.nextCall}
							class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm"
						/>
					</label>
					<label class="block">
						<span class="text-gray-500 text-xs">Описание / заметка</span>
						<textarea
							bind:value={detailsDraft.description}
							rows="3"
							class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-gray-200 text-sm resize-y"
						></textarea>
					</label>
				</div>
			{/if}
		</section>

		<!-- 8. Системные -->
		<section class="space-y-2" data-testid="lead-card-section-system">
			<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Системные поля</div>
			<div class="space-y-2 text-sm">
				{#each [
					['Источник', lead?.source],
					['Ответственный', lead?.responsible],
					['Создан', lead?.created],
				] as [label, value]}
					<div class="flex justify-between gap-2">
						<span class="text-gray-500 shrink-0">{label}</span>
						<span class="text-gray-300 text-right">{value}</span>
					</div>
				{/each}
			</div>
			<LeadScoreAdvisoryPanel scoreAdvisory={lead?.scoreAdvisory} />
		</section>

		<!-- Хвост: исследование + сырые UF -->
		<section class="space-y-2" data-testid="lead-card-section-bitrix-uf">
			{#if webResearch}
				<div class="space-y-2" data-testid="lead-card-web-research">
					<button
						type="button"
						class="flex w-full items-center justify-between gap-2 text-left text-xs text-gray-500 uppercase tracking-wide font-medium hover:text-gray-300"
						onclick={() => {
							researchOpen = !researchOpen;
						}}
						aria-expanded={researchOpen}
						data-testid="lead-card-web-research-toggle"
					>
						<span>Исследование (веб){webResearch.at ? ` · ${webResearch.at}` : ''}</span>
						<span class="text-[10px] normal-case text-gray-600">{researchOpen ? '▲' : '▼'}</span>
					</button>
					{#if researchOpen}
						<div class="rounded-lg border border-gray-800 bg-gray-950/40 p-3 space-y-2 text-sm">
							{#if webResearch.summary}
								<pre class="whitespace-pre-wrap text-gray-300 text-xs leading-relaxed max-h-64 overflow-y-auto" data-testid="lead-card-web-research-summary">{webResearch.summary}</pre>
							{/if}
							{#if webResearch.providers_used?.length}
								<p class="text-[11px] text-gray-600">Провайдеры: {webResearch.providers_used.join(', ')}</p>
							{/if}
							{#if webResearch.raw_results?.length}
								<details class="text-[11px] text-gray-500">
									<summary class="cursor-pointer hover:text-gray-300">Сырые результаты ({webResearch.raw_results.length})</summary>
									<ul class="mt-2 space-y-2 max-h-48 overflow-y-auto font-mono">
										{#each webResearch.raw_results as hit, i (hit.url || i)}
											<li class="border-t border-gray-800/80 pt-2">
												<div class="text-violet-300/80 break-all">{hit.title || hit.url}</div>
												{#if hit.url}<a class="text-indigo-400 hover:underline break-all" href={hit.url} target="_blank" rel="noreferrer">{hit.url}</a>{/if}
												{#if hit.snippet}<div class="text-gray-500 mt-0.5">{hit.snippet}</div>{/if}
											</li>
										{/each}
									</ul>
								</details>
							{/if}
						</div>
					{/if}
				</div>
			{/if}
			<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Битрикс (служебное)</div>
			<LeadBitrixExtraPanel {lead} />
		</section>
	</div>
</div>
