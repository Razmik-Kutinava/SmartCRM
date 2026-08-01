<script>
	/**
	 * Универсальная отрисовка ответа агента с карточки лида.
	 * У каждого агента свой JSON: маркетолог — письмо, стратег — решение,
	 * аналитик — скор и BANT, экономист — ROI, тех. спец — стек.
	 */
	let { result = {}, leadEmail = '', onCompose = () => {} } = $props();

	const PRIORITY_COLORS = {
		high: 'text-red-400 border-red-700',
		medium: 'text-yellow-400 border-yellow-700',
		low: 'text-gray-400 border-gray-700',
	};

	const URGENCY_LABELS = {
		today: 'сегодня',
		this_week: 'на этой неделе',
		next_week: 'на следующей неделе',
		nurture: 'в прогрев',
	};

	let bantRows = $derived(Object.entries(result?.bant || {}));
	let priorityClass = $derived(PRIORITY_COLORS[result?.priority] || PRIORITY_COLORS.low);
	// поля, уже показанные явными блоками — в «прочее» не дублируем
	const SHOWN = new Set([
		'first_email', 'value_hook', 'summary', 'touch_sequence',
		'decision', 'priority', 'urgency', 'next_action', 'rationale', 'coach_tip', 'final_reply',
		'score', 'score_rationale', 'bant', 'next_steps', 'risks',
		'roi', 'roi_months', 'payback', 'price_recommendation', 'budget_justification',
		'recommended_stack', 'integrations', 'technical_risks', 'implementation_complexity',
	]);
	let extras = $derived(
		Object.entries(result || {})
			.filter(([k, v]) => !SHOWN.has(k) && !k.startsWith('_') && v && typeof v !== 'object')
			.slice(0, 6)
	);
</script>

