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
	import { createTask, patchTask } from '$lib/tasks/taskApi.js';
	import { TASK_INTENT_OPTIONS } from '$lib/tasks/taskIntentCatalog.js';
	import {
		defaultScheduleDateIso,
		isoDateToRuDue,
		taskDueBadge,
		taskTitleFromActivity,
		tasksForActivityPanel,
	} from '$lib/leads/leadActivityTasks.js';

	/**
	 * @type {{
	 *   leadId: number | string,
	 *   relatedLead?: string,
	 *   communications?: unknown[],
	 *   comments?: unknown[],
	 *   audit?: unknown[],
	 *   tasks?: unknown[],
	 *   tasksLoading?: boolean,
	 *   onSaved: () => void | Promise<void>,
	 *   onTasksChanged?: () => void | Promise<void>,
	 * }}
	 */
	let {
		leadId,
		relatedLead = '',
		communications = [],
		comments = [],
		audit = [],
		tasks = [],
		tasksLoading = false,
		onSaved,
		onTasksChanged,
	} = $props();

	let activityType = $state('call');
	let activityText = $state('');
	let useCustomTime = $state(false);
	let customTime = $state(nowDatetimeLocalValue());
	let saving = $state(false);
	let scheduleTask = $state(false);
	let scheduleTaskIntent = $state('');
	let scheduleDateIso = $state(defaultScheduleDateIso());
	let tasksExpanded = $state(false);

	const timeline = $derived(buildActivityTimeline({ communications, comments, tasks }));
	const auditRows = $derived(
		(audit || []).filter((row) => !isAuditRowHidden(/** @type {Record<string, unknown>} */ (row)))
	);
	const taskView = $derived(
		tasksForActivityPanel(/** @type {Record<string, unknown>[]} */ (tasks), {
			expanded: tasksExpanded,
			previewLimit: 4,
		})
	);

	$effect(() => {
		if (scheduleTask) {
			scheduleDateIso = defaultScheduleDateIso({ useCustomTime, customTime });
		}
	});

	async function refreshAll() {
		await onSaved();
		if (onTasksChanged) await onTasksChanged();
	}

	async function createScheduledTask(text) {
		const title = taskTitleFromActivity(activityType, text, relatedLead);
		const due = isoDateToRuDue(scheduleDateIso);
		await createTask({
			title,
			lead_id: Number(leadId),
			related_lead: relatedLead || '',
			due: due || '—',
			note: text || '',
			task_intent: scheduleTaskIntent.trim() || null,
			assignee: 'Я',
		});
	}

	async function submitActivity() {
		const text = activityText.trim();
		if (!leadId || saving) return;
		if (!text && !scheduleTask) return;

		saving = true;
		try {
			if (text) {
				const occurredAt = useCustomTime ? datetimeLocalToIso(customTime) : null;
				await createLeadCommunication(leadId, {
					communicationType: activityType,
					content: text,
					occurredAt,
				});
			}
			if (scheduleTask) {
				await createScheduledTask(text);
			}
			activityText = '';
			useCustomTime = false;
			customTime = nowDatetimeLocalValue();
			scheduleTask = false;
			scheduleDateIso = defaultScheduleDateIso();
			await refreshAll();
		} catch (e) {
			alert('Не удалось сохранить: ' + (/** @type {Error} */ (e)?.message || e));
		} finally {
			saving = false;
		}
	}

	/** @param {Record<string, unknown>} task */
	async function toggleTaskDone(task) {
		try {
			await patchTask(task.id, { status: task.status === 'done' ? 'open' : 'done' });
			if (onTasksChanged) await onTasksChanged();
		} catch (e) {
			alert('Ошибка задачи: ' + (/** @type {Error} */ (e)?.message || e));
		}
	}
</script>

