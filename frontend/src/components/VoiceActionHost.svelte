<script>
	import { voiceModal, voiceApprove, resolveVoiceApprove, closeVoiceModal, voiceToast } from '$lib/voice/voiceAction.js';
	import { goto } from '$app/navigation';
	import { sendEmail } from '$lib/emailStorage.js';

	function modalAction(kind) {
		const m = $voiceModal;
		if (!m) return;
		if (kind === 'send' && m.payload?.draft_email) {
			const em = m.payload.draft_email;
			const target = m.slots?.target || m.slots?.email || '';
			if (target) {
				sendEmail({ to: [String(target)], subject: em.subject || '', body: em.body || '' })
					.then(() => voiceToast.set(`Письмо отправлено: ${target}`))
					.catch((e) => voiceToast.set(e?.message || String(e)));
				closeVoiceModal();
				return;
			}
			const q = new URLSearchParams({
				subject: em.subject || '',
				body: em.body || '',
			});
			closeVoiceModal();
			goto(`/email?${q.toString()}`);
			return;
		}
		closeVoiceModal();
	}

	function summaryText(block) {
		if (!block) return '';
		if (typeof block === 'string') return block;
		return block.summary || block.text || JSON.stringify(block, null, 2);
	}

	const priorityLabels = {
		high: 'Высокий',
		medium: 'Средний',
		low: 'Низкий',
	};
</script>

