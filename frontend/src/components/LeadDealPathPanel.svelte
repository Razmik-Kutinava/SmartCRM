<script>
	import { APPROVAL_LABELS_RU } from '$lib/leadApprovals.js';
	import {
		dealPathNextStep,
		dealPathTotals,
		isDealPathGroupActive,
	} from '$lib/leads/leadDealPathUi.js';

	/**
	 * @type {{
	 *   dealPath?: { groups?: Array<Record<string, unknown>>, nextStep?: Record<string, unknown> | null },
	 *   approvalsDraft: Record<string, boolean>,
	 *   onToggleApproval: (key: string, checked: boolean) => void,
	 *   onSave: () => void,
	 *   saving?: boolean,
	 *   stage?: string,
	 * }}
	 */
	let {
		dealPath = { groups: [] },
		approvalsDraft,
		onToggleApproval,
		onSave,
		saving = false,
		stage = '',
	} = $props();

	const nextStep = $derived(dealPathNextStep(dealPath));
	const totals = $derived(dealPathTotals(dealPath));

	function stepClass(done, isApproval) {
		if (done) return 'border-emerald-800/60 bg-emerald-950/20 text-emerald-200/90';
		if (isApproval) return 'border-gray-800 bg-gray-950/40 text-gray-400';
		return 'border-amber-900/40 bg-amber-950/15 text-amber-100/80';
	}

	function chipClass(group) {
		const done = group.progress?.done ?? 0;
		const total = group.progress?.total ?? 0;
		if (done >= total && total > 0) {
			return 'border-emerald-800/70 bg-emerald-950/30 text-emerald-300';
		}
		if (isDealPathGroupActive(stage, group)) {
			return 'border-indigo-700/60 bg-indigo-950/30 text-indigo-200';
		}
		return 'border-gray-800 bg-gray-950/50 text-gray-500';
	}

	async function markNextDone() {
		if (!nextStep || nextStep.kind !== 'approval') return;
		onToggleApproval(nextStep.key, true);
		await onSave();
	}

	function toggleInAccordion(step) {
		if (step.kind !== 'approval') return;
		onToggleApproval(step.key, !approvalsDraft[step.key]);
	}
</script>

<div class="rounded-xl border border-gray-800 bg-gray-900/40 p-3 space-y-3" data-testid="lead-deal-path">
	<div class="text-sm font-medium text-white">Путь сделки</div>

	<div class="flex flex-wrap gap-1.5" data-testid="lead-deal-path-chips">
		{#each dealPath.groups || [] as group (group.id)}
			<span class="text-[10px] tabular-nums px-2 py-0.5 rounded-full border {chipClass(group)}">
				{group.title} {group.progress?.done}/{group.progress?.total}
			</span>
		{/each}
	</div>

	{#if dealPath && (dealPath.groups || []).length > 0}
		{#if nextStep}
			<div
				class="rounded-lg border border-indigo-800/50 bg-indigo-950/25 px-3 py-2.5 space-y-2"
				data-testid="lead-deal-path-next"
			>
				<div class="text-[10px] uppercase tracking-wide text-indigo-300/90">Следующий шаг</div>
				<div class="text-sm font-medium text-white leading-snug">{nextStep.label}</div>
				<div class="text-[10px] text-gray-500">{nextStep.groupTitle}</div>
				{#if nextStep.kind === 'approval'}
					<button
						type="button"
						disabled={saving}
						onclick={markNextDone}
						class="text-xs px-3 py-1.5 rounded-lg bg-indigo-700 hover:bg-indigo-600 text-white disabled:opacity-50"
					>
						{saving ? 'Сохранение…' : '✓ Отметить выполненным'}
					</button>
				{:else if nextStep.kind === 'derived'}
					<p class="text-[11px] text-amber-400/90">Добавь контакт с ролью ЛПР справа в карточке.</p>
				{:else}
					<p class="text-[11px] text-amber-400/90">Заполни поле в карточке справа.</p>
				{/if}
			</div>
		{:else}
			<p class="text-xs text-emerald-400" data-testid="lead-deal-path-complete">Все шаги пройдены ✓</p>
		{/if}
	{:else}
		<p class="text-xs text-amber-400" data-testid="lead-deal-path-empty">Путь сделки не задан</p>
	{/if}

	<details class="group text-xs" data-testid="lead-deal-path-accordion">
		<summary class="cursor-pointer select-none text-gray-500 hover:text-gray-300 list-none flex items-center gap-1">
			<span class="text-gray-600 group-open:rotate-90 transition-transform">▸</span>
			Все документы ({totals.done}/{totals.total})
		</summary>
		<div class="mt-2 space-y-2 pl-1 border-l border-gray-800 ml-1">
			{#each dealPath.groups || [] as group (group.id)}
				<details
					class="pl-2"
					open={isDealPathGroupActive(stage, group) && (group.progress?.done ?? 0) < (group.progress?.total ?? 0)}
				>
					<summary class="cursor-pointer select-none text-gray-400 hover:text-gray-200 py-0.5">
						{group.title}
						<span class="text-gray-600 tabular-nums ml-1">{group.progress?.done}/{group.progress?.total}</span>
					</summary>
					<div class="mt-1 flex flex-col gap-0.5 pb-1">
						{#each group.steps as step, i (step.key + String(i))}
							{#if step.kind === 'approval'}
								<button
									type="button"
									class="flex items-center gap-2 w-full text-left text-[11px] rounded px-2 py-1 border {stepClass(step.done, true)}"
									onclick={() => toggleInAccordion(step)}
								>
									<span class="w-3 shrink-0 text-center">{step.done ? '✓' : '○'}</span>
									<span class="flex-1 truncate">{step.label || APPROVAL_LABELS_RU[step.key]}</span>
								</button>
							{:else}
								<div
									class="flex items-center gap-2 text-[11px] rounded px-2 py-1 border {stepClass(step.done, false)}"
								>
									<span class="w-3 shrink-0 text-center">{step.done ? '✓' : '○'}</span>
									<span class="flex-1 truncate">{step.label}</span>
								</div>
							{/if}
						{/each}
					</div>
				</details>
			{/each}
			<button
				type="button"
				disabled={saving}
				onclick={onSave}
				class="w-full py-1 rounded text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-50"
			>
				{saving ? 'Сохранение…' : 'Сохранить изменения'}
			</button>
		</div>
	</details>
</div>