<div class="space-y-3" data-testid="lead-activity-panel">
	{#if tasksLoading}
		<p class="text-[11px] text-gray-600">Загрузка задач…</p>
	{:else if taskView.totalOpen > 0}
		<div
			class="rounded-lg border border-violet-900/40 bg-violet-950/15 p-2.5 space-y-1.5"
			data-testid="lead-activity-tasks"
		>
			<div class="flex items-center justify-between gap-2">
				<span class="text-[10px] font-semibold uppercase tracking-wide text-violet-300/90">
					Задачи · {taskView.totalOpen}
				</span>
				<a href="/leads/calendar" class="text-[10px] text-indigo-400 hover:underline shrink-0">Календарь →</a>
			</div>
			{#each taskView.items as task (task.id)}
				{@const badge = taskDueBadge(task)}
				<div class="flex items-start gap-2 rounded-md border border-gray-800/80 bg-gray-950/60 px-2 py-1.5">
					<button
						type="button"
						class="mt-0.5 w-4 h-4 rounded border border-gray-600 shrink-0 hover:border-violet-500"
						aria-label="Отметить выполненной"
						onclick={() => toggleTaskDone(task)}
					></button>
					<div class="min-w-0 flex-1">
						<div class="text-[11px] text-gray-200 leading-snug line-clamp-2">{task.title}</div>
						<div class="flex flex-wrap items-center gap-1.5 mt-0.5">
							{#if task.due && task.due !== '—'}
								<span class="text-[10px] text-gray-500 tabular-nums">до {task.due}</span>
							{/if}
							<span class="text-[9px] px-1.5 py-px rounded border {badge.cls}">{badge.label}</span>
						</div>
					</div>
				</div>
			{/each}
			{#if taskView.hiddenCount > 0}
				<button
					type="button"
					class="w-full text-[10px] text-violet-400 hover:text-violet-300 py-1"
					data-testid="lead-activity-tasks-expand"
					onclick={() => { tasksExpanded = true; }}
				>
					Ещё {taskView.hiddenCount} {taskView.hiddenCount === 1 ? 'задача' : 'задач'} ▾
				</button>
			{:else if tasksExpanded && taskView.totalOpen > 4}
				<button
					type="button"
					class="w-full text-[10px] text-gray-500 hover:text-gray-400 py-1"
					onclick={() => { tasksExpanded = false; }}
				>
					Свернуть ▴
				</button>
			{/if}
		</div>
	{/if}

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
		<label class="flex items-center gap-2 text-[11px] text-violet-300/90 cursor-pointer select-none">
			<input
				type="checkbox"
				bind:checked={scheduleTask}
				class="rounded border-gray-600"
				data-testid="lead-activity-schedule-task"
			/>
			Поставить задачу в календарь
		</label>
		{#if scheduleTask}
			<label class="block text-[11px] text-gray-500">
				Тип дела
				<select
					bind:value={scheduleTaskIntent}
					class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-xs text-gray-200"
					data-testid="lead-activity-task-intent"
				>
					{#each TASK_INTENT_OPTIONS as opt (opt.id || 'auto')}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			<label class="block text-[11px] text-gray-500">
				Срок задачи
				<input
					type="date"
					bind:value={scheduleDateIso}
					class="mt-0.5 w-full bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-xs text-gray-200"
					data-testid="lead-activity-task-due"
				/>
			</label>
		{/if}
		<button
			type="button"
			disabled={saving || (!activityText.trim() && !scheduleTask)}
			onclick={submitActivity}
			class="w-full py-1.5 rounded-lg text-xs font-medium bg-cyan-900/50 hover:bg-cyan-800/60 text-cyan-100 disabled:opacity-50"
			data-testid="lead-activity-save"
		>
			{#if saving}
				Сохранение…
			{:else if scheduleTask && activityText.trim()}
				В историю + задача в календарь
			{:else if scheduleTask}
				Поставить задачу
			{:else}
				Сохранить в историю
			{/if}
		</button>
	</div>

	<details class="text-xs" data-testid="lead-activity-timeline" open={timeline.length > 0}>
		<summary class="cursor-pointer select-none text-gray-500 hover:text-gray-300 list-none flex items-center gap-1">
			<span class="text-gray-600">▸</span>
			История ({timeline.length})
		</summary>
		<div class="mt-2 max-h-80 overflow-y-auto space-y-2 pl-1">
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