{#if $voiceApprove}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true">
		<div class="w-full max-w-md rounded-xl border border-amber-800/60 bg-gray-900 p-5 shadow-xl">
			<h2 class="text-base font-semibold text-amber-200 mb-2">
				{$voiceApprove.title || 'Подтверждение'}
			</h2>
			<p class="text-sm text-gray-300 mb-4">
				{$voiceApprove.payload?.message || $voiceApprove.reply || 'Подтвердите действие'}
			</p>
			<div class="flex justify-end gap-2">
				<button
					type="button"
					data-testid="voice-approve-reject"
					class="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700"
					onclick={() => resolveVoiceApprove('reject')}
				>Отмена</button>
				<button
					type="button"
					data-testid="voice-approve-confirm"
					class="px-3 py-1.5 text-sm rounded-lg bg-red-700 text-white hover:bg-red-600"
					onclick={() => resolveVoiceApprove('confirm')}
				>Подтвердить</button>
			</div>
		</div>
	</div>
{/if}

{#if $voiceModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" data-testid="voice-modal">
		<div class="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-xl border border-indigo-800/60 bg-gray-900 p-5 shadow-xl">
			<div class="flex items-start justify-between gap-3 mb-3">
				<h2 class="text-base font-semibold text-indigo-200">
					{$voiceModal.title || 'Ответ агентов'}
				</h2>
				<button type="button" class="text-gray-500 hover:text-gray-300" onclick={closeVoiceModal}>✕</button>
			</div>

			{#if $voiceModal.module}
				<div class="text-xs text-gray-500 mb-2">Модуль: <span class="text-indigo-400">{$voiceModal.module}</span></div>
			{/if}

			{#if $voiceModal.agents_used?.length}
				<div class="flex flex-wrap gap-1 mb-3">
					{#each $voiceModal.agents_used as agent}
						<span class="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/50">{agent}</span>
					{/each}
				</div>
			{/if}

			{#if $voiceModal.payload?.synthesis}
				<section class="mb-4 rounded-lg border border-emerald-900/50 bg-emerald-950/20 p-4" data-testid="voice-synthesis">
					<h3 class="text-xs uppercase text-emerald-500/90 mb-2">Решение</h3>
					{#if $voiceModal.payload.synthesis.decision}
						<p class="text-sm text-emerald-100 font-medium mb-2">{$voiceModal.payload.synthesis.decision}</p>
					{/if}
					{#if $voiceModal.payload.synthesis.next_action}
						<p class="text-xs text-gray-300 mb-2">
							<span class="text-gray-500">Следующий шаг:</span>
							{$voiceModal.payload.synthesis.next_action}
						</p>
					{/if}
					<div class="flex flex-wrap gap-2 text-[10px] uppercase mb-2">
						{#if $voiceModal.payload.synthesis.priority}
							<span class="px-2 py-0.5 rounded bg-gray-800 text-gray-300">
								Приоритет: {priorityLabels[$voiceModal.payload.synthesis.priority] || $voiceModal.payload.synthesis.priority}
							</span>
						{/if}
						{#if $voiceModal.payload.synthesis.urgency}
							<span class="px-2 py-0.5 rounded bg-gray-800 text-gray-300">
								Срок: {$voiceModal.payload.synthesis.urgency}
							</span>
						{/if}
					</div>
					{#if $voiceModal.payload.synthesis.rationale}
						<p class="text-xs text-gray-400 whitespace-pre-wrap">{$voiceModal.payload.synthesis.rationale}</p>
					{/if}
					{#if $voiceModal.payload.synthesis.coach_tip}
						<p class="text-xs text-amber-400/90 mt-2 italic">💡 {$voiceModal.payload.synthesis.coach_tip}</p>
					{/if}
				</section>
			{/if}

			{#if $voiceModal.reply}
				<p class="text-sm text-gray-200 mb-4 whitespace-pre-wrap">{$voiceModal.reply}</p>
			{/if}

			{#if $voiceModal.payload?.rag_answer}
				<section class="mb-4">
					<h3 class="text-xs uppercase text-gray-500 mb-1">База знаний</h3>
					<pre class="text-xs text-gray-300 bg-gray-950/80 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">{$voiceModal.payload.rag_answer}</pre>
				</section>
			{/if}

			{#if $voiceModal.payload?.analysis}
				<section class="mb-4">
					<h3 class="text-xs uppercase text-gray-500 mb-1">Анализ</h3>
					<pre class="text-xs text-gray-300 bg-gray-950/80 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">{summaryText($voiceModal.payload.analysis)}</pre>
				</section>
			{/if}

			{#if $voiceModal.payload?.economics}
				<section class="mb-4">
					<h3 class="text-xs uppercase text-gray-500 mb-1">Экономист</h3>
					<pre class="text-xs text-gray-300 bg-gray-950/80 rounded-lg p-3 whitespace-pre-wrap">{summaryText($voiceModal.payload.economics)}</pre>
				</section>
			{/if}

			{#if $voiceModal.payload?.tech}
				<section class="mb-4">
					<h3 class="text-xs uppercase text-gray-500 mb-1">Тех. специалист</h3>
					<pre class="text-xs text-gray-300 bg-gray-950/80 rounded-lg p-3 whitespace-pre-wrap">{summaryText($voiceModal.payload.tech)}</pre>
				</section>
			{/if}

			{#if $voiceModal.payload?.strategy}
				<section class="mb-4">
					<h3 class="text-xs uppercase text-gray-500 mb-1">Стратег</h3>
					<pre class="text-xs text-gray-300 bg-gray-950/80 rounded-lg p-3 whitespace-pre-wrap">{summaryText($voiceModal.payload.strategy)}</pre>
				</section>
			{/if}

			{#if $voiceModal.payload?.history}
				<section class="mb-4">
					<h3 class="text-xs uppercase text-gray-500 mb-1">История лида</h3>
					<div class="text-xs text-gray-300 bg-gray-950/80 rounded-lg p-3 space-y-2 max-h-48 overflow-y-auto">
						{#each ($voiceModal.payload.history.audit || []).slice(0, 8) as row}
							<div class="border-b border-gray-800/80 pb-1">
								<span class="text-amber-500/90">{row.field || row.fieldName}</span>
								<span class="text-gray-600"> → </span>
								<span>{row.newValue || row.new_value || '—'}</span>
							</div>
						{/each}
						{#each ($voiceModal.payload.history.comments || []).slice(0, 5) as c}
							<div class="text-gray-400">💬 {c.body || c.text}</div>
						{/each}
						{#each ($voiceModal.payload.history.communications || []).slice(0, 5) as c}
							<div class="text-gray-400">✆ {c.communicationType || c.communication_type}: {c.content}</div>
						{/each}
					</div>
				</section>
			{/if}

			{#if $voiceModal.payload?.draft_email}
				<section class="mb-4">
					<h3 class="text-xs uppercase text-gray-500 mb-1">Черновик письма</h3>
					<div class="text-sm text-gray-200 bg-gray-950/80 rounded-lg p-3 space-y-2">
						<div><span class="text-gray-500">Тема:</span> {$voiceModal.payload.draft_email.subject || '—'}</div>
						<pre class="text-xs whitespace-pre-wrap">{$voiceModal.payload.draft_email.body || ''}</pre>
					</div>
				</section>
			{/if}

			<div class="flex flex-wrap justify-end gap-2 pt-2">
				{#each ($voiceModal.payload?.actions || ['reject']) as act}
					<button
						type="button"
						class="px-3 py-1.5 text-sm rounded-lg
							{act === 'send' ? 'bg-indigo-600 text-white hover:bg-indigo-500' :
							 act === 'reject' ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' :
							 'bg-gray-700 text-gray-200 hover:bg-gray-600'}"
						onclick={() => modalAction(act)}
					>
						{act === 'send' ? 'Отправить' : act === 'save' ? 'Закрыть' : 'Отмена'}
					</button>
				{/each}
			</div>
		</div>
	</div>
{/if}
