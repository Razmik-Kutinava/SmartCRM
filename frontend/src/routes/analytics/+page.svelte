<script>
	const funnel = [
		{ stage: 'Новых лидов', count: 48, pct: 100 },
		{ stage: 'Квалифицировано', count: 31, pct: 65 },
		{ stage: 'КП отправлено', count: 18, pct: 38 },
		{ stage: 'Переговоры', count: 9, pct: 19 },
		{ stage: 'Выиграно', count: 4, pct: 8 },
	];
</script>

<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900 shrink-0">
	<div>
		<h1 class="text-lg font-semibold text-white">Аналитика</h1>
		<p class="text-xs text-gray-500">Апрель 2026</p>
	</div>
	<button class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">📥 Экспорт отчёта</button>
</div>

<div class="flex-1 overflow-y-auto p-6 space-y-5">

	<!-- Funnel -->
	<div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
		<div class="text-sm font-medium text-white mb-4">Воронка продаж</div>
		<div class="space-y-3">
			{#each funnel as item}
				<div>
					<div class="flex justify-between text-xs text-gray-400 mb-1">
						<span>{item.stage}</span>
						<span class="text-white font-medium">{item.count}</span>
					</div>
					<div class="h-2 bg-gray-800 rounded-full">
						<div class="h-2 bg-indigo-600 rounded-full transition-all" style="width: {item.pct}%"></div>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<div class="grid grid-cols-3 gap-4">
		{#each [
			['Конверсия в сделку', '8.3%', '+1.2%'],
			['Средний чек', '650 000 ₽', '+15%'],
			['Цикл сделки', '18 дней', '-3 дня'],
		] as [label, value, change]}
			<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
				<div class="text-xs text-gray-500 mb-1">{label}</div>
				<div class="text-xl font-bold text-white">{value}</div>
				<div class="text-xs text-green-400 mt-0.5">{change}</div>
			</div>
		{/each}
	</div>

</div>