<!-- маркетолог: письмо -->
{#if result?.first_email}
	<div class="bg-gray-950 border border-gray-800 rounded-xl p-4">
		<div class="text-xs text-gray-500 mb-1">Тема:</div>
		<div class="text-sm font-semibold text-white mb-3">{result.first_email.subject}</div>
		<div class="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{result.first_email.body}</div>
		<button
			onclick={() => onCompose(leadEmail, result.first_email.subject, result.first_email.body)}
			class="mt-3 px-4 py-1.5 rounded-lg bg-indigo-600 text-xs font-semibold text-white hover:bg-indigo-500 transition-colors"
		>↗ Открыть в compose</button>
	</div>
{/if}

<!-- стратег: решение и следующий шаг -->
{#if result?.decision}
	<div class="bg-gray-950 border {priorityClass} rounded-xl p-4 border-l-4">
		<div class="text-xs text-gray-500 mb-1">
			Решение
			{#if result.urgency}<span class="ml-1">· {URGENCY_LABELS[result.urgency] || result.urgency}</span>{/if}
		</div>
		<div class="text-sm font-semibold text-white">{result.decision}</div>
		{#if result.rationale}
			<p class="mt-2 text-xs text-gray-400 leading-relaxed">{result.rationale}</p>
		{/if}
	</div>
{/if}

{#if result?.next_action}
	<div class="text-sm text-gray-200 border-l-2 border-indigo-600 pl-3">
		<span class="text-xs text-gray-500 block mb-0.5">Следующий шаг</span>
		{result.next_action}
	</div>
{/if}

{#if result?.coach_tip}
	<div class="text-xs text-indigo-300 bg-indigo-950/30 border border-indigo-900 rounded-lg px-3 py-2">
		💡 {result.coach_tip}
	</div>
{/if}

<!-- аналитик: скор и BANT -->
{#if result?.score}
	<div class="flex items-center gap-3 flex-wrap">
		<span class="px-3 py-1 rounded-lg bg-gray-800 text-sm font-semibold text-white">Скор: {result.score}/100</span>
		{#if result.score_rationale}
			<span class="text-xs text-gray-500">{result.score_rationale}</span>
		{/if}
	</div>
{/if}

{#if bantRows.length}
	<div class="grid grid-cols-2 gap-2">
		{#each bantRows as [key, value]}
			<div class="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2">
				<div class="text-[11px] uppercase tracking-wide text-gray-600">{key}</div>
				<div class="text-xs text-gray-300">{value}</div>
			</div>
		{/each}
	</div>
{/if}

{#if result?.next_steps?.length}
	<div>
		<div class="text-xs text-gray-500 mb-2">✅ Следующие шаги</div>
		<ul class="space-y-1">
			{#each result.next_steps as step}
				<li class="text-xs text-gray-300">• {step}</li>
			{/each}
		</ul>
	</div>
{/if}

{#if result?.risks?.length}
	<div>
		<div class="text-xs text-gray-500 mb-2">⚠️ Риски</div>
		<ul class="space-y-1">
			{#each result.risks as risk}
				<li class="text-xs text-red-300">• {risk}</li>
			{/each}
		</ul>
	</div>
{/if}

<!-- экономист: деньги -->
{#if result?.roi || result?.payback || result?.price_recommendation}
	<div class="bg-gray-950 border border-gray-800 rounded-xl p-4 space-y-1">
		<div class="text-xs text-gray-500">💰 Экономика</div>
		{#if result.roi}<div class="text-sm text-gray-200">ROI: {result.roi}</div>{/if}
		{#if result.payback}<div class="text-xs text-gray-400">Окупаемость: {result.payback}</div>{/if}
		{#if result.price_recommendation}<div class="text-xs text-gray-400">Цена: {result.price_recommendation}</div>{/if}
		{#if result.budget_justification}<p class="text-xs text-gray-500">{result.budget_justification}</p>{/if}
	</div>
{/if}

<!-- тех. спец: стек и интеграции -->
{#if result?.recommended_stack?.length || result?.integrations?.length || result?.technical_risks?.length}
	<div class="bg-gray-950 border border-gray-800 rounded-xl p-4 space-y-2">
		<div class="text-xs text-gray-500">⚙️ Техническая часть</div>
		{#if result.recommended_stack?.length}
			<div class="text-xs text-gray-300">Стек: {result.recommended_stack.join(', ')}</div>
		{/if}
		{#if result.integrations?.length}
			<div class="text-xs text-gray-300">Интеграции: {result.integrations.join(', ')}</div>
		{/if}
		{#if result.implementation_complexity}
			<div class="text-xs text-gray-400">Сложность внедрения: {result.implementation_complexity}</div>
		{/if}
		{#if result.technical_risks?.length}
			<ul class="space-y-1">
				{#each result.technical_risks as risk}
					<li class="text-xs text-red-300">• {risk}</li>
				{/each}
			</ul>
		{/if}
	</div>
{/if}

{#if result?.value_hook}
	<div class="text-sm text-gray-300 border-l-2 border-indigo-600 pl-3">
		<span class="text-xs text-gray-500 block mb-0.5">Крючок внимания</span>
		{result.value_hook}
	</div>
{/if}

{#if result?.summary}
	<p class="text-xs text-gray-500 italic">{result.summary}</p>
{:else if result?.final_reply && !result?.decision}
	<p class="text-xs text-gray-400">{result.final_reply}</p>
{/if}

{#if result?.touch_sequence?.length}
	<div>
		<div class="text-xs text-gray-500 mb-2">📅 План касаний</div>
		<div class="space-y-1">
			{#each result.touch_sequence as t}
				<div class="text-xs text-gray-300">
					<span class="text-indigo-400 w-12 inline-block">День {t.day}</span>
					<span class="text-gray-600 mr-2">{t.channel}</span>
					{t.action}
				</div>
			{/each}
		</div>
	</div>
{/if}

{#if extras.length}
	<div class="border-t border-gray-800 pt-2 space-y-0.5">
		{#each extras as [key, value]}
			<div class="text-[11px] text-gray-500"><span class="text-gray-600">{key}:</span> {value}</div>
		{/each}
	</div>
{/if}
