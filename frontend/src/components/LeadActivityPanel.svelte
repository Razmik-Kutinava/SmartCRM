<script>
	import { ACTIVITY_TYPES } from '$lib/leads/leadActivityTypes.js';
	import {
		buildActivityTimeline,
		datetimeLocalToIso,
		formatActivityWhen,
		nowDatetimeLocalValue,
	} from '$lib/leads/leadActivityTimeline.js';
	import { auditFieldLabel, formatAuditValue, isAuditRowHidden } from '$lib/leads/leadAudit.js';
	import { createLeadCommunication } from '$lib/leads/leadCommunications.js';

	/**
	 * @type {{
	 *   leadId: number | string,
	 *   communications?: unknown[],
	 *   comments?: unknown[],
	 *   audit?: unknown[],
	 *   onSaved: () => void | Promise<void>,
	 * }}
	 */
	let { leadId, communications = [], comments = [], audit = [], onSaved } = $props();

	let activityType = $state('call');
	let activityText = $state('');
	let useCustomTime = $state(false);
	let customTime = $state(nowDatetimeLocalValue());
	let saving = $state(false);

	const timeline = $derived(buildActivityTimeline({ communications, comments }));
	const auditRows = $derived(
		(audit || []).filter((row) => !isAuditRowHidden(/** @type {Record<string, unknown>} */ (row)))
	);

	async function submitActivity() {
		const text = activityText.trim();
		if (!leadId || !text || saving) return;
		saving = true;
		try {
			const occurredAt = useCustomTime ? datetimeLocalToIso(customTime) : null;
			await createLeadCommunication(leadId, {
				communicationType: activityType,
				content: text,
				occurredAt,
			});
			activityText = '';
			useCustomTime = false;
			customTime = nowDatetimeLocalValue();
			await onSaved();
		} catch (e) {
			alert('Не удалось сохранить: ' + (/** @type {Error} */ (e)?.message || e));
		} finally {
			saving = false;
		}
	}
</script>

<div class="space-y-3 border-t border-gray-800 pt-4" data-testid="lead-activity-panel">
	<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Действия и история</div>

	<div class="space-y-2 rounded-lg border border-gray-800 bg-gray-950/40 p-3">
		<select
			bind:value={activityType}
			class="w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-xs text-gray-200"
			data-testid="lead-activity-type"
		>
			{#each ACTIVITY_TYPES as t (t.value)}
				<option value={t.value}>{t.label}</option>
			{/each}
		</select>
		<textarea
			bind:value={activityText}
			placeholder="Что сделали, договорились или планируете…"
			class="w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-xs text-gray-200 placeholder-gray-600 min-h-[4rem] resize-y"
			data-testid="lead-activity-text"
		></textarea>
		<label class="flex items-center gap-2 text-[11px] text-gray-500 cursor-pointer select-none">
			<input type="checkbox" bind:checked={useCustomTime} class="rounded border-gray-600" />
			Другое время (не сейчас)
		</label>
		{#if useCustomTime}
			<input
				type="datetime-local"
				bind:value={customTime}
				class="w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-xs text-gray-200"
				data-testid="lead-activity-when"
			/>
		{/if}
		<button
			type="button"
			disabled={saving || !activityText.trim()}
			onclick={submitActivity}
			class="w-full py-1.5 rounded-lg text-xs font-medium bg-cyan-900/50 hover:bg-cyan-800/60 text-cyan-100 disabled:opacity-50"
			data-testid="lead-activity-save"
		>
			{saving ? 'Сохранение…' : 'Сохранить в историю'}
		</button>
	</div>

	<details class="text-xs" data-testid="lead-activity-timeline">
		<summary class="cursor-pointer select-none text-gray-500 hover:text-gray-300 list-none flex items-center gap-1">
			<span class="text-gray-600">▸</span>
			История ({timeline.length})
		</summary>
		<div class="mt-2 max-h-56 overflow-y-auto space-y-2 pl-1">
			{#each timeline as item (item.id)}
				<div class="rounded border border-gray-800/80 bg-gray-950/50 px-2 py-1.5">
					<div class="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-gray-500">
						<span class="text-cyan-600/90 font-medium">{item.label}</span>
						<span>{item.actor}</span>
						<span class="tabular-nums">{formatActivityWhen(item.at)}</span>
					</div>
					<div class="text-[11px] text-gray-300 mt-0.5 whitespace-pre-wrap">{item.text}</div>
				</div>
			{:else}
				<p class="text-gray-600 text-[11px]">Пока нет записей.</p>
			{/each}
		</div>
	</details>

	{#if auditRows.length}
		<details class="text-xs" data-testid="lead-activity-audit">
			<summary class="cursor-pointer select-none text-gray-600 hover:text-gray-400 list-none">
				Технический аудит полей ({auditRows.length})
			</summary>
			<div class="mt-2 max-h-40 overflow-y-auto space-y-1 text-[10px] pl-1">
				{#each auditRows as row (row.id)}
					<div class="text-gray-500 border-b border-gray-800/60 pb-1">
						<span class="text-amber-600/80">{auditFieldLabel(row.field)}</span>
						<span class="text-gray-600"> · </span>
						<span>{formatAuditValue(row.field, row.oldValue)}</span>
						<span class="text-gray-600"> → </span>
						<span class="text-gray-400">{formatAuditValue(row.field, row.newValue)}</span>
						<div class="text-gray-600 mt-0.5">{row.actor} · {formatActivityWhen(row.changedAt)}</div>
					</div>
				{/each}
			</div>
		</details>
	{/if}
</div>
