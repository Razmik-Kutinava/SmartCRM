<script>
	import { onMount } from 'svelte';
	import { fetchLeads } from '$lib/leadsStorage.js';
	import { createTask as apiCreateTask, fetchTasks, patchTask } from '$lib/tasks/taskApi.js';
	import { slaStatus } from '$lib/tasks/taskSla.js';

	let tasks = $state([]);
	let leads = $state([]);
	let loading = $state(true);
	let err = $state('');

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
			tasks = await fetchTasks();
			leads = await fetchLeads().catch(() => []);
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			loading = false;
		}
	}

	onMount(load);

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
			title = '';
			due = '';
			slaDue = '';
			note = '';
			leadId = '';
			relatedLead = '';
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
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden">
	<div class="px-6 py-3 border-b border-gray-800 bg-gray-900 shrink-0">
		<h1 class="text-lg font-semibold text-white">Задачи и SLA</h1>
		<p class="text-xs text-gray-500">
			Один список задач CRM: срок, SLA-дедлайн, эскалация при просрочке (флажок).
		</p>
	</div>

	<div class="flex-1 overflow-y-auto p-6 space-y-6">
		{#if err}
			<div class="text-red-400 text-sm">{err}</div>
		{/if}

		<form onsubmit={submitTaskForm} class="rounded-xl border border-gray-800 bg-gray-900/80 p-4 space-y-3 max-w-3xl">
			<div class="text-sm font-medium text-white">Новая задача</div>
			<div class="grid sm:grid-cols-2 gap-3">
				<input
					bind:value={title}
					placeholder="Название *"
					class="rounded-lg bg-gray-950 border border-gray-700 px-3 py-2 text-sm text-white"
				/>
				<input
					bind:value={assignee}
					placeholder="Исполнитель"
					class="rounded-lg bg-gray-950 border border-gray-700 px-3 py-2 text-sm text-white"
				/>
				<input
					bind:value={due}
					placeholder="Срок (текст, напр. 20.04.2026)"
					class="rounded-lg bg-gray-950 border border-gray-700 px-3 py-2 text-sm text-white"
				/>
				<input
					bind:value={slaDue}
					placeholder="SLA до (дата, напр. 18.04.2026)"
					class="rounded-lg bg-gray-950 border border-gray-700 px-3 py-2 text-sm text-white"
				/>
				<select
					bind:value={leadId}
					class="rounded-lg bg-gray-950 border border-gray-700 px-3 py-2 text-sm text-white"
				>
					<option value="">— Лид (необязательно) —</option>
					{#each leads as L}
						<option value={String(L.id)}>{L.company}</option>
					{/each}
				</select>
				<input
					bind:value={relatedLead}
					placeholder="Название лида (текстом)"
					class="rounded-lg bg-gray-950 border border-gray-700 px-3 py-2 text-sm text-white"
				/>
			</div>
			<textarea
				bind:value={note}
				placeholder="Заметка"
				class="w-full rounded-lg bg-gray-950 border border-gray-700 px-3 py-2 text-sm text-white min-h-[72px]"
			></textarea>
			<button
				type="submit"
				disabled={saving || !title.trim()}
				class="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm disabled:opacity-50"
			>
				{saving ? '…' : 'Создать задачу'}
			</button>
		</form>

		{#if loading}
			<p class="text-gray-500 text-sm">Загрузка…</p>
		{:else}
			<div class="overflow-x-auto rounded-xl border border-gray-800">
				<table class="w-full text-sm">
					<thead class="bg-gray-900 text-left text-xs text-gray-500">
						<tr>
							<th class="px-4 py-2">Задача</th>
							<th class="px-4 py-2">Срок</th>
							<th class="px-4 py-2">SLA</th>
							<th class="px-4 py-2">Статус SLA</th>
							<th class="px-4 py-2">Лид</th>
							<th class="px-4 py-2">Эскалация</th>
							<th class="px-4 py-2">Действия</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-800">
						{#each tasks as t}
							<tr class="hover:bg-gray-800/40">
								<td class="px-4 py-2 text-white">
									<div class="font-medium">{t.title}</div>
									{#if t.note}<div class="text-xs text-gray-500 line-clamp-2">{t.note}</div>{/if}
								</td>
								<td class="px-4 py-2 text-gray-400">{t.due}</td>
								<td class="px-4 py-2 text-gray-400">{t.slaDue || '—'}</td>
								<td class="px-4 py-2">
									<span class={slaStatus(t).cls}>{slaStatus(t).label}</span>
								</td>
								<td class="px-4 py-2 text-gray-400">
									{#if t.leadId}
										<a href={`/leads/${t.leadId}`} class="text-indigo-400 hover:underline">#{t.leadId}</a>
									{:else}
										{t.relatedLead || '—'}
									{/if}
								</td>
								<td class="px-4 py-2">
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
								<td class="px-4 py-2">
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
					<p class="p-6 text-center text-gray-600 text-sm">Задач пока нет</p>
				{/if}
			</div>
		{/if}
	</div>
</div>
