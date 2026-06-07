<script>
	import { onMount } from 'svelte';
	import { getApiUrl } from '$lib/websocket.js';

	const API = getApiUrl();

	let loading = $state(true);
	let saving = $state(false);
	let err = $state('');
	let ok = $state('');

	let stagesText = $state('');
	let crit = $state(130);
	let high = $state(70);
	let med = $state(30);
	let scoreMin = $state(0);
	let scoreMax = $state(100);
	let defaultScore = $state(50);
	let notes = $state('');
	let rulesJson = $state('[]');
	let bitrixOk = $state(false);
	let bitrixMasked = $state(null);

	async function load() {
		loading = true;
		err = '';
		try {
			const r = await fetch(`${API}/api/ops/crm-settings`);
			if (!r.ok) throw new Error(await r.text());
			const d = await r.json();
			const s = d.settings || {};
			stagesText = (s.stages || []).join('\n');
			const p = s.priority_thresholds || {};
			crit = p.critical ?? 130;
			high = p.high ?? 70;
			med = p.medium ?? 30;
			scoreMin = s.score_range?.min ?? 0;
			scoreMax = s.score_range?.max ?? 100;
			defaultScore = s.default_new_lead_score ?? 50;
			notes = s.notes ?? '';
			rulesJson = JSON.stringify(s.stage_transition_rules ?? [], null, 2);
			bitrixOk = !!d.bitrix_webhook_configured;
			bitrixMasked = d.bitrix_webhook_masked || null;
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			loading = false;
		}
	}

	async function save() {
		saving = true;
		ok = '';
		err = '';
		try {
			const stages = stagesText
				.split('\n')
				.map((x) => x.trim())
				.filter(Boolean);
			let stage_transition_rules;
			try {
				stage_transition_rules = JSON.parse(rulesJson || '[]');
			} catch (e) {
				throw new Error('Правила переходов стадий: невалидный JSON');
			}
			if (!Array.isArray(stage_transition_rules)) {
				throw new Error('Правила переходов: ожидается JSON-массив объектов');
			}
			const body = {
				stages,
				priority_thresholds: { critical: crit, high: high, medium: med },
				score_range: { min: scoreMin, max: scoreMax },
				default_new_lead_score: defaultScore,
				notes: notes.trim(),
				stage_transition_rules,
			};
			const r = await fetch(`${API}/api/ops/crm-settings`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(body),
			});
			if (!r.ok) {
				const t = await r.text();
				let detail = t;
				try {
					const j = JSON.parse(t);
					detail = j.detail || t;
				} catch {
					/* ignore */
				}
				throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
			}
			ok = 'Сохранено';
			setTimeout(() => (ok = ''), 3000);
		} catch (e) {
			err = e?.message || String(e);
		} finally {
			saving = false;
		}
	}

	onMount(load);
</script>

<div class="p-6 max-w-3xl mx-auto space-y-6">
	<div>
		<h2 class="text-lg font-semibold text-white">Настройки CRM</h2>
		<p class="text-sm text-gray-500 mt-1">
			Тюнинг воронки и порогов (файл <code class="text-gray-600">backend/data/crm_settings.json</code>). Карточки
			лидов в UI по-прежнему берут этапы из кода фронта — при необходимости синхронизируйте список вручную или
			подключите загрузку этапов из API позже.
		</p>
	</div>

	{#if loading}
		<p class="text-gray-500 text-sm">Загрузка…</p>
	{:else}
		<div class="rounded-xl border border-gray-800 bg-gray-950/50 p-5 space-y-4">
			<div>
				<label class="block text-xs text-gray-500 mb-1">Битрикс24 (вебхук)</label>
				<p class="text-sm">
					{#if bitrixOk}
						<span class="text-green-400">Подключён</span>
						{#if bitrixMasked}
							<span class="text-gray-500 ml-2 font-mono text-xs">{bitrixMasked}</span>
						{/if}
					{:else}
						<span class="text-amber-400">Не задан</span>
						<span class="text-gray-600 text-xs ml-2">— укажите BITRIX24_WEBHOOK_URL в .env</span>
					{/if}
				</p>
			</div>

			<div>
				<label class="block text-xs text-gray-500 mb-1">Этапы воронки (по одному в строке)</label>
				<textarea
					bind:value={stagesText}
					rows="8"
					class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white font-mono"
				></textarea>
			</div>

			<div>
				<label class="block text-xs text-gray-500 mb-1">
					Правила перехода в стадию (JSON-массив). Поля: <code class="text-gray-600">to_stage</code>,
					<code class="text-gray-600">require_non_empty</code> (ORM-имена: email, company, description…),
					<code class="text-gray-600">require_positive_amount_rub</code>
				</label>
				<textarea
					bind:value={rulesJson}
					rows="10"
					class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white font-mono"
				></textarea>
			</div>

			<div class="grid grid-cols-3 gap-3">
				<div>
					<label class="block text-xs text-gray-500 mb-1">Critical ≥</label>
					<input type="number" bind:value={crit} class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white" />
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">High ≥</label>
					<input type="number" bind:value={high} class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white" />
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">Medium ≥</label>
					<input type="number" bind:value={med} class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white" />
				</div>
			</div>

			<div class="grid grid-cols-2 gap-3">
				<div>
					<label class="block text-xs text-gray-500 mb-1">Скоринг мин</label>
					<input type="number" bind:value={scoreMin} class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white" />
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">Скоринг макс</label>
					<input type="number" bind:value={scoreMax} class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white" />
				</div>
			</div>

			<div>
				<label class="block text-xs text-gray-500 mb-1">Скор по умолчанию для нового лида</label>
				<input type="number" bind:value={defaultScore} class="max-w-xs rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white" />
			</div>

			<div>
				<label class="block text-xs text-gray-500 mb-1">Заметки для команды</label>
				<textarea
					bind:value={notes}
					rows="3"
					class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
				></textarea>
			</div>

			{#if err}
				<div class="text-red-400 text-sm">{err}</div>
			{/if}
			{#if ok}
				<div class="text-green-400 text-sm">{ok}</div>
			{/if}

			<button
				type="button"
				onclick={save}
				disabled={saving}
				class="px-5 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium disabled:opacity-50"
			>
				{saving ? 'Сохранение…' : 'Сохранить'}
			</button>
		</div>
	{/if}
</div>
