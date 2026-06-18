<script>
	import { onMount } from 'svelte';
	import {
		fetchTenderCalendarMonth,
		fetchTenderNotifications,
		markTenderNotificationsRead
	} from '$lib/tenders/tenderCalendarOps.js';

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
		'Декабрь'
	];

	let viewYear = $state(new Date().getFullYear());
	let viewMonth = $state(new Date().getMonth() + 1);
	let cal = $state(null);
	let loading = $state(true);
	let err = $state('');
	let pickDay = $state(null);

	async function loadMonth() {
		loading = true;
		err = '';
		try {
			cal = await fetchTenderCalendarMonth(viewYear, viewMonth);
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

	function tendersForDay(day) {
		if (!day || !cal?.tenders_by_day) return [];
		return cal.tenders_by_day[String(day)] || [];
	}

	function urgencyClass(daysLeft) {
		if (daysLeft == null) return 'text-gray-400';
		if (daysLeft < 0) return 'text-red-400';
		if (daysLeft <= 3) return 'text-red-400';
		if (daysLeft <= 7) return 'text-yellow-400';
		return 'text-gray-300';
	}

	onMount(() => {
		loadMonth();
	});

	const headerTitle = $derived.by(() => {
		if (!cal) return '';
		return `${MONTH_NAMES[cal.month - 1]} ${cal.year}`;
	});
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden bg-gray-950 text-white">
	<div
		class="px-6 py-3 border-b border-gray-800 shrink-0 flex flex-wrap items-center justify-between gap-3"
	>
		<div>
			<h1 class="text-lg font-semibold">Календарь дедлайнов тендеров</h1>
			<p class="text-xs text-gray-500">«Мои тендеры» + найденные мониторингом</p>
		</div>
		<div class="flex items-center gap-2">
			<a href="/tenders" class="text-xs text-blue-400 hover:underline">← Тендеры</a>
			<a href="/tenders/notifications" class="text-xs text-blue-400 hover:underline"
				>Уведомления</a
			>
			<button
				type="button"
				onclick={prevMonth}
				class="px-3 py-1.5 rounded-lg bg-gray-800 text-gray-300 text-sm">←</button
			>
			<span class="text-sm font-medium min-w-[10rem] text-center">{headerTitle}</span>
			<button
				type="button"
				onclick={nextMonth}
				class="px-3 py-1.5 rounded-lg bg-gray-800 text-gray-300 text-sm">→</button
			>
		</div>
	</div>

	{#if err}
		<p class="px-6 py-2 text-red-400 text-sm">{err}</p>
	{/if}

	<div class="flex-1 overflow-auto p-6">
		{#if loading}
			<p class="text-gray-500 text-sm">Загрузка…</p>
		{:else if cal}
			<p class="text-xs text-gray-500 mb-4">
				Дедлайнов в месяце: {cal.total_with_deadline ?? 0}
			</p>
			<div class="grid grid-cols-7 gap-1 text-center text-[10px] text-gray-500 mb-1">
				{#each cal.weekday_labels as wd}
					<div>{wd}</div>
				{/each}
			</div>
			{#each cal.weeks as week}
				<div class="grid grid-cols-7 gap-1 mb-1">
					{#each week as day}
						<button
							type="button"
							disabled={!day}
							onclick={() => (pickDay = day)}
							class="min-h-[4.5rem] rounded-lg border text-left p-1 text-xs
                {day ? 'border-gray-800 bg-gray-900 hover:border-gray-600' : 'border-transparent'}
                {pickDay === day ? 'ring-1 ring-blue-500' : ''}"
						>
							{#if day}
								<span class="text-gray-400">{day}</span>
								{#each tendersForDay(day).slice(0, 2) as t}
									<div class="truncate {urgencyClass(t.daysLeft)}" title={t.title}>
										{t.title}
									</div>
								{/each}
								{#if tendersForDay(day).length > 2}
									<div class="text-gray-600">+{tendersForDay(day).length - 2}</div>
								{/if}
							{/if}
						</button>
					{/each}
				</div>
			{/each}

			{#if pickDay}
				<div class="mt-6 border border-gray-800 rounded-xl p-4">
					<h2 class="text-sm font-semibold mb-2">
						{pickDay}.{String(viewMonth).padStart(2, '0')}.{viewYear}
					</h2>
					{#if tendersForDay(pickDay).length === 0}
						<p class="text-gray-500 text-sm">Нет дедлайнов</p>
					{:else}
						<ul class="space-y-2">
							{#each tendersForDay(pickDay) as t}
								<li class="text-sm border-b border-gray-800 pb-2">
									<a href={t.url || '/tenders'} class="text-blue-400 hover:underline"
										>{t.title}</a
									>
									<span class="ml-2 {urgencyClass(t.daysLeft)} text-xs">
										{#if t.daysLeft != null}
											{t.daysLeft < 0 ? 'просрочен' : `${t.daysLeft} д.`}
										{/if}
									</span>
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			{/if}
		{/if}
	</div>
</div>
