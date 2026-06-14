<script>
	/** Панель версий промпта: список, откат, сравнение. */
	let {
		api = '',
		promptBasePath = '',
		onRestored = () => {},
	} = $props();

	let versions = $state([]);
	let loading = $state(false);
	let msg = $state('');
	let compareLeft = $state('current');
	let compareRight = $state('');
	let compareResult = $state(null);
	let comparing = $state(false);

	async function loadVersions() {
		if (!promptBasePath) return;
		loading = true;
		msg = '';
		try {
			const r = await fetch(`${api}${promptBasePath}/versions`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			versions = d.versions || [];
			if (versions.length && !compareRight) {
				compareRight = versions[0].id;
			}
		} catch (e) {
			msg = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	async function restoreVersion(versionId) {
		if (!promptBasePath || !confirm(`Откатить промпт к ${versionId}?`)) return;
		msg = '';
		try {
			const r = await fetch(`${api}${promptBasePath}/versions/${versionId}/restore`, { method: 'POST' });
			if (!r.ok) throw new Error(await r.text());
			msg = `✓ Откат к ${versionId}`;
			await loadVersions();
			onRestored();
		} catch (e) {
			msg = e instanceof Error ? e.message : String(e);
		}
	}

	async function runCompare() {
		if (!promptBasePath || !compareLeft || !compareRight) return;
		comparing = true;
		compareResult = null;
		try {
			const q = new URLSearchParams({ left: compareLeft, right: compareRight });
			const r = await fetch(`${api}${promptBasePath}/versions/compare?${q}`);
			if (!r.ok) throw new Error(await r.text());
			compareResult = await r.json();
		} catch (e) {
			msg = e instanceof Error ? e.message : String(e);
		} finally {
			comparing = false;
		}
	}

	function fmtTs(ts) {
		if (!ts) return '—';
		return new Date(ts * 1000).toLocaleString('ru-RU', {
			day: '2-digit',
			month: 'short',
			hour: '2-digit',
			minute: '2-digit',
		});
	}

	$effect(() => {
		if (promptBasePath) loadVersions();
	});
</script>

<div class="rounded-xl border border-gray-800 bg-gray-900/40 p-4 space-y-3" data-testid="prompt-versions-panel">
	<h4 class="text-sm font-medium text-white">История версий</h4>
	<p class="text-xs text-gray-500">Каждое сохранение создаёт снимок. Откат без перезапуска сервера.</p>

	{#if loading}
		<p class="text-xs text-gray-600">Загрузка…</p>
	{:else if !versions.length}
		<p class="text-xs text-gray-600">Версий пока нет — сохраните промпт.</p>
	{:else}
		<ul class="space-y-2 max-h-40 overflow-y-auto">
			{#each versions as v}
				<li class="flex items-center justify-between gap-2 text-xs border border-gray-800 rounded-lg px-2 py-1.5">
					<div class="min-w-0">
						<span class="text-indigo-300 font-mono">{v.id}</span>
						<span class="text-gray-600 ml-2">{fmtTs(v.ts)} · {v.chars} симв.</span>
						{#if v.note}
							<span class="text-gray-500 ml-1">({v.note})</span>
						{/if}
					</div>
					<button
						type="button"
						data-testid="prompt-version-restore"
						class="shrink-0 text-emerald-400 hover:text-emerald-300"
						onclick={() => restoreVersion(v.id)}
					>↩ откат</button>
				</li>
			{/each}
		</ul>
	{/if}

	<div class="border-t border-gray-800 pt-3 space-y-2">
		<p class="text-xs font-medium text-gray-400">Сравнение</p>
		<div class="flex flex-wrap gap-2 items-center text-xs">
			<select bind:value={compareLeft} class="rounded border border-gray-700 bg-gray-950 px-2 py-1 text-gray-200">
				<option value="current">текущий</option>
				<option value="builtin">встроенный</option>
				{#each versions as v}
					<option value={v.id}>{v.id}</option>
				{/each}
			</select>
			<span class="text-gray-600">vs</span>
			<select bind:value={compareRight} class="rounded border border-gray-700 bg-gray-950 px-2 py-1 text-gray-200">
				<option value="current">текущий</option>
				<option value="builtin">встроенный</option>
				{#each versions as v}
					<option value={v.id}>{v.id}</option>
				{/each}
			</select>
			<button
				type="button"
				data-testid="prompt-version-compare"
				disabled={comparing || !compareLeft || !compareRight}
				class="rounded bg-gray-800 px-2 py-1 text-gray-300 hover:bg-gray-700 disabled:opacity-40"
				onclick={runCompare}
			>{comparing ? '…' : 'Сравнить'}</button>
		</div>
		{#if compareResult}
			<div class="text-xs text-gray-400" data-testid="prompt-version-diff-stats">
				+{compareResult.added_lines} / −{compareResult.removed_lines} строк
				· {compareResult.left_chars} → {compareResult.right_chars} симв.
			</div>
			<pre class="text-[10px] text-gray-500 max-h-32 overflow-auto rounded bg-gray-950 p-2 font-mono">{compareResult.diff?.join('\n')}</pre>
		{/if}
	</div>

	{#if msg}
		<p class="text-xs {msg.startsWith('✓') ? 'text-emerald-400' : 'text-red-400'}">{msg}</p>
	{/if}
</div>
