<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';
	import { fetchLeads } from '$lib/leadsStorage.js';

	const API = getApiUrl();

	const MONTH_NAMES = [
		'Январь',
		'Февраль',
		'Март',
		'Апрель',
		'Май',
		'Июнь',
		'Июль',
		'Август',
		'Сентябрь',
		'Октябрь',
		'Ноябрь',
		'Декабрь',
	];

	let viewYear = $state(new Date().getFullYear());
	let viewMonth = $state(new Date().getMonth() + 1);
	let cal = $state(null);
	let leads = $state([]);
	let loading = $state(true);
	let err = $state('');

	let panelOpen = $state(false);
	let pickDay = $state(null);
	let newTitle = $state('');
	let newDue = $state('');
	let newSla = $state('');
	let newAssignee = $state('Я');
	let newLeadId = $state('');
	let newNote = $state('');
	let saving = $state(false);

	function pad2(n) {
		return String(n).padStart(2, '0');
	}

	function formatRuDate(year, month, day) {
		return `${pad2(day)}.${pad2(month)}.${year}`;
	}

	async function loadMonth() {
		loading = true;
		err = '';
		try {
			const r = await fetch(
				`${API}/api/tasks/calendar/month?year=${viewYear}&month=${viewMonth}`
			);
			if (!r.ok) throw new Error(await r.text());
			cal = await r.json();
			if (!leads.length) leads = await fetchLeads().catch(() => []);
		} catch (e) {
			err = e?.message || String(e);
			cal = null;
		} finally {
			loading = false;
		}
	}

	function prevMonth() {
		let m = viewMonth - 1;
		let y = viewYear;
		if (m < 1) {
			m = 12;
			y -= 1;
		}
		viewMonth = m;
		viewYear = y;
		loadMonth();
	}

	function nextMonth() {
		let m = viewMonth + 1;
		let y = viewYear;
		if (m > 12) {
			m = 1;
			y += 1;
		}
		viewMonth = m;
		viewYear = y;
		loadMonth();
	}

	function openDay(day) {
		if (!day) return;
		pickDay = day;
		newDue = formatRuDate(viewYear, viewMonth, day);
		newSla = '';
		newTitle = '';
		newNote = '';
		newLeadId = '';
		panelOpen = true;
	}

	function closePanel() {
		panelOpen = false;
		pickDay = null;
	}

	async function submitNew(ev) {
		ev?.preventDefault();
		if (!newTitle.trim()) return;
		saving = true;
		try {
			const body = {
				title: newTitle.trim(),
				due: newDue.trim() || '—',
				assignee: newAssignee.trim() || 'Я',
				related_lead: '',
				lead_id: newLeadId ? Number(newLeadId) : null,
				note: newNote.trim(),
				sla_due: newSla.trim() || null,
				escalated: false,
			};
			const r = await fetch(`${API}/api/tasks`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(body),
			});
			if (!r.ok) throw new Error(await r.text());
			closePanel();
			await loadMonth();
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			saving = false;
		}
	}

	onMount(() => {
		const n = new Date();
		viewYear = n.getFullYear();
		viewMonth = n.getMonth() + 1;
		loadMonth();
	});

	const headerTitle = $derived.by(() => {
		if (!cal) return '';
		return `${MONTH_NAMES[cal.month - 1]} ${cal.year}`;
	});

	function tasksForDay(day) {
		if (!day || !cal?.tasks_by_day) return [];
		return cal.tasks_by_day[String(day)] || [];
	}
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden">
	<div class="px-6 py-3 border-b border-gray-800 bg-gray-900 shrink-0 flex flex-wrap items-center justify-between gap-3">
		<div>
			<h1 class="text-lg font-semibold text-white">Календарь задач</h1>
			<p class="text-xs text-gray-500">
				Сетка месяца (Python <code class="text-gray-400">calendar.monthcalendar</code>) · клик по дню — новая задача
			</p>
		</div>
		<div class="flex items-center gap-2">
			<button
				type="button"
				onclick={prevMonth}
				class="px-3 py-1.5 rounded-lg bg-gray-800 text-gray-300 text-sm hover:bg-gray-700"
			>
				←
			</button>
			<span class="text-sm text-white font-medium min-w-[10rem] text-center">{headerTitle}</span>
			<button
				type="button"
				onclick={nextMonth}
				class="px-3 py-1.5 rounded-lg bg-gray-800 text-gray-300 text-sm hover:bg-gray-700"
			>
				→
			</button>
			<a
				href="/leads/tasks"
				data-sveltekit-preload-data="off"
				class="ml-2 text-xs text-indigo-400 hover:underline"
			>
				Все задачи →
			</a>
		</div>
	</div>

	<div class="flex-1 overflow-auto p-4">
		{#if err && !cal}
			<p class="text-red-400 text-sm">{err}</p>
		{:else if loading && !cal}
			<p class="text-gray-500 text-sm">Загрузка календаря…</p>
		{:else if cal}
			{#if err}
				<p class="text-amber-400 text-xs mb-2">{err}</p>
			{/if}
			<div class="grid grid-cols-7 gap-px bg-gray-800 rounded-xl overflow-hidden border border-gray-800 max-w-5xl">
				{#each cal.weekday_labels as wd}
					<div class="bg-gray-900 px-2 py-2 text-center text-[11px] text-gray-500 font-medium">{wd}</div>
				{/each}
				{#each cal.weeks as week}
					{#each week as day}
						<button
							type="button"
							onclick={() => openDay(day)}
							class="min-h-[5.5rem] bg-gray-950 hover:bg-gray-900/90 text-left p-2 align-top border-t border-gray-800/80 transition-colors
								{day ? '' : 'cursor-default opacity-40'}"
							disabled={!day}
						>
							{#if day}
								<div class="text-xs font-semibold text-gray-300 mb-1">{day}</div>
								<ul class="space-y-0.5">
									{#each tasksForDay(day).slice(0, 4) as t}
										<li class="text-[10px] leading-tight text-indigo-300 truncate" title={t.title}>
											{t.status === 'done' ? '✓ ' : ''}{t.title}
										</li>
									{/each}
									{#if tasksForDay(day).length > 4}
										<li class="text-[10px] text-gray-600">
											+{tasksForDay(day).length - 4}
										</li>
									{/if}
								</ul>
							{/if}
						</button>
					{/each}
				{/each}
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
		class="fixed z-50 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md rounded-2xl border border-gray-800 bg-gray-950 p-6 shadow-2xl"
	>
		<h2 class="text-sm font-semibold text-white mb-1">Новая задача</h2>
		<p class="text-xs text-gray-500 mb-4">День {pickDay} · срок по умолчанию в поле «Срок»</p>
		<form onsubmit={submitNew} class="space-y-3">
			<input
				bind:value={newTitle}
				placeholder="Название *"
				class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
			/>
			<div class="grid grid-cols-2 gap-2">
				<div>
					<label class="text-[10px] text-gray-500 uppercase">Срок (дд.мм.гггг)</label>
					<input
						bind:value={newDue}
						class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
					/>
				</div>
				<div>
					<label class="text-[10px] text-gray-500 uppercase">SLA</label>
					<input
						bind:value={newSla}
						placeholder="опц."
						class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
					/>
				</div>
			</div>
			<input
				bind:value={newAssignee}
				placeholder="Исполнитель"
				class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
			/>
			<select
				bind:value={newLeadId}
				class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
			>
				<option value="">— Лид —</option>
				{#each leads as L}
					<option value={String(L.id)}>{L.company}</option>
				{/each}
			</select>
			<textarea
				bind:value={newNote}
				placeholder="Заметка"
				class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white min-h-[64px]"
			></textarea>
			<div class="flex justify-end gap-2 pt-2">
				<button
					type="button"
					onclick={closePanel}
					class="px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-white"
				>
					Отмена
				</button>
				<button
					type="submit"
					disabled={saving || !newTitle.trim()}
					class="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm disabled:opacity-50"
				>
					{saving ? '…' : 'Создать'}
				</button>
			</div>
		</form>
	</div>
{/if}
