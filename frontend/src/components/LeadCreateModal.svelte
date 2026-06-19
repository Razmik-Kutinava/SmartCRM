<script>
	import {
		leadCreateOpen,
		leadCreateSource,
		closeLeadCreateModal,
		notifyLeadCreated,
	} from '$lib/leads/leadCreateUi.js';
	import { apiCreateLead, readLeadsCache, writeLeadsCache } from '$lib/leadsStorage.js';
	import {
		CRM_STAGES,
		DEFAULT_CRM_STAGES,
		loadCrmConfig,
		getCachedCrmConfig,
	} from '$lib/crmStages.js';
	import { fetchLeadIndustries } from '$lib/leads/industryCatalog.js';

	let company = $state('');
	let contact = $state('');
	let email = $state('');
	let phone = $state('');
	let stage = $state('Новый');
	let budget = $state('');
	let city = $state('');
	let industry = $state('');
	let description = $state('');
	let industryOptions = $state([]);
	let busy = $state(false);
	let error = $state('');
	let success = $state('');

	const open = $derived($leadCreateOpen);
	const stages = $derived(CRM_STAGES.length ? CRM_STAGES : DEFAULT_CRM_STAGES);

	function resetForm() {
		company = '';
		contact = '';
		email = '';
		phone = '';
		stage = 'Новый';
		budget = '';
		city = '';
		industry = '';
		description = '';
		error = '';
		success = '';
	}

	$effect(() => {
		if (!open) return;
		resetForm();
		loadCrmConfig();
		fetchLeadIndustries().then((rows) => { industryOptions = rows; }).catch(() => { industryOptions = []; });
	});

	async function onSubmit(e) {
		e.preventDefault();
		const name = company.trim();
		if (!name) {
			error = 'Укажите название компании';
			return;
		}
		busy = true;
		error = '';
		success = '';
		const score = getCachedCrmConfig()?.default_new_lead_score ?? 50;
		const payload = {
			company: name,
			contact: contact.trim() || '—',
			email: email.trim() || '—',
			phone: phone.trim() || '—',
			stage: stage || 'Новый',
			score,
			source: $leadCreateSource || 'UI',
			budget: budget.trim() || '—',
			city: city.trim() || '—',
			industry: industry.trim() || '—',
			description: description.trim(),
		};
		try {
			const created = await apiCreateLead(payload);
			const cached = readLeadsCache().filter((l) => l.id !== created.id);
			writeLeadsCache([created, ...cached]);
			notifyLeadCreated(created);
			success = `Лид «${created.company}» сохранён в БД`;
			setTimeout(() => closeLeadCreateModal(), 600);
		} catch (err) {
			error = err?.message || String(err);
		} finally {
			busy = false;
		}
	}
</script>

{#if open}
	<div
		class="fixed inset-0 z-[110] flex items-center justify-center bg-black/70 p-4"
		role="dialog"
		aria-modal="true"
		data-testid="lead-create-modal"
	>
		<div class="w-full max-w-lg rounded-2xl border border-gray-800 bg-gray-950 p-5 shadow-2xl max-h-[90vh] overflow-y-auto">
			<h2 class="text-sm font-semibold text-white mb-1">Новый лид</h2>
			<p class="text-xs text-gray-500 mb-4">Запись в PostgreSQL через POST /api/leads</p>
			{#if error}<p class="text-xs text-red-300 mb-2" data-testid="lead-create-error">{error}</p>{/if}
			{#if success}<p class="text-xs text-green-300 mb-2" data-testid="lead-create-success">{success}</p>{/if}
			<form class="space-y-3" onsubmit={onSubmit}>
				<div>
					<label class="block text-xs text-gray-500 mb-1" for="lead-create-company">Компания *</label>
					<input
						id="lead-create-company"
						bind:value={company}
						required
						class="w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm text-white"
						placeholder="ООО Ромашка"
						data-testid="lead-create-company"
					/>
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="block text-xs text-gray-500 mb-1" for="lead-create-contact">Контакт</label>
						<input id="lead-create-contact" bind:value={contact} class="w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm text-white" />
					</div>
					<div>
						<label class="block text-xs text-gray-500 mb-1" for="lead-create-phone">Телефон</label>
						<input id="lead-create-phone" bind:value={phone} class="w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm text-white" />
					</div>
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1" for="lead-create-email">Email</label>
					<input id="lead-create-email" type="email" bind:value={email} class="w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm text-white" />
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="block text-xs text-gray-500 mb-1" for="lead-create-stage">Этап</label>
						<select id="lead-create-stage" bind:value={stage} class="w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm text-white">
							{#each stages as s (s)}<option value={s}>{s}</option>{/each}
						</select>
					</div>
					<div>
						<label class="block text-xs text-gray-500 mb-1" for="lead-create-budget">Бюджет</label>
						<input id="lead-create-budget" bind:value={budget} class="w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="500 000 ₽" />
					</div>
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="block text-xs text-gray-500 mb-1" for="lead-create-city">Город</label>
						<input id="lead-create-city" bind:value={city} class="w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm text-white" />
					</div>
					<div>
						<label class="block text-xs text-gray-500 mb-1" for="lead-create-industry">Отрасль</label>
						<input
							id="lead-create-industry"
							list="lead-create-industry-list"
							bind:value={industry}
							class="w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm text-white"
						/>
						<datalist id="lead-create-industry-list">
							{#each industryOptions as opt (opt)}<option value={opt}></option>{/each}
						</datalist>
					</div>
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1" for="lead-create-desc">Описание</label>
					<textarea id="lead-create-desc" bind:value={description} rows="2" class="w-full rounded-xl bg-gray-900 border border-gray-800 px-3 py-2 text-sm text-white"></textarea>
				</div>
				<div class="flex justify-end gap-2 pt-2">
					<button type="button" class="px-4 py-2 text-sm text-gray-400 hover:text-white" onclick={closeLeadCreateModal} disabled={busy}>Отмена</button>
					<button type="submit" class="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg disabled:opacity-50" disabled={busy} data-testid="lead-create-submit">
						{busy ? 'Сохраняю…' : 'Создать'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
