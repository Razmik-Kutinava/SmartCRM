<script>
	import { onMount } from 'svelte';
	import {
		fetchLeads,
		apiCreateLead,
		apiUpdateLead,
		apiDeleteLead,
		apiImportBitrix,
		apiImportAmo,
		apiImportHubspot,
		apiImportLeadsCsv,
		downloadLeadsCsvExport,
		fetchBitrixImportStats,
		fetchLeadCoverage,
		fetchLeadManagers,
		readLeadsCache,
		writeLeadsCache,
	} from '$lib/leadsStorage.js';
	import { getApiUrl, onMessage } from '$lib/websocket.js';
	import { goto } from '$app/navigation';
	import {
		DEFAULT_CRM_STAGES,
		CRM_STAGES,
		loadCrmConfig,
		getCachedCrmConfig,
		leadPriorityTier,
		priorityTierBadgeClass,
	} from '$lib/crmStages.js';
	import {
		applyLeadListView,
		applyVoiceListFilter,
		PRIORITY_FILTERS,
		SCORE_RISK_FILTERS,
		EMPLOYEES_BAND_FILTERS,
		TASK_DUE_FILTERS,
		SUBSCRIPTION_FILTERS,
		distinctDeliveryTypes,
		needsEnrichBadgeForLead,
		taskDueBadgeForLead,
		GROUP_BY_OPTIONS,
		distinctOkvedSections,
		distinctIndustryBuckets,
		INDUSTRY_BUCKET_OPTIONS,
		groupLeads,
		SORT_OPTIONS,
		leadListViewFromVoiceSlots,
		todayIsoDate,
	} from '$lib/leads/leadListFilter.js';
	import { coachItemsForLead, coachSeverityClass } from '$lib/leads/leadListCoach.js';
	import {
		voiceLeadFilter,
		registerLeadIntentHandler,
	} from '$lib/voice/voiceAction.js';
	import { createLeadComment } from '$lib/leads/leadComments.js';
	import { createLeadCommunication } from '$lib/leads/leadCommunications.js';
	import { openLeadCreateModal } from '$lib/leads/leadCreateUi.js';
	import { subscriptionBadgeForLead, deliveryTypeFromLead } from '$lib/leads/leadBitrixExtra.js';
	import { COVERAGE_FILTERS } from '$lib/leads/leadCoverage.js';
	import { leadManagerLabel } from '$lib/leads/leadManager.js';

	const API = getApiUrl();

	let search = $state('');
	let filterStage = $state('all');
	let filterPriority = $state('all');
	let filterScoreRisk = $state('all');
	let filterIndustry = $state('');
	let filterCity = $state('');
	let filterEmployeesBand = $state('all');
	let filterOkvedSection = $state('all');
	let filterIndustryBucket = $state('all');
	let filterTaskDue = $state('all');
	let filterTaskDueDate = $state('');
	let filterSubscription = $state('all');
	let filterDeliveryType = $state('all');
	let filterCoverage = $state('all');
	let filterManager = $state('all');
	let filterMinScore = $state(null);
	let groupBy = $state('none');
	/** @type {string[]} */
	let collapsedGroupKeys = $state([]);
	let sortBy = $state('my_day');
	let showVoice = $state(false); // голос теперь глобальный — в layout
	let notification = $state(null); // { text, type: 'success'|'error'|'info' }
	let apiError = $state(false); // флаг недоступности API
	let bitrixImporting = $state(false);
	let amoImporting = $state(false);
	let hubspotImporting = $state(false);
	let csvImporting = $state(false);
	let csvExporting = $state(false);
	let csvInput = $state(null);
	/** @type {{ bitrix_total: number | null, local_bitrix_leads_count: number, date_from?: string } | null} */
	let bitrixStats = $state(null);
	/** @type {{ total?: number, bitrixTotal?: number, segments?: Record<string, number>, resync?: { status?: string, processed?: number, totalB24?: number } } | null} */
	let coverageStats = $state(null);
	/** @type {Array<{ name: string, count: number }>} */
	let managerOptions = $state([]);

	/** Воронка с сервера (Ops → CRM / crm_settings.json), иначе дефолт */
	let stages = $state(/** @type {string[]} */ (['all', ...DEFAULT_CRM_STAGES]));

	// Сразу показываем кэш, потом перезаписываем данными из БД
	let leads = $state(readLeadsCache());

	onMount(async () => {
		await loadCrmConfig();
		stages = ['all', ...CRM_STAGES];
		try {
			const fresh = await fetchLeads();
			leads = fresh;
			apiError = false;
			console.log('[Leads] список загружен из БД:', fresh.length);
		} catch (e) {
			console.error('[leads] fetchLeads ошибка:', e);
			apiError = true;
		}
		try {
			bitrixStats = await fetchBitrixImportStats('2023-01-01');
		} catch {
			bitrixStats = null;
		}
		try {
			coverageStats = await fetchLeadCoverage();
		} catch {
			coverageStats = null;
		}
		try {
			const mgr = await fetchLeadManagers();
			managerOptions = Array.isArray(mgr?.managers) ? mgr.managers : [];
			if (mgr?.defaultFilter && filterManager === 'all') {
				filterManager = mgr.defaultFilter;
			}
		} catch {
			managerOptions = [];
		}

		registerLeadIntentHandler(handleVoiceResult);

		const unsubWs = onMessage((data) => {
			if (data.type === 'intent' && data.intent) {
				// delete_lead — только через voice_action approve
				if (data.intent !== 'delete_lead') {
					handleVoiceResult(data);
				}
			}
		});

		const unsubFilter = voiceLeadFilter.subscribe((filt) => {
			if (!filt) return;
			const v = applyVoiceListFilter(filt);
			filterStage = v.filterStage;
			filterPriority = v.filterPriority;
			sortBy = v.sortBy;
			search = v.search;
			filterIndustry = v.filterIndustry;
			filterCity = v.filterCity;
			filterMinScore = v.minScore;
			notify(
				v.minScore != null ? `Фильтр: скор ≥ ${v.minScore}` : 'Фильтр применён голосом',
				'info',
			);
			voiceLeadFilter.set(null);
		});

		return () => {
			unsubWs();
			unsubFilter();
			registerLeadIntentHandler(null);
		};
	});

	let filtered = $derived(
		applyLeadListView(
			leads,
			{
				search,
				filterStage,
				filterPriority,
				filterScoreRisk,
				filterIndustry,
				filterCity,
				filterEmployeesBand,
				filterOkvedSection,
				filterIndustryBucket,
				filterTaskDue,
				filterTaskDueDate,
				filterSubscription,
				filterDeliveryType,
				filterCoverage,
				filterManager,
				sortBy,
				minScore: filterMinScore,
			},
			getCachedCrmConfig(),
		),
	);

	let showListMenu = $state(false);

	const okvedSectionOptions = $derived(distinctOkvedSections(leads));
	const industryBucketOptions = $derived(distinctIndustryBuckets(leads));
	const deliveryTypeOptions = $derived(distinctDeliveryTypes(leads));

	const managerFilterOptions = $derived.by(() => {
		if (managerOptions.length > 0) return managerOptions;
		/** @type {Map<string, number>} */
		const counts = new Map();
		for (const l of leads) {
			const name = l.managerName || leadManagerLabel(l);
			if (!name) continue;
			counts.set(name, (counts.get(name) || 0) + 1);
		}
		return [...counts.entries()]
			.map(([name, count]) => ({ name, count }))
			.sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'ru'));
	});

	const coverageCounts = $derived.by(() => {
		/** @type {Record<string, number>} */
		const counts = { all: leads.length };
		for (const chip of COVERAGE_FILTERS) {
			if (chip.id !== 'all') counts[chip.id] = 0;
		}
		for (const l of leads) {
			for (const seg of l.coverageSegments || []) {
				if (counts[seg] != null) counts[seg] += 1;
			}
		}
		return counts;
	});

	const listGroups = $derived(groupLeads(filtered, groupBy));

	function toggleListGroup(key) {
		if (collapsedGroupKeys.includes(key)) {
			collapsedGroupKeys = collapsedGroupKeys.filter((k) => k !== key);
		} else {
			collapsedGroupKeys = [...collapsedGroupKeys, key];
		}
	}

	function onGroupByChange() {
		collapsedGroupKeys = [];
	}

	const listKpi = $derived.by(() => {
		const cfg = getCachedCrmConfig();
		let hot = 0;
		let warnings = 0;
		let scoreSum = 0;
		let portraitSum = 0;
		let tasksToday = 0;
		let tasksOverdue = 0;
		for (const l of filtered) {
			const tier = leadPriorityTier(l.score, cfg);
			if (tier.key === 'high' || tier.key === 'critical') hot += 1;
			if (l.hasScoreWarnings) warnings += 1;
			if (l.taskDueToday) tasksToday += 1;
			if (l.taskOverdue) tasksOverdue += 1;
			scoreSum += Number(l.score) || 0;
			portraitSum += Number(l.portraitScore) || 0;
		}
		return {
			hot,
			warnings,
			avg: filtered.length ? Math.round(scoreSum / filtered.length) : 0,
			portraitAvg: filtered.length ? Math.round(portraitSum / filtered.length) : 0,
			tasksToday,
			tasksOverdue,
		};
	});

	const filtersActive = $derived(
		Boolean(
			search.trim()
			|| filterStage !== 'all'
			|| filterPriority !== 'all'
			|| filterScoreRisk !== 'all'
			|| filterIndustry
			|| filterCity
			|| filterEmployeesBand !== 'all'
			|| filterOkvedSection !== 'all'
			|| filterIndustryBucket !== 'all'
			|| filterTaskDue !== 'all'
			|| (filterTaskDue === 'on_date' && filterTaskDueDate)
			|| filterSubscription !== 'all'
			|| filterDeliveryType !== 'all'
			|| filterCoverage !== 'all'
			|| filterManager !== 'all'
			|| filterMinScore != null,
		),
	);

	function onTaskDueFilterChange() {
		if (filterTaskDue === 'on_date' && !filterTaskDueDate) {
			filterTaskDueDate = todayIsoDate();
		}
		if (filterTaskDue !== 'on_date') {
			filterTaskDueDate = '';
		}
	}

	function resetListFilters() {
		search = '';
		filterStage = 'all';
		filterPriority = 'all';
		filterScoreRisk = 'all';
		filterIndustry = '';
		filterCity = '';
		filterEmployeesBand = 'all';
		filterOkvedSection = 'all';
		filterIndustryBucket = 'all';
		filterTaskDue = 'all';
		filterTaskDueDate = '';
		filterSubscription = 'all';
		filterDeliveryType = 'all';
		filterCoverage = 'all';
		filterManager = 'all';
		filterMinScore = null;
		sortBy = 'my_day';
	}

	function closeListMenu() {
		showListMenu = false;
	}

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

	async function runAmoImport() {
		if (amoImporting) return;
		amoImporting = true;
		try {
			const res = await apiImportAmo();
			leads = await fetchLeads();
			writeLeadsCache(leads);
			notify(`AmoCRM: +${res.imported} новых, обновлено ${res.updated}`, 'info');
		} catch (e) {
			notify(`AmoCRM: ${e.message}`, 'error');
		} finally {
			amoImporting = false;
		}
	}

	async function runHubspotImport() {
		if (hubspotImporting) return;
		hubspotImporting = true;
		try {
			const res = await apiImportHubspot();
			leads = await fetchLeads();
			writeLeadsCache(leads);
			notify(`HubSpot: +${res.imported} новых, обновлено ${res.updated}`, 'info');
		} catch (e) {
			notify(`HubSpot: ${e.message}`, 'error');
		} finally {
			hubspotImporting = false;
		}
	}

	async function runCsvImport(file) {
		if (!file || csvImporting) return;
		csvImporting = true;
		try {
			const res = await apiImportLeadsCsv(file, 'upsert');
			const fresh = await fetchLeads();
			leads = fresh;
			writeLeadsCache(leads);
			notify(
				`CSV: +${res.imported} новых, обновлено ${res.updated}, пропущено ${res.skipped}`,
				'success',
			);
		} catch (e) {
			notify(`CSV импорт: ${e?.message || e}`, 'error');
		} finally {
			csvImporting = false;
			if (csvInput) csvInput.value = '';
		}
	}

	function onCsvFileChange(e) {
		const file = e.currentTarget?.files?.[0];
		if (file) runCsvImport(file);
	}

	async function runCsvExport() {
		if (csvExporting) return;
		csvExporting = true;
		try {
			await downloadLeadsCsvExport();
			notify('CSV экспорт готов', 'success');
		} catch (e) {
			notify(`CSV экспорт: ${e?.message || e}`, 'error');
		} finally {
			csvExporting = false;
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
					score: getCachedCrmConfig()?.default_new_lead_score ?? 50,
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
			const view = leadListViewFromVoiceSlots(slots);
			filterStage = view.filterStage;
			filterPriority = view.filterPriority;
			sortBy = view.sortBy;
			search = view.search || search;
			filterIndustry = view.filterIndustry;
			filterCity = view.filterCity;
			notify('Фильтр списка обновлён', 'info');
			break;
		}

			case 'analyze_lead':
			case 'lead_history': {
				notify(reply || 'Смотри модалку / карточку лида', 'info');
				break;
			}

			case 'add_communication': {
				const lead = findLead(slots);
				if (!lead) {
					notify('Лид не найден — уточни компанию', 'error');
					return;
				}
				const content = String(slots?.content || slots?.comment || '').trim();
				if (!content) {
					notify('Не указан текст касания или комментария', 'error');
					return;
				}
				try {
					if (slots?.kind === 'comment') {
						await createLeadComment(lead.id, content, 'Голос');
						notify(`✓ Комментарий к ${lead.company} сохранён`);
					} else {
						const ctype = slots?.communication_type || slots?.communicationType || 'call';
						await createLeadCommunication(lead.id, {
							communicationType: ctype,
							content,
							actor: 'Голос',
						});
						notify(`✓ Касание (${ctype}) к ${lead.company} записано`);
					}
				} catch (e) {
					notify(`Ошибка записи: ${e.message}`, 'error');
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
				goto('/leads/tasks');
				notify('Раздел задач', 'info');
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

	async function deleteLead(lead) {
		try {
			const ok = await confirmAndDeleteLead(lead);
			if (!ok) return;
			leads = leads.filter((l) => l.id !== lead.id);
			notify(`✓ Лид удалён: ${lead.company}`, 'success');
		} catch (e) {
			notify(`Ошибка удаления: ${e.message}`, 'error');
		}
	}
</script>

<!-- Шапка + фильтры -->
<header
	class="shrink-0 border-b border-gray-800 bg-gray-900 overflow-visible"
	data-testid="leads-list-header"
>
	<div class="flex items-start justify-between gap-3 px-4 sm:px-6 pt-[18px] pb-3">
		<div class="min-w-0">
			<h1 class="text-lg font-bold text-white leading-tight">Список лидов</h1>
			<p class="text-xs text-gray-500 mt-0.5" data-testid="leads-list-count">
				<span class="text-gray-400">{filtered.length.toLocaleString('ru-RU')}</span>
				{filtered.length === leads.length ? 'лидов' : `показано · ${leads.length.toLocaleString('ru-RU')} всего`}
			</p>
		</div>
		<div class="flex items-center gap-2 shrink-0 pt-0.5">
			<button
				type="button"
				onclick={() => openLeadCreateModal({
					source: 'Список лидов',
					onCreated: (created) => {
						leads = [created, ...leads.filter((l) => l.id !== created.id)];
						notify(`✓ Лид сохранён: ${created.company}`);
					},
				})}
				class="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-sm font-medium text-white rounded-xl shadow-lg shadow-indigo-950/40 transition-colors"
				data-testid="leads-list-create-lead"
			>+ Новый лид</button>
			<div class="relative">
				<button
					type="button"
					class="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 text-xl leading-none transition-colors"
					data-testid="leads-list-more-menu"
					aria-label="Импорт и экспорт"
					aria-expanded={showListMenu}
					onclick={() => { showListMenu = !showListMenu; }}
				>⋯</button>
				{#if showListMenu}
					<button
						type="button"
						class="fixed inset-0 z-30 cursor-default"
						aria-label="Закрыть меню"
						onclick={closeListMenu}
					></button>
					<div
						class="absolute right-0 top-full mt-1.5 z-40 w-56 rounded-xl border border-gray-700 bg-gray-950 shadow-2xl py-1.5"
						data-testid="leads-list-more-panel"
					>
						<p class="px-3 py-1.5 text-[10px] uppercase tracking-wider text-gray-600">Импорт</p>
						<button
							type="button"
							disabled={bitrixImporting}
							onclick={() => { closeListMenu(); runBitrixImport(); }}
							class="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-gray-800 disabled:opacity-50"
							data-testid="leads-bitrix-import"
							title="Нужен BITRIX24_WEBHOOK_URL на сервере"
						>{bitrixImporting ? '⏳ Битрикс24…' : '📤 Битрикс24'}</button>
						<button
							type="button"
							disabled={amoImporting}
							onclick={() => { closeListMenu(); runAmoImport(); }}
							class="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-gray-800 disabled:opacity-50"
							data-testid="leads-amo-import"
						>{amoImporting ? '⏳ AmoCRM…' : '📤 AmoCRM'}</button>
						<button
							type="button"
							disabled={hubspotImporting}
							onclick={() => { closeListMenu(); runHubspotImport(); }}
							class="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-gray-800 disabled:opacity-50"
							data-testid="leads-hubspot-import"
						>{hubspotImporting ? '⏳ HubSpot…' : '📤 HubSpot'}</button>
						<input
							bind:this={csvInput}
							type="file"
							accept=".csv,text/csv"
							class="hidden"
							data-testid="leads-csv-input"
							onchange={onCsvFileChange}
						/>
						<button
							type="button"
							disabled={csvImporting}
							onclick={() => { closeListMenu(); csvInput?.click(); }}
							class="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-gray-800 disabled:opacity-50"
							data-testid="leads-csv-import"
						>{csvImporting ? '⏳ CSV…' : '📥 Импорт CSV'}</button>
						<div class="my-1 border-t border-gray-800"></div>
						<button
							type="button"
							disabled={csvExporting || leads.length === 0}
							onclick={() => { closeListMenu(); runCsvExport(); }}
							class="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-gray-800 disabled:opacity-50"
							data-testid="leads-csv-export"
						>{csvExporting ? '⏳…' : '📤 Экспорт CSV'}</button>
						{#if bitrixStats}
							<div class="mt-1 mx-2 px-2 py-2 rounded-lg bg-gray-900 border border-gray-800 text-[11px] text-gray-500 leading-snug" data-testid="leads-bitrix-stats">
								B24 (≥2023): <span class="text-gray-400">{bitrixStats.bitrix_total ?? '—'}</span>
								· у нас: <span class="text-gray-400">{bitrixStats.local_bitrix_leads_count ?? '—'}</span>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	</div>

	<div class="px-4 sm:px-6 pb-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-gray-500" data-testid="leads-list-kpi">
		<span><span class="text-amber-400 font-semibold">{listKpi.hot}</span> горячих</span>
		<span><span class="text-orange-400 font-semibold">{listKpi.warnings}</span> с предупрежд.</span>
		<span>ср. балл <span class="text-green-400 font-semibold">{listKpi.avg}</span></span>
		<span>портрет <span class="text-sky-400 font-semibold">{listKpi.portraitAvg}%</span></span>
		<a href="/leads/tasks?filter=today" class="hover:text-amber-200 transition-colors">
			<span class="text-amber-300 font-semibold">{listKpi.tasksToday}</span> дел сегодня
		</a>
		<a href="/leads/tasks?filter=overdue" class="hover:text-red-300 transition-colors">
			<span class="text-red-400 font-semibold">{listKpi.tasksOverdue}</span> просроч.
		</a>
		{#if bitrixStats}
			<span class="hidden sm:inline text-gray-600">
				B24: {bitrixStats.local_bitrix_leads_count ?? '—'} / {bitrixStats.bitrix_total ?? '—'}
			</span>
		{/if}
	</div>

	<div class="px-4 sm:px-6 pb-2 flex flex-wrap items-center gap-2" data-testid="leads-coverage-chips">
		<span class="text-[10px] uppercase tracking-wider text-gray-600 mr-1 w-full sm:w-auto">Полнота</span>
		{#each COVERAGE_FILTERS as chip (chip.id)}
			<button
				type="button"
				class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] border transition-colors
					{filterCoverage === chip.id
					? 'bg-indigo-600/25 border-indigo-500/80 text-indigo-200'
					: 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600 hover:text-gray-300'}"
				aria-pressed={filterCoverage === chip.id}
				data-testid="leads-coverage-{chip.id}"
				onclick={() => { filterCoverage = chip.id; }}
			>
				{chip.label}
				<span class="font-semibold tabular-nums">{coverageCounts[chip.id] ?? 0}</span>
			</button>
		{/each}
		{#if coverageStats?.resync?.status}
			<span class="text-[10px] text-gray-600 ml-auto" data-testid="leads-coverage-resync">
				B24 resync: {coverageStats.resync.processed ?? 0}/{coverageStats.resync.totalB24 ?? '—'}
				· {coverageStats.resync.status}
			</span>
		{/if}
	</div>

	<div class="flex flex-col gap-2.5 px-4 sm:px-6 pt-1 pb-3 border-t border-gray-800/80" data-testid="leads-list-filters">
		<div class="flex items-end gap-2 sm:gap-3 flex-wrap">
			<label class="flex-1 min-w-[12rem] max-w-md">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Поиск</span>
				<input
					bind:value={search}
					placeholder="Компания, контакт, город…"
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
					data-testid="leads-list-search"
				/>
			</label>
			<label class="min-w-[10rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Менеджер</span>
				<select
					bind:value={filterManager}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					data-testid="leads-list-manager"
				>
					<option value="all">Все менеджеры</option>
					{#each managerFilterOptions as opt (opt.name)}
						<option value={opt.name}>{opt.name} ({opt.count})</option>
					{/each}
				</select>
			</label>
			<label class="min-w-[7.5rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Сортировка</span>
				<select
					bind:value={sortBy}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					aria-label="Сортировка"
					data-testid="leads-list-sort"
				>
					{#each SORT_OPTIONS as opt}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			<label class="min-w-[7.5rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Тир</span>
				<select
					bind:value={filterPriority}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					aria-label="Фильтр тира"
					data-testid="leads-list-tier"
				>
					{#each PRIORITY_FILTERS as opt}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			<label class="min-w-[8.5rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Подсказка балла</span>
				<select
					bind:value={filterScoreRisk}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					aria-label="Фильтр по подсказке балла"
					data-testid="leads-filter-score-risk"
				>
					{#each SCORE_RISK_FILTERS as opt}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			<label class="min-w-[7rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Размер</span>
				<select
					bind:value={filterEmployeesBand}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					data-testid="leads-list-employees-band"
				>
					{#each EMPLOYEES_BAND_FILTERS as opt}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			<label class="min-w-[8rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Отрасль</span>
				<select
					bind:value={filterIndustryBucket}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					data-testid="leads-list-industry-bucket"
				>
					<option value="all">Все отрасли</option>
					{#each industryBucketOptions as opt (opt.id)}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			<label class="min-w-[7rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">ОКВЭД сек.</span>
				<select
					bind:value={filterOkvedSection}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					data-testid="leads-list-okved-section"
				>
					<option value="all">Все секции</option>
					{#each okvedSectionOptions as opt (opt.id)}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			<label class="min-w-[8.5rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Подписка</span>
				<select
					bind:value={filterSubscription}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					data-testid="leads-list-subscription"
				>
					{#each SUBSCRIPTION_FILTERS as opt}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			<label class="min-w-[9rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Тип поставки</span>
				<select
					bind:value={filterDeliveryType}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					data-testid="leads-list-delivery-type"
				>
					<option value="all">Все типы</option>
					{#each deliveryTypeOptions as opt (opt.id)}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			<label class="min-w-[8rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Дела</span>
				<select
					bind:value={filterTaskDue}
					onchange={onTaskDueFilterChange}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					data-testid="leads-list-task-due"
				>
					{#each TASK_DUE_FILTERS as opt}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			{#if filterTaskDue === 'on_date'}
				<label class="min-w-[9rem]">
					<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Дата дела</span>
					<input
						type="date"
						bind:value={filterTaskDueDate}
						class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
						data-testid="leads-list-task-due-date"
					/>
				</label>
			{/if}
			<label class="min-w-[8rem]">
				<span class="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">Группировка</span>
				<select
					bind:value={groupBy}
					onchange={onGroupByChange}
					class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
					data-testid="leads-list-group-by"
				>
					{#each GROUP_BY_OPTIONS as opt}
						<option value={opt.id}>{opt.label}</option>
					{/each}
				</select>
			</label>
			{#if filtersActive}
				<button
					type="button"
					class="px-3 py-2 text-xs rounded-lg border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 transition-colors mb-0.5"
					data-testid="leads-list-reset-filters"
					onclick={resetListFilters}
				>Сбросить</button>
			{/if}
		</div>
		<div class="flex gap-1 flex-wrap" data-testid="leads-list-stage-chips">
			{#each stages as stage}
				<button
					type="button"
					onclick={() => filterStage = stage}
					class="px-2.5 py-1 text-xs rounded-lg transition-colors
						{filterStage === stage ? 'bg-indigo-600 text-white shadow-md shadow-indigo-950/50' : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'}"
				>{stage === 'all' ? 'Все этапы' : stage}</button>
			{/each}
		</div>
		{#if filterIndustry || filterCity}
			<div class="flex gap-2 flex-wrap items-center">
				<span class="text-[11px] text-gray-500 uppercase tracking-wide">Голос</span>
				{#if filterIndustry}
					<button
						type="button"
						class="px-2 py-0.5 text-xs rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800 hover:bg-cyan-900"
						onclick={() => filterIndustry = ''}
						title="Сбросить отрасль"
					>Отрасль: {filterIndustry} ✕</button>
				{/if}
				{#if filterCity}
					<button
						type="button"
						class="px-2 py-0.5 text-xs rounded-full bg-violet-950 text-violet-300 border border-violet-800 hover:bg-violet-900"
						onclick={() => filterCity = ''}
						title="Сбросить город"
					>Город: {filterCity} ✕</button>
				{/if}
			</div>
		{/if}
	</div>
</header>

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

<!-- Table -->
<div class="flex-1 overflow-y-auto">
	<table class="w-full text-sm">
		<thead class="sticky top-0 bg-gray-900 border-b border-gray-800 z-10">
			<tr>
				<th class="text-left px-6 py-2.5 text-xs text-gray-500 font-medium">#</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Компания</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Контакт</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Этап</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Менеджер</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">
					<button type="button" class="hover:text-gray-300" onclick={() => sortBy = sortBy === 'score_desc' ? 'score_asc' : 'score_desc'}>
						Скоринг {sortBy === 'score_asc' ? '↑' : '↓'}
					</button>
				</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">
					<button type="button" class="hover:text-gray-300" onclick={() => sortBy = 'priority_desc'}>Приоритет</button>
				</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Бюджет</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Подписка до</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium">Источник</th>
				<th class="text-left px-4 py-2.5 text-xs text-gray-500 font-medium max-w-[14rem]">Заметка</th>
				<th class="px-4 py-2.5 text-xs text-gray-500 font-medium text-right">Действия</th>
			</tr>
		</thead>
		<tbody class="divide-y divide-gray-800/60">
			{#each listGroups as group (group.key || '__all__')}
				{#if groupBy !== 'none'}
					<tr class="bg-gray-800/50" data-testid="leads-list-group-header">
						<td colspan="12" class="px-4 py-2">
							<button
								type="button"
								class="flex items-center gap-2 text-xs font-medium text-gray-300 hover:text-white w-full text-left"
								data-testid="leads-list-group-toggle"
								data-group-key={group.key}
								onclick={() => toggleListGroup(group.key)}
							>
								<span class="text-gray-500 w-4 shrink-0">{collapsedGroupKeys.includes(group.key) ? '▶' : '▼'}</span>
								<span>{group.label}</span>
								<span class="text-gray-600 font-normal">({group.count})</span>
							</button>
						</td>
					</tr>
				{/if}
				{#if groupBy === 'none' || !collapsedGroupKeys.includes(group.key)}
					{#each group.leads as lead, i}
				{@const tier = leadPriorityTier(lead.score, getCachedCrmConfig())}
				{@const taskBadge = taskDueBadgeForLead(lead)}
				{@const enrichBadge = needsEnrichBadgeForLead(lead)}
				{@const coachItems = coachItemsForLead(lead)}
				{@const subBadge = subscriptionBadgeForLead(lead)}
				<tr class="hover:bg-gray-800/30 transition-colors group">
					<td class="px-6 py-3 text-gray-600 text-xs">{i + 1}</td>
					<td class="px-4 py-3">
						<a href="/leads/{lead.id}" class="font-medium text-white hover:text-indigo-400 transition-colors">
							{lead.company}
						</a>
						{#if coachItems.length}
							<ul class="mt-1.5 space-y-0.5 max-w-[18rem]" data-testid="leads-list-coach">
								{#each coachItems as item (item.code)}
									<li
										class="text-[10px] leading-snug px-1.5 py-0.5 rounded border {coachSeverityClass(item.severity)}"
										data-coach-code={item.code}
										title={item.text}
									>{item.text}</li>
								{/each}
							</ul>
						{:else if taskBadge || enrichBadge}
							<div class="mt-1 flex flex-wrap items-center gap-1 max-w-[14rem]">
								{#if enrichBadge}
									<span
										class="inline-block px-1.5 py-0.5 rounded text-[10px] border {enrichBadge.cls}"
										data-testid="leads-list-needs-enrich"
										title="Горячий лид — дозаполни паспорт и карточку"
									>{enrichBadge.label}</span>
								{/if}
								{#if taskBadge}
									<span
										class="inline-block px-1.5 py-0.5 rounded text-[10px] border {taskBadge.cls}"
										data-testid="leads-list-task-badge"
										title={lead.nextTaskTitle ? `${lead.nextTaskTitle}${lead.nextTaskDue ? ` · ${lead.nextTaskDue}` : ''}` : ''}
									>{taskBadge.label}</span>
									{#if lead.nextTaskTitle}
										<span class="text-[10px] text-gray-600 truncate" title={lead.nextTaskTitle}>{lead.nextTaskTitle}</span>
									{/if}
								{/if}
							</div>
						{/if}
						{#if lead.okvedMain || lead.employeesBand}
							<div class="text-[10px] text-gray-600 mt-0.5 truncate max-w-[14rem]">
								{#if lead.okvedMain}<span title={lead.okvedName || ''}>ОКВЭД {lead.okvedMain}</span>{/if}
								{#if lead.okvedMain && lead.employeesBand}<span class="mx-1">·</span>{/if}
								{#if lead.employeesBand}{lead.employeesBand} сотр.{/if}
							</div>
						{/if}
					</td>
					<td class="px-4 py-3">
						<div class="text-gray-300">{lead.contact}</div>
						<div class="text-xs text-gray-600">{lead.email !== '—' ? lead.email : ''}</div>
					</td>
					<td class="px-4 py-3">
						<span class="px-2 py-0.5 rounded-full text-xs font-medium {stageColor(lead.stage)}">{lead.stage}</span>
					</td>
					<td class="px-4 py-3 text-gray-400 text-xs max-w-[9rem] truncate" data-testid="leads-list-manager-cell" title={lead.managerName || leadManagerLabel(lead)}>
						{lead.managerName || leadManagerLabel(lead) || '—'}
					</td>
					<td class="px-4 py-3">
						<span class="font-bold {scoreColor(lead.score)}">{lead.score}</span>
						<span class="text-gray-600 text-xs">/100</span>
						{#if lead.suggestedScore != null && lead.scoreDivergent}
							<span
								class="ml-1 px-1.5 py-0.5 rounded text-[10px] bg-amber-950 text-amber-300 border border-amber-800"
								title="Подсказка {lead.suggestedScore}/100"
							>Δ</span>
						{/if}
						{#if lead.hasScoreWarnings}
							<span
								class="ml-1 px-1.5 py-0.5 rounded text-[10px] bg-orange-950 text-orange-300 border border-orange-800"
								title="{lead.scoreWarningsCount ?? 1} предупрежд."
							>!</span>
						{/if}
					</td>
					<td class="px-4 py-3">
						<span class="px-2 py-0.5 rounded text-xs font-medium {priorityTierBadgeClass(tier)}">{tier.label}</span>
					</td>
					<td class="px-4 py-3 text-gray-300">{lead.budget}</td>
					<td class="px-4 py-3">
						{#if subBadge}
							<span
								class="inline-block px-1.5 py-0.5 rounded text-[10px] border tabular-nums {subBadge.cls}"
								data-testid="leads-list-subscription-badge"
								title={subBadge.kind === 'expiring' ? `Истекает через ${subBadge.days} дн.` : subBadge.kind === 'expired' ? 'Подписка просрочена' : 'Подписка до'}
							>{subBadge.label}</span>
							{#if deliveryTypeFromLead(lead)}
								<div class="text-[10px] text-gray-600 mt-0.5 truncate max-w-[8rem]" title={deliveryTypeFromLead(lead)}>
									{deliveryTypeFromLead(lead)}
								</div>
							{/if}
						{:else}
							<span class="text-gray-600 text-xs">—</span>
						{/if}
					</td>
					<td class="px-4 py-3 text-gray-500 text-xs">{lead.source}</td>
					<td class="px-4 py-3 text-xs text-gray-500 max-w-[14rem]">
						{#if lead.description}
							<span class="line-clamp-2" title={lead.description}>{lead.description}</span>
						{:else}
							—
						{/if}
					</td>
					<td class="px-4 py-3 text-right">
						<div class="flex items-center justify-end gap-1">
							<a href="/leads/{lead.id}" class="px-2 py-1 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded transition-colors">Открыть</a>
							<button
								type="button"
								data-testid="leads-list-delete-lead"
								onclick={() => deleteLead(lead)}
								class="px-2 py-1 text-xs text-red-400 hover:text-white hover:bg-red-900 rounded transition-colors"
							>Удалить</button>
						</div>
					</td>
				</tr>
					{/each}
				{/if}
			{/each}

			{#if filtered.length === 0}
				<tr>
					<td colspan="11" class="px-6 py-12 text-center text-gray-600 text-sm">
						Лидов не найдено. Скажи "создай лид компания ..." 🎙
					</td>
				</tr>
			{/if}
		</tbody>
	</table>
</div>
