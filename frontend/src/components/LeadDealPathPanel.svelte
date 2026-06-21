<script>
	import { APPROVAL_LABELS_RU } from '$lib/leadApprovals.js';

	/**
	 * @type {{
	 *   dealPath?: { groups?: Array<Record<string, unknown>> },
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

	function groupVisible(g) {
		const stages = g.relatedStages || [];
		if (!stages.length) return true;
		return stages.includes(stage) || g.progress?.done < g.progress?.total;
	}

	function stepClass(done, isApproval) {
		if (done) return 'border-emerald-800/80 bg-emerald-950/30 text-emerald-100';
		if (isApproval) return 'border-gray-700 bg-gray-900/50 text-gray-300 hover:border-indigo-600/60';
		return 'border-amber-900/50 bg-amber-950/20 text-amber-100/90';
	}
</script>

<div class="rounded-xl border border-gray-800 bg-gray-900/40 p-4 space-y-4" data-testid="lead-deal-path">
	<div>
		<div class="text-sm font-medium text-white">Путь сделки</div>
		<p class="text-[11px] text-gray-500 mt-0.5">Квалификация и документы по порядку — отметь факты, двигай этап.</p>
	</div>

	{#each dealPath.groups || [] as group (group.id)}
		{#if groupVisible(group)}
			<div class="space-y-2" data-deal-path-group={group.id}>
				<div class="flex items-center justify-between gap-2">
					<div>
						<div class="text-xs font-medium text-gray-300">{group.title}</div>
						<div class="text-[10px] text-gray-600">{group.subtitle}</div>
					</div>
					<span class="text-[10px] tabular-nums text-gray-500 shrink-0">
						{group.progress?.done}/{group.progress?.total}
					</span>
				</div>
				<div class="flex flex-col gap-1">
					{#each group.steps as step, i (step.key + String(i))}
						{#if step.kind === 'approval'}
							<button
								type="button"
								class="flex items-center gap-2 w-full text-left text-xs rounded-lg border px-2.5 py-2 transition-colors {stepClass(step.done, true)}"
								onclick={() => onToggleApproval(step.key, !approvalsDraft[step.key])}
							>
								<span class="w-4 shrink-0 text-center">{step.done ? '✓' : '○'}</span>
								<span class="flex-1">{step.label || APPROVAL_LABELS_RU[step.key]}</span>
							</button>
						{:else if step.kind === 'derived'}
							<div
								class="flex items-center gap-2 text-xs rounded-lg border px-2.5 py-2 {stepClass(step.done, false)}"
								data-testid="deal-path-derived-{step.key}"
							>
								<span class="w-4 shrink-0 text-center">{step.done ? '✓' : '○'}</span>
								<span class="flex-1">{step.label}</span>
								{#if !step.done}
									<span class="text-[10px] text-amber-500/80">в контактах</span>
								{/if}
							</div>
						{:else}
							<div
								class="flex items-center gap-2 text-xs rounded-lg border px-2.5 py-2 {stepClass(step.done, false)}"
							>
								<span class="w-4 shrink-0 text-center">{step.done ? '✓' : '○'}</span>
								<span class="flex-1">{step.label}</span>
								{#if !step.done}
									<span class="text-[10px] text-amber-500/80">в карточке</span>
								{/if}
							</div>
						{/if}
					{/each}
				</div>
			</div>
		{/if}
	{/each}

	<button
		type="button"
		disabled={saving}
		onclick={onSave}
		class="w-full py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-100 disabled:opacity-50"
	>
		{saving ? 'Сохранение…' : 'Сохранить документы'}
	</button>
</div>
