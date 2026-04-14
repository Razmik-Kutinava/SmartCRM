<script>
	import { onMount } from 'svelte';
	import {
		fetchLeads,
		apiCreateLead,
		apiUpdateLead,
		apiDeleteLead,
		apiImportBitrix,
		fetchBitrixImportStats,
		readLeadsCache,
		writeLeadsCache,
	} from '$lib/leadsStorage.js';
	import { getApiUrl, onMessage } from '$lib/websocket.js';

	const API = getApiUrl();

	let search = $state('');
	let filterStage = $state('all');
	let showVoice = $state(false); // голос теперь глобальный — в layout
	let notification = $state(null); // { text, type: 'success'|'error'|'info' }
	let editingLead = $state(null); // лид в режиме редактирования
	let apiError = $state(false); // флаг недоступности API
	let bitrixImporting = $state(false);
	/** @type {{ bitrix_total: number | null, local_bitrix_leads_count: number, date_from?: string } | null} */
	let bitrixStats = $state(null);

	const stages = ['all', 'Новый', 'Квалифицирован', 'КП отправлено', 'Переговоры', 'Выигран', 'Проигран'];

	// Сразу показываем кэш, потом перезаписываем данными из БД
	let leads = $state(readLeadsCache());

	onMount(async () => {
		try {
			const fresh = await fetchLeads();
			leads = fresh;
			apiError = false;
			console.log('[leads] загружено из БД:', fresh.length);
		} catch (e) {
			console.error('[leads] fetchLeads ошибка:', e);
			apiError = true;
		}
		try {
			bitrixStats = await fetchBitrixImportStats('2023-01-01');
		} catch {
			bitrixStats = null;
		}

		// Подписываемся на глобальный голосовой ввод — обрабатываем intent-события
		const unsub = onMessage((data) => {
			if (data.type === 'intent' && data.intent) {
				handleVoiceResult(data);
			}
		});
		return unsub;
	});

	let filtered = $derived(leads.filter(l => {
		const q = search.toLowerCase();
		const desc = (l.description || '').toLowerCase();
		const city = (l.city || '').toLowerCase();
		const industry = (l.industry || '').toLowerCase();
		const matchSearch =
			!q ||
			l.company.toLowerCase().includes(q) ||
			l.contact.toLowerCase().includes(q) ||
			desc.includes(q) ||
			city.includes(q) ||
			industry.includes(q);
		const matchStage = filterStage === 'all' || l.stage === filterStage;
		return matchSearch && matchStage;
	}));

	function notify(text, type = 'success') {
		notification = { text, type };
		setTimeout(() => notification = null, 4000);
	}

	async function runBitrixImport() {
		if (bitrixImporting) return;
		bitrixImporting = true;
		try {
			const res = await apiImportBitrix({ date_from: '2023-01-01', max_items: 0 });
			const fresh = await fetchLeads();
			leads = fresh;
			writeLeadsCache(leads);
			try {
				bitrixStats = await fetchBitrixImportStats('2023-01-01');
			} catch {
				bitrixStats = null;
			}
			const bx = res.bitrix_total != null ? String(res.bitrix_total) : '?';
			const loc = res.local_bitrix_leads_count != null ? String(res.local_bitrix_leads_count) : '?';
			const line1 = `Битрикс (фильтр с 2023): ${bx} лидов | у нас с Bitrix ID: ${loc}`;
			const line2 = `Импорт: +${res.imported} новых, обновлено ${res.updated}, обработано ${res.total_processed}${res.unlimited ? ' (без лимита)' : ''}`;
			notify(`${line1} — ${line2}`, 'info');
			if (res.sync_note) notify(res.sync_note, 'info');
			if (res.error_count > 0) {
				notify(`Предупреждения импорта: ${res.error_count} (см. лог бэкенда)`, 'error');
			}
		} catch (e) {
			console.error('[leads] Bitrix import:', e);
			notify(`Импорт Битрикс24: ${e.message}`, 'error');
		} finally {
			bitrixImporting = false;
		}
	}

	/** Слишком общие формы — не матчим по одному слову (иначе «ООО» бьёт в любую компанию) */
	const GENERIC_ORG_MARKERS = new Set(['ооо', 'зао', 'ао', 'оао', 'ип', 'гк', 'пао', 'нко']);

	/** Убираем кавычки/ёлочки для сравнения с тем, что приходит от Hermes/Whisper */
	function stripCompanyNoise(s) {
		return String(s || '')
			.replace(/[«»""„"'`]/g, ' ')
			.replace(/\s+/g, ' ')
			.trim();
	}

	function companyNorm(s) {
		return stripCompanyNoise(s).toLowerCase();
	}

	/**
	 * Поиск лида для update/delete.
	 * По компании / id / lead_id — всегда по полному списку `leads`, иначе при фильтре таблицы
	 * лид «пропадает» из выборки и правки перестают находиться.
	 * Параметр visibleForRow — только для «номер N» = N-я строка текущей таблицы (filtered).
	 */
	function findLead(slots, visibleForRow = filtered) {
		if (!slots) return null;

		const full = leads;
		const rowList = visibleForRow ?? full;

		if (slots.id != null && slots.id !== '') {
			const id = Number(slots.id);
			if (!Number.isNaN(id)) return full.find((l) => l.id === id);
		}

		if (slots.lead_id != null && slots.lead_id !== '') {
			const lidRaw = String(slots.lead_id).trim();
			if (/^\d+$/.test(lidRaw)) {
				const idNum = parseInt(lidRaw, 10);
				const found = full.find((l) => l.id === idNum);
				if (found) return found;
			}
			const q = companyNorm(lidRaw);
			if (q.length >= 2 && !GENERIC_ORG_MARKERS.has(q)) {
				const matches = full.filter((l) => companyNorm(l.company).includes(q));
				if (matches.length === 1) return matches[0];
				const exact = full.find((l) => companyNorm(l.company) === q);
				if (exact) return exact;
				if (matches.length > 1) return null;
			}
		}

		const raw = stripCompanyNoise(slots.company || '');
		if (raw.length > 0) {
			const q = raw.toLowerCase();
			if (GENERIC_ORG_MARKERS.has(q)) return null;

			// Точное совпадение
			const exact = full.find((l) => companyNorm(l.company) === q);
			if (exact) return exact;

			// Частичное включение
			const matches = full.filter((l) => companyNorm(l.company).includes(q));
			if (matches.length === 1) return matches[0];
			if (matches.length > 1) return null;

			// Fuzzy без пробелов: "ЭдуардСтрой" → "эдуардстрой" матчит "эдуард строй"
			const qNoSpace = q.replace(/\s+/g, '');
			if (qNoSpace.length >= 3) {
				const fuzzy = full.filter((l) => {
					const cn = companyNorm(l.company).replace(/\s+/g, '');
					return cn.includes(qNoSpace) || qNoSpace.includes(cn);
				});
				if (fuzzy.length === 1) return fuzzy[0];
			}
		}

		if (slots.number != null && slots.number !== '') {
			const n = Number(slots.number);
			if (Number.isInteger(n) && n >= 1 && n <= rowList.length) return rowList[n - 1];
		}
		return null;
	}

	/** Hermes отдаёт пару field+value — маппим на поля карточки */
	function patchFromFieldValue(fieldRaw, valueRaw) {
		const v = String(valueRaw ?? '').trim();
		if (!v) return {};
		const f = String(fieldRaw ?? '')
			.toLowerCase()
			.replace(/ё/g, 'е');

		if (/почт|email|e-mail|@|mail/.test(f)) return { email: v };
		if (/телефон|номер|phone|мобил|\+7/.test(f)) return { phone: v };
		if (/контакт|contact|имя\s+лица/.test(f)) return { contact: v };
		if (/стади|этап|stage|воронк/.test(f)) return { stage: v };
		if (/бюджет|сумм|budget/.test(f)) return { budget: v };
		if (/скоринг|score|балл/.test(f)) {
			const n = parseInt(v, 10);
			return Number.isNaN(n) ? {} : { score: n };
		}
		if (/компани|название|юр|firm/.test(f)) return { company: v };
		if (/город|city/.test(f)) return { city: v };
		if (/отрасл|industry|сфер/.test(f)) return { industry: v };
		if (v.includes('@')) return { email: v };
		return {};
	}

	function buildUpdatePatch(slots) {
		const p = {};
		if (slots?.stage) p.stage = slots.stage;
		if (slots?.contact) p.contact = slots.contact;
		if (slots?.email) p.email = slots.email;
		if (slots?.phone) p.phone = slots.phone;
		if (slots?.budget) p.budget = slots.budget;
		if (slots?.score != null && slots.score !== '') p.score = Number(slots.score);
		// Hermes: слот note → поле description в БД
		if (slots?.note != null && String(slots.note).trim()) {
			p.description = String(slots.note).trim();
		}
		if (slots?.next_call != null && String(slots.next_call).trim()) {
			p.next_call = String(slots.next_call).trim();
		}
		if (slots?.city != null && String(slots.city).trim()) {
			p.city = String(slots.city).trim();
		}
		if (slots?.industry != null && String(slots.industry).trim()) {
			p.industry = String(slots.industry).trim();
		}
		const fv = patchFromFieldValue(slots?.field, slots?.value);
		return { ...fv, ...p };
	}

	// ── Обработчик голосовых интентов ──────────────────────────────
	async function handleVoiceResult(data) {
		const { intent, slots, reply } = data;

		switch (intent) {

			case 'create_lead': {
				const company = stripCompanyNoise(slots?.company || '');
				if (!company) {
					notify('Название компании не распознано — скажи, например: «создай лид ООО Ромашка»', 'error');
					return;
				}
				const noteText = slots?.note != null ? String(slots.note).trim() : '';
				const nextCallText =
					slots?.next_call != null ? String(slots.next_call).trim() : '';
				const cityText = slots?.city != null ? String(slots.city).trim() : '';
				const industryText = slots?.industry != null ? String(slots.industry).trim() : '';
				const payload = {
					company,
					contact: slots.contact || '—',
					email: slots.email || '—',
					phone: slots.phone || '—',
					stage: slots.stage || 'Новый',
					score: 50,
					source: 'Голосовая команда',
					budget: slots.budget || '—',
					city: cityText || '—',
					industry: industryText || '—',
					description: noteText,
					next_call: nextCallText || '—',
				};
				// Оптимистичное обновление — лид виден сразу
				const tempId = -(Date.now());
				const tempLead = { ...payload, id: tempId, created: new Date().toLocaleDateString('ru-RU') };
				leads = [tempLead, ...leads];
				notify(`Создаю лид: ${company}…`, 'info');
				try {
					const created = await apiCreateLead(payload);
					// Заменяем временный лид настоящим из БД
					leads = leads.map(l => l.id === tempId ? created : l);
					writeLeadsCache(leads);
					notify(`✓ Лид сохранён в БД: ${created.company}`);
				} catch (e) {
					console.error('[leads] apiCreateLead ошибка:', e);
					// Убираем временный лид, показываем ошибку
					leads = leads.filter(l => l.id !== tempId);
					notify(`Ошибка сохранения: ${e.message}`, 'error');
				}
				break;
			}

			case 'update_lead': {
				const lead = findLead(slots);
				if (!lead) {
					notify('Лид не найден — уточни компанию или номер в списке', 'error');
					return;
				}
				const patch = buildUpdatePatch(slots);
				if (Object.keys(patch).length === 0) {
					notify('Не указано, что менять (почта, телефон, этап, контакт)', 'error');
					return;
				}
				// Оптимистичное обновление
				const prevLeads = leads;
				leads = leads.map((l) => (l.id !== lead.id ? l : { ...l, ...patch }));
				notify(`Обновляю: ${lead.company}…`, 'info');
				try {
					const updated = await apiUpdateLead(lead.id, patch);
					leads = leads.map((l) => (l.id !== lead.id ? l : { ...l, ...updated }));
					writeLeadsCache(leads);
					notify(`✓ Лид обновлён: ${lead.company}`);
				} catch (e) {
					console.error('[leads] apiUpdateLead ошибка:', e);
					leads = prevLeads;
					notify(`Ошибка обновления: ${e.message}`, 'error');
				}
				break;
			}

			case 'delete_lead': {
				const lead = findLead(slots);
				if (!lead) { notify('Лид не найден', 'error'); return; }
				const prevLeads2 = leads;
				leads = leads.filter(l => l.id !== lead.id);
				notify(`Удаляю: ${lead.company}…`, 'info');
				try {
					await apiDeleteLead(lead.id);
					writeLeadsCache(leads);
					notify(`✓ Лид удалён: ${lead.company}`, 'info');
				} catch (e) {
					console.error('[leads] apiDeleteLead ошибка:', e);
					leads = prevLeads2;
					notify(`Ошибка удаления: ${e.message}`, 'error');
				}
				break;
			}

		case 'list_leads': {
			const f = slots?.filter;
			const q = slots?.query ? String(slots.query).trim() : '';
			if (f === 'hot' || f === 'горячих') {
				filterStage = 'Квалифицирован';
				notify('Показываю горячих лидов');
			} else if (f === 'cold' || f === 'холодных') {
				filterStage = 'Новый';
				notify('Показываю холодных лидов');
			} else if (f === 'new' || f === 'новых') {
				filterStage = 'Новый';
				notify('Показываю новых лидов');
			} else if (f === 'won' || f === 'выигранных') {
				filterStage = 'Выигран';
				notify('Показываю выигранные сделки');
			} else {
				filterStage = 'all';
				notify('Показываю всех лидов');
			}
			if (q) {
				search = q;
				notify(`Фильтр по запросу: ${q}`);
			}
			break;
		}

			case 'create_task': {
				const title = slots?.title || '';
				if (!title) {
					notify('Не указано название задачи', 'error');
					return;
				}
				try {
					const r = await fetch(`${API}/api/tasks`, {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({
							title,
							due: slots?.due || '—',
							assignee: slots?.assignee || 'Я',
							related_lead: slots?.related_lead || '',
							note: slots?.note || '',
						})
					});
					const task = await r.json();
					notify(`✓ Задача создана: ${task.title}`);
				} catch (e) {
					notify(`Ошибка создания задачи: ${e.message}`, 'error');
				}
				break;
			}

			case 'list_tasks': {
				// Открываем страницу задач или показываем уведомление
				notify('Задачи — раздел в разработке. Используй голос для создания задач.', 'info');
				break;
			}

			case 'update_task': {
				notify(reply || 'Обновление задач — в разработке', 'info');
				break;
			}

			case 'delete_task': {
				notify(reply || 'Удаление задач — в разработке', 'info');
				break;
			}

			case 'write_email':
			case 'run_analysis':
			case 'ask_strategist':
			case 'search_web':
				notify(reply || `Агент выполняет: ${intent}`, 'info');
				break;

			case 'noop':
				notify(reply || 'Команда не распознана', 'error');
				break;

			default:
				notify(reply || `Выполняю: ${intent}`, 'info');
		}
	}

	function stageColor(stage) {
		const map = {
			'Новый': 'bg-gray-700 text-gray-300',
			'Квалифицирован': 'bg-blue-900 text-blue-300',
			'КП отправлено': 'bg-yellow-900 text-yellow-300',
			'Переговоры': 'bg-indigo-900 text-indigo-300',
			'Выигран': 'bg-green-900 text-green-300',
			'Проигран': 'bg-red-900 text-red-300',
		};
		return map[stage] || 'bg-gray-700 text-gray-300';
	}

	function scoreColor(score) {
		if (score >= 80) return 'text-green-400';
		if (score >= 55) return 'text-yellow-400';
		return 'text-red-400';
	}

	function deleteLead(lead) {
		leads = leads.filter(l => l.id !== lead.id);
		notify(`Лид удалён: ${lead.company}`, 'info');
	}
</script>

<!-- Header -->
<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900 shrink-0">
	<div>
		<h1 class="text-lg font-semibold text-white">Лиды</h1>
		<p class="text-xs text-gray-500">{filtered.length} из {leads.length}</p>
		{#if bitrixStats}
			<p class="text-[11px] text-gray-600 mt-0.5" title={bitrixStats.hint || ''}>
				Битрикс (≥2023): <span class="text-gray-400">{bitrixStats.bitrix_total ?? '—'}</span>
				· У нас Bitrix-ID: <span class="text-gray-400">{bitrixStats.local_bitrix_leads_count ?? '—'}</span>
			</p>
		{/if}
	</div>
	<div class="flex items-center gap-2">
		<button
			type="button"
			disabled={bitrixImporting}
			onclick={runBitrixImport}
			class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-sm text-gray-300 rounded-lg"
			title="Нужен BITRIX24_WEBHOOK_URL на сервере"
		>{bitrixImporting ? '⏳ Битрикс24…' : '📤 Битрикс24'}</button>
		<button class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg">📥 Экспорт</button>
		<button
			onclick={() => {
				const name = prompt('Компания:');
				if (name) handleVoiceResult({ intent: 'create_lead', slots: { company: name }, reply: '' });
			}}
			class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg"
		>+ Новый лид</button>
	</div>
</div>

<!-- API error banner -->
{#if apiError}
	<div class="px-6 py-2 shrink-0 text-sm bg-yellow-950 text-yellow-300 border-b border-yellow-900 flex items-center gap-2">
		⚠ База данных недоступна — показываю кэш. Изменения не сохранятся.
	</div>
{/if}

<!-- Notification -->
{#if notification}
	<div class="px-6 py-2 shrink-0 text-sm flex items-center gap-2
		{notification.type === 'success' ? 'bg-green-950 text-green-300 border-b border-green-900' :
		 notification.type === 'error'   ? 'bg-red-950 text-red-300 border-b border-red-900' :
		                                   'bg-gray-900 text-gray-300 border-b border-gray-800'}">
		{notification.text}
	</div>
{/if}

<!-- Filters -->
<div class="flex items-center gap-3 px-6 py-3 border-b border-gray-800 bg-gray-900 shrink-0">
	<input
		bind:value={search}
		placeholder="Поиск..."
		class="flex-1 max-w-xs bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-1.5 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
	/>
	<div class="flex gap-1 flex-wrap">
		{#each stages as stage}
			<button
				onclick={() => filterStage = stage}
				class="px-2.5 py-1 text-xs rounded-lg transition-colors
					{filterStage === stage ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'}"
			>{stage === 'all' ? 'Все' : stage}</button>
		{/each}
	</div>
</div>

<!-- Table -->
<div class="flex-1 overflow-y-auto">
	<table class="w-full text-sm">
		<thead class="sticky top-0 bg-gray-900 border-b border-gray-800 z-10">
			<tr>
				<th class="text-left px-6 py-2.5 text-xs text-gray-500 font-medium">#</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Компания</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Контакт</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Этап</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Скоринг</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Бюджет</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Источник</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium max-w-[14rem]">Заметка</th>
				<th class="px-4 py-2.5 text-xs text-gray-500 font-medium text-right">Действия</th>
			</tr>
		</thead>
		<tbody class="divide-y divide-gray-800/60">
			{#each filtered as lead, i}
				<tr class="hover:bg-gray-800/30 transition-colors group">
					<td class="px-6 py-3 text-gray-600 text-xs">{i + 1}</td>
					<td class="px-4 py-3">
						<a href="/leads/{lead.id}" class="font-medium text-white hover:text-indigo-400 transition-colors">
							{lead.company}
						</a>
					</td>
					<td class="px-4 py-3">
						<div class="text-gray-300">{lead.contact}</div>
						<div class="text-xs text-gray-600">{lead.email !== '—' ? lead.email : ''}</div>
					</td>
					<td class="px-4 py-3">
						<span class="px-2 py-0.5 rounded-full text-xs font-medium {stageColor(lead.stage)}">{lead.stage}</span>
					</td>
					<td class="px-4 py-3">
						<span class="font-bold {scoreColor(lead.score)}">{lead.score}</span>
						<span class="text-gray-600 text-xs">/100</span>
					</td>
					<td class="px-4 py-3 text-gray-300">{lead.budget}</td>
					<td class="px-4 py-3 text-gray-500 text-xs">{lead.source}</td>
					<td class="px-4 py-3 text-xs text-gray-500 max-w-[14rem]">
						{#if lead.description}
							<span class="line-clamp-2" title={lead.description}>{lead.description}</span>
						{:else}
							—
						{/if}
					</td>
					<td class="px-4 py-3 text-right">
						<div class="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
							<a href="/leads/{lead.id}" class="px-2 py-1 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded transition-colors">Открыть</a>
							<button
								onclick={() => deleteLead(lead)}
								class="px-2 py-1 text-xs text-red-400 hover:text-white hover:bg-red-900 rounded transition-colors"
							>Удалить</button>
						</div>
					</td>
				</tr>
			{/each}

			{#if filtered.length === 0}
				<tr>
					<td colspan="8" class="px-6 py-12 text-center text-gray-600 text-sm">
						Лидов не найдено. Скажи "создай лид компания ..." 🎙
					</td>
				</tr>
			{/if}
		</tbody>
	</table>
</div>
