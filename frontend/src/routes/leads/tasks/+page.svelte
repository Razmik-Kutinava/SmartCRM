<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { fetchLeads } from '$lib/leadsStorage.js';
	import { createTask as apiCreateTask, fetchTasks, patchTask } from '$lib/tasks/taskApi.js';
	import { slaStatus } from '$lib/tasks/taskSla.js';
	import {
		parseTasksPageFilter,
		TASK_PAGE_FILTERS,
		tasksFetchParams,
	} from '$lib/tasks/tasksPageFilters.js';

	let tasks = $state([]);
	let leads = $state([]);
	let loading = $state(true);
	let err = $state('');
	let filter = $state('all');
	let panelOpen = $state(false);
	let createMode = $state('task');

	let title = $state('');
	let due = $state('');
	let slaDue = $state('');
	let assignee = $state('Я');
	let relatedLead = $state('');
	let leadId = $state('');
	let note = $state('');
	let saving = $state(false);

	async function load() {
		loading = true;
		err = '';
		try {
			tasks = await fetchTasks(tasksFetchParams(filter));
			leads = await fetchLeads().catch(() => []);
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			loading = false;
		}
	}

	function resetForm() {
		title = '';
		due = '';
		slaDue = '';
		note = '';
		leadId = '';
		relatedLead = '';
		assignee = 'Я';
	}

	function openCreate(mode = 'task') {
		createMode = mode;
		resetForm();
		panelOpen = true;
	}

	function closePanel() {
		panelOpen = false;
	}

	onMount(() => {
		filter = parseTasksPageFilter($page.url.searchParams.get('filter'));
		load();
	});

	async function submitTaskForm(ev) {
		ev?.preventDefault();
		if (!title.trim()) return;
		saving = true;
		try {
			const body = {
				title: title.trim(),
				due: due.trim() || '—',
				assignee: assignee.trim() || 'Я',
				related_lead: relatedLead.trim(),
				lead_id: leadId ? Number(leadId) : null,
				note: note.trim(),
				sla_due: slaDue.trim() || null,
				escalated: false,
			};
			await apiCreateTask(body);
			resetForm();
			closePanel();
			await load();
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			saving = false;
		}
	}

	async function toggleDone(t) {
		const next = t.status === 'done' ? 'open' : 'done';
		try {
			await patchTask(t.id, { status: next });
			await load();
		} catch (e) {
			err = e?.message || String(e);
		}
	}

	async function toggleEscalation(t) {
		try {
			await patchTask(t.id, { escalated: !t.escalated });
			await load();
		} catch (e) {
			err = e?.message || String(e);
		}
	}

	function setFilter(id) {
		filter = id;
		load();
	}
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden">
	<div class="px-6 py-3 border-b border-gray-800 bg-gray-900 shrink-0">
		<div class="flex flex-wrap items-start justify-between gap-3">
			<div class="min-w-0">
				<h1 class="text-lg font-semibold text-white">Задачи и SLA</h1>
				<p class="text-xs text-gray-500 mt-0.5">
					Список дел по лидам: срок, SLA, эскалация. Встречи из Битрикса — с префиксом «Встреча:».
				</p>
			</div>
			<div class="flex items-center gap-2 shrink-0">
				<button
					type="button"
					data-testid="tasks-create-btn"
					onclick={() => openCreate('task')}
					class="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-500"
				>
					<span class="text-base leading-none" aria-hidden="true">+</span>
					Создать задачу
				</button>
				<button
					type="button"
					data-testid="tasks-create-sla-btn"
					onclick={() => openCreate('sla')}
					class="rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-sm text-gray-200 hover:bg-gray-700 hover:text-white"
				>
					+ SLA
				</button>
			</div>
		</div>
		<div class="flex gap-2 mt-3 flex-wrap" role="tablist" aria-label="Фильтр задач">
			{#each TASK_PAGE_FILTERS as [id, label]}
				<button
					type="button"
					role="tab"
					aria-selected={filter === id}
					class="text-xs px-2.5 py-1 rounded-md {filter === id
						? 'bg-indigo-600 text-white'
						: 'bg-gray-800 text-gray-400 hover:text-gray-200'}"
					onclick={() => setFilter(id)}
				>{label}</button>
			{/each}
			{#if !loading}
				<span class="text-xs text-gray-600 self-center ml-1">{tasks.length} шт.</span>
			{/if}
		</div>
	</div>

	<div class="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6">
		{#if err}
			<div class="text-red-400 text-sm mb-3">{err}</div>
		{/if}

		{#if loading}
			<p class="text-gray-500 text-sm">Загрузка…</p>
		{:else}
			<div
				class="overflow-x-auto rounded-xl border border-gray-800"
				data-testid="tasks-table"
			>
				<table class="w-full text-sm">
					<thead class="bg-gray-900 text-left text-xs text-gray-500 sticky top-0 z-10">
						<tr>
							<th class="px-4 py-2.5">Задача</th>
							<th class="px-4 py-2.5">Срок</th>
							<th class="px-4 py-2.5">SLA</th>
							<th class="px-4 py-2.5">Статус SLA</th>
							<th class="px-4 py-2.5">Лид</th>
							<th class="px-4 py-2.5">Эскалация</th>
							<th class="px-4 py-2.5">Действия</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-800">
						{#each tasks as t}
							<tr class="hover:bg-gray-800/40">
								<td class="px-4 py-2.5 text-white max-w-md">
									<div class="font-medium">{t.title}</div>
									{#if t.note}
										<div class="text-xs text-gray-500 line-clamp-2 mt-0.5">{t.note}</div>
									{/if}
								</td>
								<td class="px-4 py-2.5 text-gray-400 whitespace-nowrap">{t.due}</td>
								<td class="px-4 py-2.5 text-gray-400 whitespace-nowrap">{t.slaDue || '—'}</td>
								<td class="px-4 py-2.5 whitespace-nowrap">
									<span class={slaStatus(t).cls}>{slaStatus(t).label}</span>
								</td>
								<td class="px-4 py-2.5 text-gray-400 max-w-[140px] truncate">
									{#if t.leadId}
										<a href={`/leads/${t.leadId}`} class="text-indigo-400 hover:underline">#{t.leadId}</a>
									{:else}
										{t.relatedLead || '—'}
									{/if}
								</td>
								<td class="px-4 py-2.5">
									<button
										type="button"
										onclick={() => toggleEscalation(t)}
										class="text-xs px-2 py-1 rounded {t.escalated
											? 'bg-red-900 text-red-200'
											: 'bg-gray-800 text-gray-400'}"
									>
										{t.escalated ? 'Да' : 'Нет'}
									</button>
								</td>
								<td class="px-4 py-2.5 whitespace-nowrap">
									<button
										type="button"
										onclick={() => toggleDone(t)}
										class="text-xs text-indigo-400 hover:underline"
									>
										{t.status === 'done' ? 'Открыть' : 'Выполнено'}
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
				{#if tasks.length === 0}
					<p class="p-8 text-center text-gray-600 text-sm">
						Задач нет. Нажмите «Создать задачу» или дождитесь синка из Битрикса.
					</p>
				{/if}
			</div>
		{/if}
	</div>
</div>

{#if panelOpen}
	<button
		type="button"
		class="fixed inset-0 bg-black/60 z-40"
		onclick={closePanel}
		aria-label="Закрыть"
	></button>
	<div
		class="fixed z-50 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg rounded-2xl border border-gray-800 bg-gray-950 p-6 shadow-2xl"
		data-testid="tasks-create-modal"
	>
		<h2 class="text-sm font-semibold text-white mb-1">
			{createMode === 'sla' ? 'Новая задача со SLA' : 'Новая задача'}
		</h2>
		<p class="text-xs text-gray-500 mb-4">
			{createMode === 'sla'
				? 'Укажите SLA-дедлайн — статус просрочки появится в списке.'
				: 'Задача появится в общем списке и у выбранного лида.'}
		</p>
		<form onsubmit={submitTaskForm} class="space-y-3">
			<input
				bind:value={title}
				placeholder="Название *"
				class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
			/>
			<div class="grid sm:grid-cols-2 gap-3">
				<input
					bind:value={assignee}
					placeholder="Исполнитель"
					class="rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
				/>
				<input
					bind:value={due}
					placeholder="Срок (дд.мм.гггг)"
					class="rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
				/>
				<input
					bind:value={slaDue}
					placeholder="SLA до (дд.мм.гггг)"
					class="rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white sm:col-span-2 {createMode === 'sla'
						? 'ring-1 ring-indigo-500/50'
						: ''}"
				/>
				<select
					bind:value={leadId}
					class="rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
				>
					<option value="">— Лид (необязательно) —</option>
					{#each leads as L}
						<option value={String(L.id)}>{L.company}</option>
					{/each}
				</select>
				<input
					bind:value={relatedLead}
					placeholder="Название лида (текстом)"
					class="rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
				/>
			</div>
			<textarea
				bind:value={note}
				placeholder="Заметка"
				class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white min-h-[72px]"
			></textarea>
			<div class="flex justify-end gap-2 pt-1">
				<button
					type="button"
					onclick={closePanel}
					class="px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-white"
				>
					Отмена
				</button>
				<button
					type="submit"
					disabled={saving || !title.trim()}
					class="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm disabled:opacity-50"
				>
					{saving ? '…' : 'Создать'}
				</button>
			</div>
		</form>
	</div>
{/if}
