<script>
	/** @type {{ preview: Record<string, string> | null, loading?: boolean, onConfirm?: () => void, onCancel?: () => void }} */
	let { preview = null, loading = false, onConfirm = () => {}, onCancel = () => {} } = $props();
</script>

{#if preview}
	<div
		class="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-4"
		role="dialog"
		aria-modal="true"
		data-testid="email-approve-modal"
	>
		<div class="w-full max-w-lg rounded-2xl border border-amber-800/60 bg-gray-950 p-5 shadow-2xl">
			<h2 class="text-base font-semibold text-amber-200 mb-3">{preview.title || 'Подтверждение'}</h2>
			<div class="space-y-2 text-sm text-gray-300 mb-4">
				{#if preview.to}
					<p><span class="text-gray-500">Кому:</span> {preview.to}</p>
				{/if}
				{#if preview.subject}
					<p><span class="text-gray-500">Тема:</span> {preview.subject}</p>
				{/if}
				{#if preview.body}
					<div class="rounded-lg border border-gray-800 bg-gray-900/80 px-3 py-2 max-h-40 overflow-y-auto">
						<p class="whitespace-pre-wrap text-xs text-gray-200">{preview.body}</p>
					</div>
				{/if}
			</div>
			<div class="flex justify-end gap-2">
				<button
					type="button"
					data-testid="email-approve-reject"
					class="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700"
					disabled={loading}
					onclick={onCancel}
				>Отмена</button>
				<button
					type="button"
					data-testid="email-approve-confirm"
					class="px-3 py-1.5 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 disabled:bg-gray-700"
					disabled={loading}
					onclick={onConfirm}
				>{loading ? 'Отправка...' : 'Отправить'}</button>
			</div>
		</div>
	</div>
{/if}
