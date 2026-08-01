<script>
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		enrichLeadForCard,
		getLeadById,
		apiUpdateLead,
		fetchLeads,
		fetchLeadById,
		writeLeadsCache,
	} from '$lib/leadsStorage.js';
	import {
		CRM_STAGES,
		loadCrmConfig,
		getCachedCrmConfig,
		leadPriorityTier,
		priorityTierBadgeClass,
		stageBadgeClass,
	} from '$lib/crmStages.js';
	import { fetchEmailAccounts, fetchEmailThreads, fetchNurtureChains } from '$lib/emailStorage.js';
	import {
		defaultApprovals,
		mergeApprovals,
	} from '$lib/leadApprovals.js';
	import { detailsDraftFromLead, patchFromDetailsDraft } from '$lib/leads/leadCardEdit.js';
	import { contactsDraftFromLead, contactsPatchFromDraft } from '$lib/leads/leadContacts.js';
	import { loadLeadCardActivity } from '$lib/leads/leadCardActivity.js';
	import { describeTransitionRule, rulesForTargetStage } from '$lib/leads/stageTransition.js';
	import { buildMoneyPatch, formatDealAmountLabel, moneyStringsFromLead } from '$lib/leads/leadCardMoney.js';
	import { isRepeatLead } from '$lib/leads/leadBitrixExtra.js';
	import { leadManagerLabel } from '$lib/leads/leadManager.js';
	import { createTask, fetchTasks, patchTask } from '$lib/tasks/taskApi.js';
	import { TASK_INTENT_OPTIONS } from '$lib/tasks/taskIntentCatalog.js';
	import { slaStatus } from '$lib/tasks/taskSla.js';
	import { formatRuDate } from '$lib/leads/leadActivityTasks.js';
	import { enrichLeadOnCard } from '$lib/search/enrichLeadOnCard.js';
	import { researchLeadOnCard } from '$lib/search/researchLeadOnCard.js';
	import { openLeadMailing } from '$lib/leads/leadMailingUi.js';
	import { openLeadIndustryModal } from '$lib/leads/leadIndustryUi.js';
	import { apiFetch } from '$lib/api.js';
	import { fetchLeadIndustries } from '$lib/leads/industryCatalog.js';
	import { assignLeadSlaProtocol, fetchSlaProtocols } from '$lib/leads/slaProtocol.js';
	import { confirmAndDeleteLead } from '$lib/leads/leadDelete.js';
	import LeadStageHints from '../../../components/LeadStageHints.svelte';
	import LeadDealPathPanel from '../../../components/LeadDealPathPanel.svelte';
	import LeadClientCardForm from '../../../components/LeadClientCardForm.svelte';
	import LeadActivityPanel from '../../../components/LeadActivityPanel.svelte';
	import LeadPassportPanel from '../../../components/LeadPassportPanel.svelte';
	import LeadSlideOver from '../../../components/LeadSlideOver.svelte';
	import LeadHubTile from '../../../components/LeadHubTile.svelte';
	import LeadProductsPanel from '../../../components/LeadProductsPanel.svelte';
	import { passportHasData } from '$lib/leads/leadPassport.js';
	import { buildHubTilePreviews, PANEL_TITLES } from '$lib/leads/leadHubPreview.js';
	import {
		moveHubTile,
		parseHubTileDragId,
		readHubTileOrder,
		setHubTileDragData,
		sortTilesByOrder,
		writeHubTileOrder,
	} from '$lib/leads/hubTileOrder.js';
	import { buildLeadCardCoachItems, hubTileAlertsFromCoach } from '$lib/leads/leadCardCoach.js';
	import LeadCardCoachBanner from '../../../components/LeadCardCoachBanner.svelte';

	let lead = $state(null);
	let notFound = $state(false);
	let slaProtocols = $state([]);
	let slaAssigning = $state(false);
	let slaMsg = $state('');
	let deleteBusy = $state(false);

	let approvalsDraft = $state({});
	function toggleApprovalKey(key, checked) {
		approvalsDraft[key] = checked;
		approvalsDraft = { ...approvalsDraft };
	}
	function syncApprovalsDraft() {
		if (!lead) {
			approvalsDraft = defaultApprovals();
			return;
		}
		approvalsDraft = mergeApprovals(defaultApprovals(), lead.approvals);
	}

	function sync() {
		const id = get(page).params.id;
		const raw = getLeadById(id);
		lead     = raw ? enrichLeadForCard(raw) : null;
		notFound = !raw;
		syncApprovalsDraft();
	}

	/**
	 * Перечитать лид из детального API и применить к карточке.
	 * Кэш списка (`sync()`) для этого не годится: на 3k+ лидах `fetchLeads()`
	 * идёт больше 10 секунд, и до его конца карточка показывает старые данные.
	 */
	async function refreshLeadFromApi() {
		const id = lead?.id ?? get(page).params.id;
		if (!id) return false;
		try {
			lead = enrichLeadForCard(await fetchLeadById(id));
			notFound = false;
			syncApprovalsDraft();
			return true;
		} catch {
			sync();
			return false;
		}
	}

	/** Обновить кэш списка в фоне — карточка его не ждёт. */
	function refreshLeadsCacheInBackground() {
		fetchLeads()
			.then((fresh) => writeLeadsCache(fresh))
			.catch(() => {
				/* список обновится при следующем заходе */
			});
	}

	onMount(() => {
		let lastFetchedOkId = '';
		let inFlightId = '';
		async function pullLead() {
			const id = String(get(page).params.id ?? '');
			// page.subscribe срабатывает и на смену ?panel=/?tab= — на том же лиде
			// перезагружать нечего, а пересборка черновиков стирала незаполненный
			// контакт из формы и следующий ввод уходил в предыдущую карточку.
			// Отметку ставим до await: openHubPanel меняет URL сразу после подписки,
			// и оба вызова успевали пройти проверку — карточка грузилась дважды.
			if (id && (id === lastFetchedOkId || id === inFlightId)) return;
			inFlightId = id;
			await loadCrmConfig();
			if (id) {
				try {
					// Источник правды — ответ API; кэш только ускоряет повторный заход.
					// При квоте localStorage (~5MB на большой базе) запись молчит —
					// без прямого применения ответа карточка показывала «Лид не найден».
					const fetched = await fetchLeadById(id);
					lead = enrichLeadForCard(fetched);
					notFound = false;
					lastFetchedOkId = id;
					syncApprovalsDraft();
				} catch {
					/* офлайн / демо — остаётся кэш; id не фиксируем, чтобы повторить fetch при следующем заходе */
					inFlightId = '';
					sync();
				}
			} else {
				sync();
			}
			syncMoneyInputsFromLead();
			syncDetailsDraftFromLead();
			syncContactsDraftFromLead();
			await loadLeadActivity();
			await loadLeadTasks();
		}
		loadIndustryOptions();
		loadSlaCatalog();
		const panel = get(page).url.searchParams.get('panel');
		const tab = get(page).url.searchParams.get('tab');
		if (panel) openHubPanel(panel, tab || undefined);
		// Только subscribe: он сразу вызывает pullLead (без двойного fetch).
		return page.subscribe(pullLead);
	});

	async function loadSlaCatalog() {
		try {
			const d = await fetchSlaProtocols();
			slaProtocols = d.protocols || [];
		} catch {
			slaProtocols = [];
		}
	}

	async function changeSlaProtocol(protocolId) {
		if (!lead || slaAssigning) return;
		slaAssigning = true;
		slaMsg = '';
		try {
			const updated = await assignLeadSlaProtocol(lead.id, protocolId || null);
			lead = enrichLeadForCard(updated);
			refreshLeadsCacheInBackground();
			slaMsg = protocolId ? 'SLA-протокол назначен' : 'Протокол снят';
			await loadLeadTasks();
		} catch (e) {
			slaMsg = e?.message || String(e);
		} finally {
			slaAssigning = false;
		}
	}

	let stageSaving = $state(false);
	let moneyAmountStr = $state('');
	let moneyPaidStr = $state('');
	let moneySaving = $state(false);

	let leadComments = $state([]);
	let leadAudit = $state([]);
	let leadComms = $state([]);
	let approvalsSaving = $state(false);
	let detailsDraft = $state(detailsDraftFromLead(null));
	let contactsDraft = $state(/** @type {Array<Record<string, string>>} */ ([]));
	let detailsSaving = $state(false);
	let contactsSaving = $state(false);
	let enrichRunning = $state(false);
	let researchRunning = $state(false);
	let researchStatus = $state('');
	let researchStatusLabelText = $state('');
	let researchElapsed = $state(0);
	let enrichMsg = $state('');
	let exportPdfLoading = $state(false);
	let bitrixPushLoading = $state(false);
	let bitrixPushMsg = $state('');
	let amoPushLoading = $state(false);
	let hubspotPushLoading = $state(false);
	let crmPushMsg = $state('');
	let industryOptions = $state(/** @type {string[]} */ ([]));

	async function loadIndustryOptions() {
		try {
			industryOptions = await fetchLeadIndustries();
		} catch {
			industryOptions = [];
		}
	}

	function openIndustryModal() {
		if (!lead) return;
		openLeadIndustryModal(lead, {
			onSaved: async () => {
				await refreshLeadFromApi();
				refreshLeadsCacheInBackground();
				syncDetailsDraftFromLead();
				syncContactsDraftFromLead();
			},
		});
	}

	async function runLeadEnrich(force = false) {
		if (!lead || enrichRunning || researchRunning) return;
		enrichRunning = true;
		enrichMsg = '';
		try {
			const { data, patch, applied } = await enrichLeadOnCard(lead, { force });
			await refreshLeadFromApi();
			refreshLeadsCacheInBackground();
			syncDetailsDraftFromLead();
			syncContactsDraftFromLead();
			if (data.cached) {
				enrichMsg = 'Данные из кэша enrich (24 ч)';
			} else if (applied) {
				enrichMsg = `Обновлено: ${Object.keys(patch).join(', ')}`;
			} else {
				enrichMsg = 'Новых полей не найдено';
			}
		} catch (e) {
			enrichMsg = e?.message || String(e);
		} finally {
			enrichRunning = false;
		}
	}

	async function runLeadResearch(force = true) {
		if (!lead || researchRunning || enrichRunning) return;
		researchRunning = true;
		enrichMsg = '';
		researchStatus = 'searching';
		researchStatusLabelText = 'Ищу в интернете (Serper / Brave / Tavily)…';
		researchElapsed = 0;
		const tick = setInterval(() => {
			researchElapsed += 1;
		}, 1000);
		try {
			const { data, patch, applied } = await researchLeadOnCard(lead, {
				force,
				onProgress: (status, label) => {
					researchStatus = status;
					researchStatusLabelText = label;
				},
			});
			await refreshLeadFromApi();
			refreshLeadsCacheInBackground();
			syncDetailsDraftFromLead();
			syncContactsDraftFromLead();
			const providers = (data.providers_used || []).join(', ') || '—';
			const llmNote = data?.web_research?.llm
				? `LLM: ${data.web_research.llm_provider || 'да'}`
				: 'без LLM (выжимка из поиска)';
			if (applied) {
				enrichMsg = `Исследование готово за ${researchElapsed}с (${providers}; ${llmNote}). Выжимка в карточке и сыром JSON.`;
			} else {
				enrichMsg = `Исследование без новых полей за ${researchElapsed}с (${providers}; ${llmNote})`;
			}
			openHubPanel('client');
			setClientTab('card');
		} catch (e) {
			researchStatus = 'error';
			researchStatusLabelText = 'Исследование не удалось';
			enrichMsg = e?.message || String(e);
		} finally {
			clearInterval(tick);
			researchRunning = false;
		}
	}

	async function exportLeadPdf() {
		if (!lead || exportPdfLoading) return;
		exportPdfLoading = true;
		try {
			const r = await apiFetch(`/api/leads/${lead.id}/export?format=pdf`);
			if (!r.ok) throw new Error(`Экспорт: HTTP ${r.status}`);
			const blob = await r.blob();
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `lead-${lead.id}.pdf`;
			a.click();
			URL.revokeObjectURL(url);
		} catch (e) {
			enrichMsg = e?.message || String(e);
		} finally {
			exportPdfLoading = false;
		}
	}

	async function pushLeadBitrix() {
		if (!lead || bitrixPushLoading) return;
		bitrixPushLoading = true;
		bitrixPushMsg = '';
		try {
			const r = await apiFetch(`/api/leads/${lead.id}/push-bitrix`, { method: 'POST' });
			const body = await r.json().catch(() => ({}));
			if (!r.ok) {
				const d = body?.detail;
				throw new Error(typeof d === 'string' ? d : `HTTP ${r.status}`);
			}
			bitrixPushMsg =
				body.action === 'updated'
					? `Обновлён в Битрикс #${body.bitrix_lead_id}`
					: `Создан в Битрикс #${body.bitrix_lead_id}`;
			await refreshLeadFromApi();
		} catch (e) {
			bitrixPushMsg = e?.message || String(e);
		} finally {
			bitrixPushLoading = false;
		}
	}

	async function pushLeadAmo() {
		if (!lead || amoPushLoading) return;
		amoPushLoading = true;
		crmPushMsg = '';
		try {
			const r = await apiFetch(`/api/leads/${lead.id}/push-amo`, { method: 'POST' });
			const body = await r.json().catch(() => ({}));
			if (!r.ok) throw new Error(body?.detail || `HTTP ${r.status}`);
			crmPushMsg = `Amo #${body.amo_lead_id}`;
			await refreshLeadFromApi();
		} catch (e) {
			crmPushMsg = e?.message || String(e);
		} finally {
			amoPushLoading = false;
		}
	}

	async function pushLeadHubspot() {
		if (!lead || hubspotPushLoading) return;
		hubspotPushLoading = true;
		crmPushMsg = '';
		try {
			const r = await apiFetch(`/api/leads/${lead.id}/push-hubspot`, { method: 'POST' });
			const body = await r.json().catch(() => ({}));
			if (!r.ok) throw new Error(body?.detail || `HTTP ${r.status}`);
			crmPushMsg = `HubSpot ${body.hubspot_deal_id}`;
			await refreshLeadFromApi();
		} catch (e) {
			crmPushMsg = e?.message || String(e);
		} finally {
			hubspotPushLoading = false;
		}
	}

	function syncDetailsDraftFromLead() {
		detailsDraft = detailsDraftFromLead(lead);
	}

	function syncContactsDraftFromLead() {
		contactsDraft = contactsDraftFromLead(lead);
	}

	async function saveContactsFields() {
		if (!lead || contactsSaving) return;
		contactsSaving = true;
		try {
			const contacts = contactsPatchFromDraft(contactsDraft);
			await apiUpdateLead(lead.id, { contacts });
			await refreshLeadFromApi();
			refreshLeadsCacheInBackground();
			syncDetailsDraftFromLead();
			syncContactsDraftFromLead();
			syncApprovalsDraft();
			await loadLeadActivity();
		} catch (e) {
			console.error(e);
			alert('Не удалось сохранить контакты: ' + (e?.message || e));
		} finally {
			contactsSaving = false;
		}
	}

	async function saveDetailsFields() {
		if (!lead || detailsSaving) return;
		let patch;
		try {
			patch = patchFromDetailsDraft(detailsDraft);
		} catch (e) {
			alert(e?.message || String(e));
			return;
		}
		detailsSaving = true;
		try {
			await apiUpdateLead(lead.id, patch);
			await refreshLeadFromApi();
			refreshLeadsCacheInBackground();
			syncDetailsDraftFromLead();
			syncContactsDraftFromLead();
			syncMoneyInputsFromLead();
			await loadLeadActivity();
		} catch (e) {
			console.error(e);
			alert('Не удалось сохранить поля: ' + (e?.message || e));
		} finally {
			detailsSaving = false;
		}
	}

	async function loadLeadActivity() {
		const id = String(get(page).params.id ?? '');
		const activity = await loadLeadCardActivity(id);
		leadComments = activity.comments;
		leadAudit = activity.audit;
		leadComms = activity.communications;
	}

	async function loadLeadTasks() {
		if (!lead?.id) {
			leadTasksList = [];
			return;
		}
		leadTasksLoading = true;
		try {
			leadTasksList = await fetchTasks({ leadId: lead.id });
		} catch {
			leadTasksList = [];
		} finally {
			leadTasksLoading = false;
		}
	}

	async function deleteCurrentLead() {
		if (!lead || deleteBusy) return;
		deleteBusy = true;
		try {
			const ok = await confirmAndDeleteLead(lead);
			if (ok) await goto('/leads/list');
		} catch (e) {
			enrichMsg = `Ошибка удаления: ${e?.message || e}`;
		} finally {
			deleteBusy = false;
		}
	}

	async function addLeadTask() {
		if (!lead || leadTaskSaving) return;
		if (!leadTaskFormOpen) {
			leadTaskFormOpen = true;
			leadTaskTitle = '';
			leadTaskDue = formatRuDate(new Date());
			leadTaskIntent = '';
			return;
		}
		if (!leadTaskTitle.trim()) return;
		leadTaskSaving = true;
		try {
			await createTask({
				title: leadTaskTitle.trim(),
				lead_id: lead.id,
				related_lead: lead.company,
				due: leadTaskDue.trim() || formatRuDate(new Date()),
				sla_due: leadTaskDue.trim() || formatRuDate(new Date()),
				task_intent: leadTaskIntent.trim() || null,
			});
			leadTaskFormOpen = false;
			leadTaskTitle = '';
			await loadLeadTasks();
		} catch (e) {
			alert('Не удалось создать задачу: ' + (e?.message || e));
		} finally {
			leadTaskSaving = false;
		}
	}

	async function toggleLeadTaskDone(task) {
		try {
			await patchTask(task.id, { status: task.status === 'done' ? 'open' : 'done' });
			await loadLeadTasks();
		} catch (e) {
			alert('Ошибка: ' + (e?.message || e));
		}
	}

	async function saveApprovalsChecklist() {
		if (!lead || approvalsSaving) return;
		approvalsSaving = true;
		try {
			await apiUpdateLead(lead.id, { approvals: approvalsDraft });
			await refreshLeadFromApi();
			refreshLeadsCacheInBackground();
			syncMoneyInputsFromLead();
			await loadLeadActivity();
		} catch (e) {
			console.error(e);
			alert('Не удалось сохранить чеклист: ' + (e?.message || e));
		} finally {
			approvalsSaving = false;
		}
	}

	function syncMoneyInputsFromLead() {
		const { amount, paid } = moneyStringsFromLead(lead);
		moneyAmountStr = amount;
		moneyPaidStr = paid;
	}

	async function saveMoneyFields() {
		if (!lead || moneySaving) return;
		let patch;
		try {
			patch = buildMoneyPatch(moneyAmountStr, moneyPaidStr);
		} catch (e) {
			alert(e?.message || String(e));
			return;
		}
		moneySaving = true;
		try {
			await apiUpdateLead(lead.id, patch);
			await refreshLeadFromApi();
			refreshLeadsCacheInBackground();
			syncMoneyInputsFromLead();
			await loadLeadActivity();
		} catch (e) {
			console.error(e);
			alert('Не удалось сохранить суммы: ' + (e?.message || e));
		} finally {
			moneySaving = false;
		}
	}

	async function setStage(newStage) {
		if (!lead || stageSaving) return;
		stageSaving = true;
		try {
			await apiUpdateLead(lead.id, { stage: newStage });
			await refreshLeadFromApi();
			refreshLeadsCacheInBackground();
			await loadLeadActivity();
		} catch (e) {
			console.error(e);
			alert('Не удалось сменить этап: ' + (e?.message || e));
		} finally {
			stageSaving = false;
		}
	}

	let openPanel = $state(null);
	/** @type {'card' | 'passport'} */
	let clientTab = $state('card');
	/** @type {'activity' | 'tasks'} */
	let workTab = $state('activity');
	let hubTileOrder = $state(readHubTileOrder());
	let draggingHubId = $state(/** @type {string | null} */ (null));
	let hubDropTarget = $state(/** @type {string | null} */ (null));

	const hubTiles = $derived(
		sortTilesByOrder(
			buildHubTilePreviews({
				lead,
				leadTasksList,
				leadComms,
				leadThreads,
				agentHistory,
			}),
			hubTileOrder
		)
	);

	function onHubTileDragStart(e, tileId) {
		draggingHubId = tileId;
		hubDropTarget = null;
		setHubTileDragData(e, tileId);
	}

	function onHubTileDragEnd() {
		draggingHubId = null;
		hubDropTarget = null;
	}

	function onHubTileDragOver(e, tileId) {
		e.preventDefault();
		if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
		if (draggingHubId && draggingHubId !== tileId) hubDropTarget = tileId;
	}

	function onHubTileDragLeave(tileId) {
		if (hubDropTarget === tileId) hubDropTarget = null;
	}

	function onHubTileDrop(e, targetId) {
		e.preventDefault();
		const fromId = parseHubTileDragId(e.dataTransfer) || draggingHubId;
		draggingHubId = null;
		hubDropTarget = null;
		if (!fromId || fromId === targetId) return;
		hubTileOrder = moveHubTile(hubTileOrder, fromId, targetId);
		writeHubTileOrder(hubTileOrder);
	}

	const cardCoachItems = $derived(buildLeadCardCoachItems(lead, leadTasksList));
	const hubTileAlerts = $derived(hubTileAlertsFromCoach(cardCoachItems));

	let leadTasksList = $state([]);
	let leadTasksLoading = $state(false);
	let leadTaskSaving = $state(false);
	let leadTaskFormOpen = $state(false);
	let leadTaskTitle = $state('');
	let leadTaskDue = $state('');
	let leadTaskIntent = $state('');

	const stageTransitionRules = $derived(getCachedCrmConfig()?.stageTransitionRules ?? []);

	// ─── Агенты ─────────────────────────────────────────────────
	let agentRunning  = $state('');
	let agentResult   = $state(null);
	let agentError    = $state('');
	let agentTask     = $state('');
	let showAgentTask = $state(false);
	let pendingAgent  = $state('');
	let agentHistory  = $state([]);
	let showHistory   = $state(false);
	let feedbackSent  = $state('');     // 'good' | 'bad' | ''
	let feedbackNote  = $state('');
	let showBadNote   = $state(false);

	const AGENT_LIST = [
		{ key: 'marketer',   label: 'Маркетолог', desc: 'Прочитает переписку → напишет письмо', icon: '✉️' },
		{ key: 'analyst',    label: 'Аналитик',   desc: 'Пересчитает скоринг и даст рекомендации', icon: '📊' },
		{ key: 'strategist', label: 'Стратег',    desc: 'Предложит следующий шаг по сделке', icon: '🧠' },
		{ key: 'economist',  label: 'Экономист',  desc: 'Рассчитает ROI и обоснует бюджет', icon: '💰' },
		{ key: 'tech_specialist', label: 'Тех. спец', desc: 'Стек, интеграции, тех. разбор карточки', icon: '⚙️' },
	];

	function startAgent(agentKey) {
		pendingAgent  = agentKey;
		agentTask     = '';
		agentResult   = null;
		agentError    = '';
		showAgentTask = true;
	}

	async function runAgent() {
		if (!lead) return;
		agentRunning  = pendingAgent;
		agentResult   = null;
		agentError    = '';
		feedbackSent  = '';
		showAgentTask = false;
		try {
			const r = await fetch('/api/agents/email/run', {
				method:  'POST',
				headers: { 'Content-Type': 'application/json' },
				body:    JSON.stringify({ lead_id: lead.id, agent: pendingAgent, task: agentTask }),
			});
			if (!r.ok) throw new Error(await r.text());
			agentResult = await r.json();
		} catch (e) { agentError = '❌ ' + e.message; }
		finally { agentRunning = ''; }
	}

	async function sendFeedback(type) {
		if (!agentResult?.run_id) return;
		feedbackSent = type;
		if (type === 'bad') { showBadNote = true; return; }
		await _postFeedback(type, '');
	}

	async function submitBadNote() {
		showBadNote = false;
		await _postFeedback('bad', feedbackNote);
		feedbackNote = '';
	}

	async function _postFeedback(type, note) {
		try {
			await fetch('/api/agents/email/feedback', {
				method:  'POST',
				headers: { 'Content-Type': 'application/json' },
				body:    JSON.stringify({ run_id: agentResult.run_id, feedback: type, note }),
			});
		} catch (e) { console.error(e); }
	}

	async function markFewShot() {
		if (!agentResult?.run_id) return;
		try {
			await fetch('/api/agents/email/few-shots', {
				method:  'POST',
				headers: { 'Content-Type': 'application/json' },
				body:    JSON.stringify({ run_id: agentResult.run_id }),
			});
			feedbackSent = 'good';
		} catch (e) { console.error(e); }
	}

	async function loadHistory() {
		if (!lead) return;
		try {
			const r = await fetch(`/api/agents/email/history/${lead.id}`);
			if (r.ok) agentHistory = await r.json();
		} catch (e) { console.error(e); }
		showHistory = true;
	}

	// ─── Email-таб ──────────────────────────────────────────────
	let emailAccounts      = $state([]);
	let leadThreads        = $state([]);
	let loadingEmails      = $state(false);
	let emailsLoaded       = $state(false);

	// compose
	let showCompose    = $state(false);
	let composeTo      = $state('');
	let composeSubject = $state('');
	let composeBody    = $state('');
	let sendingNew     = $state(false);
	let composeError   = $state('');
	let composeSent    = $state(false);

	// тред
	let selectedThread  = $state(null);
	let threadMessages  = $state([]);
	let loadingMsgs     = $state(false);
	let replyBody       = $state('');
	let replyLoading    = $state(false);

	// ─── Рассылка с карточки (nurture и др.) ─────────────────────
	let nurtureChainCount = $state(0);

	async function refreshNurtureChainCount() {
		if (!lead?.id) {
			nurtureChainCount = 0;
			return;
		}
		try {
			const chains = await fetchNurtureChains(lead.id);
			nurtureChainCount = chains?.length ?? 0;
		} catch {
			nurtureChainCount = 0;
		}
	}

	$effect(() => {
		if (lead?.id) refreshNurtureChainCount();
	});

	// Загружаем письма только когда переходим на таб
	async function loadEmails() {
		if (emailsLoaded || !lead) return;
		loadingEmails = true;
		try {
			const [accs, threads] = await Promise.all([
				fetchEmailAccounts(),
				fetchEmailThreads({ lead_id: lead.id }),
			]);
			emailAccounts = accs;
			leadThreads   = threads;
			emailsLoaded  = true;
		} catch (e) {
			console.error('Ошибка загрузки писем лида:', e);
		} finally {
			loadingEmails = false;
		}
	}

	/** @param {string | null} panel @param {string} [tab] */
	function openHubPanel(panel, tab) {
		if (!panel) {
			openPanel = null;
			const url = new URL(get(page).url);
			url.searchParams.delete('panel');
			url.searchParams.delete('tab');
			const q = url.searchParams.toString();
			goto(`${url.pathname}${q ? `?${q}` : ''}`, { replaceState: true, keepFocus: true, noScroll: true });
			return;
		}
		if (panel === 'stages' || panel === 'header' || panel === 'dealPath') {
			openPanel = null;
			const url = new URL(get(page).url);
			url.searchParams.delete('panel');
			url.searchParams.delete('tab');
			const q = url.searchParams.toString();
			goto(`${url.pathname}${q ? `?${q}` : ''}`, { replaceState: true, keepFocus: true, noScroll: true });
			queueMicrotask(() => {
				document
					.querySelector('[data-testid="lead-card-header-stages"]')
					?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
			});
			return;
		}
		let next = panel;
		let nextClient = clientTab;
		let nextWork = workTab;
		if (panel === 'card' || panel === 'passport') {
			next = 'client';
			nextClient = panel === 'passport' ? 'passport' : 'card';
		} else if (panel === 'activity' || panel === 'tasks') {
			next = 'work';
			nextWork = panel === 'tasks' ? 'tasks' : 'activity';
		} else if (panel === 'client') {
			nextClient = tab === 'passport' ? 'passport' : 'card';
		} else if (panel === 'work') {
			nextWork = tab === 'tasks' ? 'tasks' : 'activity';
		}
		openPanel = next;
		clientTab = nextClient;
		workTab = nextWork;
		if (next === 'emails') loadEmails();
		if (next === 'work') {
			loadLeadTasks();
			if (nextWork === 'activity') loadLeadActivity();
		}
		if (next === 'client' && nextClient === 'card') {
			/* noop */
		}
		const url = new URL(get(page).url);
		url.searchParams.set('panel', next);
		const sub =
			next === 'client' ? nextClient : next === 'work' ? nextWork : '';
		if (sub && (next === 'client' || next === 'work')) url.searchParams.set('tab', sub);
		else url.searchParams.delete('tab');
		const q = url.searchParams.toString();
		goto(`${url.pathname}${q ? `?${q}` : ''}`, { replaceState: true, keepFocus: true, noScroll: true });
	}

	function closeHubPanel() {
		openHubPanel(null);
	}

	function setClientTab(tab) {
		clientTab = tab;
		openHubPanel('client', tab);
	}

	function setWorkTab(tab) {
		workTab = tab;
		openHubPanel('work', tab);
	}

	// ─── Compose ────────────────────────────────────────────────
	function openCompose(to = '', subject = '', body = '') {
		composeTo      = to || lead?.email || '';
		composeSubject = subject;
		composeBody    = body;
		composeError   = '';
		composeSent    = false;
		showCompose    = true;
	}

	async function sendEmail() {
		composeError = '';
		if (!composeTo || !composeSubject) { composeError = 'Заполни кому и тему'; return; }
		sendingNew = true;
		try {
			const r = await fetch('/api/email/send', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					to: [composeTo],
					subject: composeSubject,
					body: composeBody,
					lead_id: lead?.id,
				}),
			});
			if (!r.ok) throw new Error(await r.text());
			composeSent  = true;
			emailsLoaded = false;          // сбросить кэш
			await loadEmails();            // перезагрузить
			setTimeout(() => { showCompose = false; }, 1200);
		} catch (e) { composeError = '❌ ' + e.message; }
		finally { sendingNew = false; }
	}

	// ─── Thread detail ──────────────────────────────────────────
	async function openThread(thread) {
		selectedThread = thread;
		threadMessages = [];
		replyBody      = '';
		loadingMsgs    = true;
		try {
			const r = await fetch(`/api/email/threads/${thread.id}/messages`);
			if (r.ok) threadMessages = await r.json();
		} catch (e) { console.error(e); }
		finally { loadingMsgs = false; }
	}

	function closeThread() { selectedThread = null; threadMessages = []; replyBody = ''; }

	async function sendReply() {
		if (!replyBody.trim() || !selectedThread) return;
		replyLoading = true;
		try {
			const r = await fetch('/api/email/reply', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ thread_id: selectedThread.id, body: replyBody }),
			});
			if (!r.ok) throw new Error(await r.text());
			const data = await r.json();
			threadMessages = [...threadMessages, data.message];
			replyBody = '';
		} catch (e) { alert('Ошибка: ' + e.message); }
		finally { replyLoading = false; }
	}

	// ─── helpers ────────────────────────────────────────────────
	function fmtTime(iso) {
		if (!iso) return '—';
		const d = new Date(iso);
		if (d.toDateString() === new Date().toDateString())
			return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
		return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
	}
	function fmtFull(iso) {
		if (!iso) return '—';
		return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
	}
</script>

{#if notFound}
	<div class="flex flex-col items-center justify-center flex-1 p-8 text-center">
		<p class="text-lg text-white mb-2">Лид не найден</p>
		<a href="/leads/list" class="text-indigo-400 hover:text-indigo-300 text-sm">← К списку лидов</a>
	</div>
{:else if lead}
	{@const _tier = leadPriorityTier(lead.score, getCachedCrmConfig())}
	<!-- Один скролл на всю карточку: шапка (этап+путь) иначе съедает высоту (~450px) и плитки остаются в ~90px без заметного скролла. -->
	<div class="flex-1 min-h-0 overflow-y-auto flex flex-col" data-testid="lead-card-scroll">
	<!-- Единая шапка: назад + название + мета + действия; этап и путь сделки -->
	<header
		class="flex flex-col gap-3 px-4 sm:px-6 pt-[18px] pb-3 border-b border-gray-800 bg-gray-900 shrink-0 overflow-visible"
		data-testid="lead-card-header"
	>
		<div class="flex items-start justify-between gap-3">
		<div class="flex items-start gap-2 sm:gap-3 min-w-0 flex-1">
			<a
				href="/leads/list"
				class="shrink-0 mt-0.5 text-gray-500 hover:text-white transition-colors text-sm"
				data-testid="lead-card-back"
			>← Лиды</a>
			<div class="min-w-0">
				<h1 class="text-base sm:text-lg font-bold text-white truncate leading-tight">{lead.company}</h1>
				<p class="text-[11px] sm:text-xs text-gray-500 mt-0.5 leading-snug flex flex-wrap items-center gap-x-1.5 gap-y-0.5" data-testid="lead-card-header-meta">
					{#if lead.contact && lead.contact !== '—'}
						<span>{lead.contact}{#if lead.position && lead.position !== '—'} · {lead.position}{/if}</span>
						<span class="text-gray-700" aria-hidden="true">·</span>
					{/if}
					<span class="text-green-400 font-semibold">{lead.score}/100</span>
					<span class="px-1.5 py-px rounded text-[10px] font-medium {priorityTierBadgeClass(_tier)}">{_tier.label}</span>
					<span>{lead.stage}</span>
					{#if leadManagerLabel(lead)}
						<span class="text-sky-300/90" data-testid="lead-card-manager">{leadManagerLabel(lead)}</span>
					{/if}
					{#if formatDealAmountLabel(lead)}
						<span class="text-amber-300/90 font-semibold tabular-nums" data-testid="lead-card-deal-amount">{formatDealAmountLabel(lead)}</span>
					{/if}
					{#if isRepeatLead(lead)}
						<span
							class="px-1.5 py-px rounded text-[10px] font-medium bg-violet-900/70 text-violet-200 border border-violet-700/50"
							data-testid="lead-repeat-badge"
						>Повторный лид</span>
					{/if}
					{#if lead.inn}
						<span>ИНН {lead.inn}</span>
					{/if}
				</p>
			</div>
		</div>
		<div class="flex items-center gap-0.5 sm:gap-1 flex-nowrap shrink-0 overflow-x-auto max-w-[52%] sm:max-w-none pt-1.5 pb-0.5" data-testid="lead-card-toolbar">
			<button
				type="button"
				data-testid="lead-card-enrich"
				title={enrichRunning ? 'Обогащение…' : 'Обогатить'}
				aria-label="Обогатить"
				class="w-9 h-9 flex items-center justify-center bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-sm text-white rounded-lg transition-colors"
				disabled={enrichRunning || researchRunning || !lead?.company}
				onclick={() => runLeadEnrich(false)}
			>{enrichRunning ? '⟳' : '✨'}</button>			<button
				type="button"
				data-testid="lead-card-research"
				title={researchRunning ? 'Исследование…' : 'Исследовать в интернете (Brave / Tavily / Serper)'}
				aria-label="Исследовать"
				class="w-9 h-9 flex items-center justify-center bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-sm text-gray-300 rounded-lg transition-colors"
				disabled={researchRunning || enrichRunning || !lead?.company}
				onclick={() => runLeadResearch(true)}
			>{researchRunning ? '⟳' : '🔍'}</button>
			<button
				type="button"
				data-testid="lead-export-pdf"
				title={exportPdfLoading ? 'Экспорт PDF…' : 'Экспорт PDF'}
				aria-label="Экспорт PDF"
				class="w-9 h-9 flex items-center justify-center bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-sm text-gray-300 rounded-lg transition-colors"
				disabled={exportPdfLoading}
				onclick={exportLeadPdf}
			>{exportPdfLoading ? '…' : '📄'}</button>
			<button
				type="button"
				data-testid="lead-push-bitrix"
				title={bitrixPushLoading ? 'Отправка в Битрикс…' : 'В Битрикс'}
				aria-label="В Битрикс"
				class="w-9 h-9 flex items-center justify-center bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors disabled:opacity-50"
				disabled={bitrixPushLoading}
				onclick={pushLeadBitrix}
			>{bitrixPushLoading ? '…' : '📤'}</button>
			<button
				type="button"
				data-testid="lead-push-amo"
				title={amoPushLoading ? 'Отправка в Amo…' : 'В Amo'}
				aria-label="В Amo"
				class="w-9 h-9 flex items-center justify-center bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors disabled:opacity-50"
				disabled={amoPushLoading}
				onclick={pushLeadAmo}
			>{amoPushLoading ? '…' : '🅰'}</button>
			<button
				type="button"
				data-testid="lead-push-hubspot"
				title={hubspotPushLoading ? 'Отправка в HubSpot…' : 'В HubSpot'}
				aria-label="В HubSpot"
				class="w-9 h-9 flex items-center justify-center bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors disabled:opacity-50"
				disabled={hubspotPushLoading}
				onclick={pushLeadHubspot}
			>{hubspotPushLoading ? '…' : '🅷'}</button>
			<button
				type="button"
				title="Анализ"
				aria-label="Анализ"
				class="w-9 h-9 flex items-center justify-center bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors"
			>📊</button>
			<button
				type="button"
				title="Голос"
				aria-label="Голос"
				class="w-9 h-9 flex items-center justify-center bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors"
			>🎙</button>
			<button
				type="button"
				data-testid="lead-card-delete"
				title={deleteBusy ? 'Удаление…' : 'Удалить лид'}
				aria-label="Удалить лид"
				class="w-9 h-9 flex items-center justify-center bg-red-950 hover:bg-red-900 disabled:opacity-50 text-sm text-red-200 rounded-lg transition-colors"
				disabled={deleteBusy}
				onclick={deleteCurrentLead}
			>{deleteBusy ? '…' : '🗑'}</button>
		</div>
		</div>

		<div class="space-y-2 min-w-0" data-testid="lead-card-header-stages">
			<div class="space-y-2" data-testid="lead-card-stages">
				<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Этап воронки</div>
				<div class="flex flex-wrap gap-1.5">
					{#each CRM_STAGES as stage}
						{@const stageRules = rulesForTargetStage(stageTransitionRules, stage)}
						<button
							type="button"
							disabled={stageSaving}
							onclick={() => setStage(stage)}
							title={stageRules.length
								? `Требования: ${stageRules.map(describeTransitionRule).join('; ')}`
								: stage}
							class="px-2.5 py-1 text-xs rounded-full transition-all disabled:opacity-50 {stageBadgeClass(stage)}
								{lead.stage === stage
								? 'ring-2 ring-white/35 font-semibold shadow-md'
								: 'opacity-80 hover:opacity-100'}"
						>
							{stage}
						</button>
					{/each}
				</div>
				{#if stageTransitionRules.length}
					<p class="text-[10px] text-gray-600 leading-snug">
						Правила из CRM/Ops: наведи на стадию — подсказка; при блокировке покажем детали.
					</p>
				{/if}
			</div>
			<LeadStageHints hints={lead.stageHints || []} />
			<div data-testid="lead-card-header-deal">
				<LeadDealPathPanel
					dealPath={lead.dealPath}
					approvalsDraft={approvalsDraft}
					stage={lead.stage}
					saving={approvalsSaving}
					onToggleApproval={toggleApprovalKey}
					onSave={saveApprovalsChecklist}
				/>
			</div>
			{#if lead.tenderLink?.title}
				<p class="text-xs text-indigo-400" data-testid="lead-tender-link">
					◇ Тендер:
					{#if lead.tenderLink.url && lead.tenderLink.url !== '#'}
						<a href={lead.tenderLink.url} target="_blank" rel="noopener" class="hover:underline">{lead.tenderLink.title}</a>
					{:else}
						{lead.tenderLink.title}
					{/if}
				</p>
			{/if}
		</div>
	</header>
	{#if researchRunning || (researchStatus && researchStatus !== 'done_llm')}
		<div
			class="px-6 py-1.5 text-xs border-b border-gray-800 bg-gray-900/80 {researchStatus === 'error' ? 'text-rose-400' : 'text-amber-300'}"
			data-testid="lead-card-research-status"
		>
			{researchRunning ? '⟳ ' : ''}{researchStatusLabelText}{researchRunning ? ` · ${researchElapsed}с` : ''}
		</div>
	{/if}
	{#if enrichMsg}
		<div class="px-6 py-1.5 text-xs border-b border-gray-800 bg-gray-900/80 text-gray-400" data-testid="lead-card-enrich-msg">{enrichMsg}</div>
	{/if}

	<div class="flex flex-col" data-testid="lead-card-main">
		<div class="p-4 sm:p-6" data-testid="lead-card-hub">
			<div class="w-full" data-testid="lead-card-overview">
				<LeadCardCoachBanner items={cardCoachItems} onOpen={openHubPanel} />
				<p class="text-[11px] text-gray-500 mb-3" data-testid="lead-hub-dnd-hint">
					Перетащите плитку, чтобы изменить порядок · сохраняется в этом браузере
				</p>
				<div class="grid grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4" data-testid="lead-card-hub-grid">
					{#each hubTiles as tile (tile.id)}
						<LeadHubTile
							icon={tile.icon}
							title={tile.title}
							preview={tile.preview}
							meta={tile.meta}
							accent={tile.accent}
							alert={Boolean(hubTileAlerts[tile.id])}
							testId="lead-hub-tile-{tile.id}"
							draggable={true}
							dragging={draggingHubId === tile.id}
							dropTarget={hubDropTarget === tile.id}
							ondragstart={(e) => onHubTileDragStart(e, tile.id)}
							ondragend={onHubTileDragEnd}
							ondragover={(e) => onHubTileDragOver(e, tile.id)}
							ondragleave={() => onHubTileDragLeave(tile.id)}
							ondrop={(e) => onHubTileDrop(e, tile.id)}
							onclick={() => openHubPanel(tile.id)}
						/>
					{/each}
				</div>
			</div>
		</div>
	</div>
	</div>

	<LeadSlideOver
		open={!!openPanel}
		title={PANEL_TITLES[openPanel] || ''}
		subtitle={lead.company}
		onClose={closeHubPanel}
		testId="lead-slide-over-{openPanel || 'closed'}"
	>
			{#if openPanel === 'products'}
				<LeadProductsPanel {lead} />
			{:else if openPanel === 'client'}
				<div class="flex gap-2 mb-3" data-testid="lead-client-tabs">
					<button type="button" class="px-3 py-1.5 text-xs rounded-lg {clientTab === 'card' ? 'bg-indigo-700 text-white' : 'bg-gray-900 text-gray-400 hover:text-white'}" onclick={() => setClientTab('card')} data-testid="lead-client-tab-card">Карточка</button>
					<button type="button" class="px-3 py-1.5 text-xs rounded-lg {clientTab === 'passport' ? 'bg-indigo-700 text-white' : 'bg-gray-900 text-gray-400 hover:text-white'}" onclick={() => setClientTab('passport')} data-testid="lead-client-tab-passport">Паспорт</button>
				</div>
				{#if clientTab === 'card'}
				<LeadClientCardForm
					{lead}
					bind:detailsDraft
					bind:contactsDraft
					bind:moneyAmountStr
					bind:moneyPaidStr
					{industryOptions}
					{detailsSaving}
					{contactsSaving}
					{moneySaving}
					onSaveDetails={saveDetailsFields}
					onSaveContacts={saveContactsFields}
					onSaveMoney={saveMoneyFields}
					onOpenIndustry={openIndustryModal}
					onWriteEmail={(email) => { openHubPanel('emails'); openCompose(email); }}
					onOpenAgents={() => openHubPanel('agents')}
				/>

				{:else}
					{#if !passportHasData(lead)}
						<div class="text-center py-12 text-gray-600 text-sm" data-testid="lead-passport-empty">
							Паспорт пуст. Укажите ИНН, создайте лид через Лидогенератор или нажмите ✨ Обогатить.
						</div>
					{:else}
						<LeadPassportPanel {lead} />
					{/if}
				{/if}
			{:else if openPanel === 'work'}
				<div class="flex gap-2 mb-3" data-testid="lead-work-tabs">
					<button type="button" class="px-3 py-1.5 text-xs rounded-lg {workTab === 'activity' ? 'bg-indigo-700 text-white' : 'bg-gray-900 text-gray-400 hover:text-white'}" onclick={() => setWorkTab('activity')} data-testid="lead-work-tab-activity">История</button>
					<button type="button" class="px-3 py-1.5 text-xs rounded-lg {workTab === 'tasks' ? 'bg-indigo-700 text-white' : 'bg-gray-900 text-gray-400 hover:text-white'}" onclick={() => setWorkTab('tasks')} data-testid="lead-work-tab-tasks">Задачи</button>
				</div>
				{#if workTab === 'activity'}
				<div class="min-w-0" data-testid="lead-card-overview-activity">
					<div class="min-w-0 flex-1" data-testid="lead-card-overview-right">
						<LeadActivityPanel
							leadId={lead.id}
							relatedLead={lead.company}
							tasks={leadTasksList}
							tasksLoading={leadTasksLoading}
							communications={leadComms}
							comments={leadComments}
							audit={leadAudit}
							onSaved={loadLeadActivity}
							onTasksChanged={loadLeadTasks}
						/>
					</div>
				</div>

				{:else}
					<div class="mb-4 rounded-xl border border-gray-800 bg-gray-900/80 p-4 space-y-2" data-testid="lead-sla-protocol">
						<div class="text-sm font-medium text-white">SLA-протокол</div>
						<select
							class="w-full rounded-lg bg-gray-950 border border-gray-700 px-3 py-2 text-sm text-white"
							disabled={slaAssigning}
							value={lead.slaProtocolId || ''}
							onchange={(e) => changeSlaProtocol(e.currentTarget.value)}
						>
							<option value="">— Не назначен —</option>
							{#each slaProtocols as p}
								<option value={p.id}>{p.name}</option>
							{/each}
						</select>
						{#if lead.slaProtocol?.steps?.length}
							<ul class="text-xs text-gray-400 space-y-1 mt-2">
								{#each lead.slaProtocol.steps as step}
									<li class="flex justify-between gap-2">
										<span>{step.title}</span>
										<span class={step.escalated ? 'text-red-400' : 'text-gray-500'}>
											{step.sla_status || step.status}
										</span>
									</li>
								{/each}
							</ul>
						{/if}
						{#if slaMsg}
							<p class="text-xs text-gray-500">{slaMsg}</p>
						{/if}
					</div>
					<div class="space-y-2">
						{#if leadTasksLoading}
							<p class="text-gray-500 text-sm">Загрузка задач…</p>
						{:else if leadTasksList.length === 0}
							<p class="text-gray-600 text-sm">Задач по этому лиду пока нет.</p>
						{/if}
						{#each leadTasksList as task (task.id)}
							<div class="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
								<button
									type="button"
									class="w-4 h-4 rounded border {task.status === 'done' ? 'bg-green-500 border-green-500' : 'border-gray-600'} flex items-center justify-center shrink-0"
									onclick={() => toggleLeadTaskDone(task)}
									aria-label="Отметить выполненной"
								>
									{#if task.status === 'done'}<span class="text-white text-xs">✓</span>{/if}
								</button>
								<div class="flex-1 min-w-0">
									<div class="text-sm {task.status === 'done' ? 'line-through text-gray-500' : 'text-gray-200'}">{task.title}</div>
									<div class="text-xs text-gray-600 flex flex-wrap gap-2 mt-0.5">
										<span>Срок: {task.due || '—'}</span>
										{#if task.slaDue}
											<span class={slaStatus(task).cls}>SLA: {slaStatus(task).label}</span>
										{/if}
									</div>
								</div>
							</div>
						{/each}
						{#if leadTaskFormOpen}
							<div class="p-3 border border-gray-700 rounded-lg space-y-2" data-testid="lead-card-task-form">
								<input
									bind:value={leadTaskTitle}
									placeholder="Название задачи"
									class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
								/>
								<input
									bind:value={leadTaskDue}
									placeholder="Срок дд.мм.гггг"
									class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
								/>
								<select
									bind:value={leadTaskIntent}
									class="w-full rounded-lg bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-white"
									data-testid="lead-card-task-intent"
								>
									{#each TASK_INTENT_OPTIONS as opt (opt.id || 'auto')}
										<option value={opt.id}>{opt.label}</option>
									{/each}
								</select>
								<div class="flex gap-2">
									<button
										type="button"
										disabled={leadTaskSaving}
										onclick={addLeadTask}
										class="flex-1 py-2 rounded-lg bg-indigo-600 text-sm text-white disabled:opacity-50"
									>
										{leadTaskSaving ? 'Создание…' : 'Сохранить задачу'}
									</button>
									<button
										type="button"
										class="px-3 py-2 rounded-lg border border-gray-700 text-sm text-gray-400"
										onclick={() => (leadTaskFormOpen = false)}
									>
										Отмена
									</button>
								</div>
							</div>
						{:else}
						<button
							type="button"
							disabled={leadTaskSaving}
							onclick={addLeadTask}
							class="w-full p-3 border border-dashed border-gray-700 rounded-lg text-sm text-gray-500 hover:text-gray-300 hover:border-gray-500 transition-colors disabled:opacity-50"
						>
							+ Добавить задачу
						</button>
						{/if}
						<a href="/leads/tasks" class="block text-xs text-indigo-400 hover:underline">Все задачи и SLA →</a>
					</div>

				<!-- ── ПИСЬМА ── -->
				{/if}
			{:else if openPanel === 'emails'}
					<div class="flex flex-col h-full gap-4">

						<!-- шапка таба -->
						<div class="flex items-center justify-between gap-2 flex-wrap">
							<div>
								<h3 class="text-sm font-semibold text-white">Переписка с {lead.company}</h3>
								{#if lead.email && lead.email !== '—'}
									<p class="text-xs text-gray-500 mt-0.5">{lead.email}</p>
								{/if}
							</div>
							<div class="flex items-center gap-2">
								<button
									type="button"
									data-testid="lead-mailing-open"
									class="flex items-center gap-2 px-3 py-2 rounded-xl bg-violet-700 text-sm font-semibold text-white hover:bg-violet-600 transition-colors relative"
									onclick={() => lead && openLeadMailing(lead)}
								>
									🔗 Рассылка
									{#if nurtureChainCount > 0}
										<span class="absolute -top-1 -right-1 min-w-[1.1rem] h-[1.1rem] px-1 rounded-full bg-indigo-500 text-[10px] leading-[1.1rem] text-center font-bold">{nurtureChainCount}</span>
									{/if}
								</button>
								<button
									class="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors"
									onclick={() => openCompose(lead.email)}
								>✏ Написать</button>
							</div>
						</div>

						<!-- нет аккаунта -->
						{#if !loadingEmails && emailAccounts.length === 0}
							<div class="flex-1 flex flex-col items-center justify-center text-center py-10">
								<div class="text-3xl mb-3">✉️</div>
								<p class="text-gray-400 text-sm mb-3">Почта не подключена</p>
								<a href="/email" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors">
									Подключить почту →
								</a>
							</div>

						<!-- загрузка -->
						{:else if loadingEmails}
							<div class="text-gray-500 text-sm flex items-center gap-2">
								<span class="animate-spin">⟳</span> Загрузка писем...
							</div>

						<!-- нет писем -->
						{:else if leadThreads.length === 0}
							<div class="flex-1 flex flex-col items-center justify-center text-center py-10">
								<div class="text-3xl mb-3">✉️</div>
								<p class="text-gray-400 text-sm mb-1">Писем пока нет</p>
								<p class="text-gray-600 text-xs mb-4">Переписки с этим лидом ещё не было</p>
								<button
									class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors"
									onclick={() => openCompose(lead.email)}
								>✏ Написать первое письмо</button>
							</div>

						<!-- список тредов -->
						{:else}
							<div class="space-y-2">
								{#each leadThreads as thread (thread.id)}
									<button
										class="w-full text-left flex items-start gap-3 px-4 py-3 rounded-xl border border-gray-800 bg-gray-900
											   hover:bg-gray-800 hover:border-indigo-700 transition-colors group"
										onclick={() => openThread(thread)}
									>
										<div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5
											{thread.category === 'outbound' ? 'bg-indigo-800/60 text-indigo-300' : 'bg-gray-700 text-gray-300'}">
											{thread.category === 'outbound' ? '↑' : '↓'}
										</div>
										<div class="flex-1 min-w-0">
											<div class="flex items-baseline justify-between gap-2">
												<span class="text-sm font-semibold text-white truncate group-hover:text-indigo-300 transition-colors">
													{thread.subject || 'Без темы'}
												</span>
												<span class="text-xs text-gray-500 flex-shrink-0">{fmtTime(thread.lastMessageAt)}</span>
											</div>
											<p class="text-xs text-gray-400 truncate mt-0.5">{thread.snippet || ''}</p>
										</div>
									</button>
								{/each}
							</div>
						{/if}
					</div>

				<!-- ── АГЕНТЫ ── -->
				{:else if openPanel === 'agents'}
					<div class="space-y-4">
						<div class="flex items-center justify-between">
							<p class="text-sm text-gray-400">Агент читает переписку с клиентом и действует по настроенным правилам</p>
							<a href="/ops/email-agents" class="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">⚙ Настроить правила →</a>
						</div>

						{#if agentError}
							<div class="px-4 py-3 rounded-xl bg-red-950 border border-red-800 text-red-200 text-sm">{agentError}</div>
						{/if}

						<!-- кнопки агентов -->
						<div class="space-y-2">
							{#each AGENT_LIST as item}
								<div class="flex items-center gap-3 p-4 bg-gray-900 border border-gray-800 hover:border-indigo-800/60 rounded-xl transition-colors">
									<span class="text-xl flex-shrink-0">{item.icon}</span>
									<div class="flex-1 min-w-0">
										<div class="text-sm font-medium text-white">{item.label}</div>
										<div class="text-xs text-gray-500">{item.desc}</div>
									</div>
									<button
										onclick={() => startAgent(item.key)}
										disabled={agentRunning === item.key}
										class="flex-shrink-0 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white rounded-lg transition-colors disabled:bg-gray-700"
									>
										{agentRunning === item.key ? '⟳ Думает...' : 'Запустить'}
									</button>
								</div>
							{/each}
						</div>

						<!-- результат агента -->
						{#if agentResult}
							<div class="bg-gray-900 border border-indigo-800/50 rounded-2xl p-5 space-y-4">
								<!-- заголовок результата -->
								<div class="flex items-center justify-between flex-wrap gap-2">
									<span class="text-xs font-semibold text-indigo-400 uppercase tracking-wide">
										{AGENT_LIST.find(a => a.key === agentResult.agent)?.label} · результат
									</span>
									<div class="flex items-center gap-2 text-xs text-gray-600">
										<span>Тредов: {agentResult.threads_analyzed}</span>
										<span>·</span>
										<span>Правил: {agentResult.intents_applied}</span>
										{#if agentResult.few_shots_used > 0}
											<span>·</span>
											<span class="text-indigo-500">✦ few-shot</span>
										{/if}
									</div>
								</div>

								<!-- письмо -->
								{#if agentResult.result?.first_email}
									<div class="bg-gray-950 border border-gray-800 rounded-xl p-4">
										<div class="text-xs text-gray-500 mb-1">Тема:</div>
										<div class="text-sm font-semibold text-white mb-3">{agentResult.result.first_email.subject}</div>
										<div class="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{agentResult.result.first_email.body}</div>
										<button
											onclick={() => openCompose(lead.email, agentResult.result.first_email.subject, agentResult.result.first_email.body)}
											class="mt-3 px-4 py-1.5 rounded-lg bg-indigo-600 text-xs font-semibold text-white hover:bg-indigo-500 transition-colors"
										>↗ Открыть в compose</button>
									</div>
								{/if}

								{#if agentResult.result?.value_hook}
									<div class="text-sm text-gray-300 border-l-2 border-indigo-600 pl-3">
										<span class="text-xs text-gray-500 block mb-0.5">Крючок внимания</span>
										{agentResult.result.value_hook}
									</div>
								{/if}

								{#if agentResult.result?.summary}
									<p class="text-xs text-gray-500 italic">{agentResult.result.summary}</p>
								{/if}

								{#if agentResult.result?.touch_sequence?.length}
									<div>
										<div class="text-xs text-gray-500 mb-2">📅 План касаний</div>
										<div class="space-y-1">
											{#each agentResult.result.touch_sequence as t}
												<div class="text-xs text-gray-300">
													<span class="text-indigo-400 w-12 inline-block">День {t.day}</span>
													<span class="text-gray-600 mr-2">{t.channel}</span>
													{t.action}
												</div>
											{/each}
										</div>
									</div>
								{/if}

								<!-- 👍/👎 обратная связь -->
								<div class="border-t border-gray-800 pt-3 flex items-center gap-3 flex-wrap">
									<span class="text-xs text-gray-500">Качество ответа:</span>
									{#if feedbackSent === 'good'}
										<span class="text-xs text-green-400">✓ Отлично! Добавлено как пример для обучения.</span>
										<button onclick={markFewShot} class="text-xs text-indigo-400 hover:text-indigo-300 underline">+ В few-shot</button>
									{:else if feedbackSent === 'bad'}
										<span class="text-xs text-red-400">✗ Записано. Агент учтёт это.</span>
									{:else}
										<button onclick={() => sendFeedback('good')}
											class="flex items-center gap-1 px-3 py-1 rounded-lg bg-gray-800 hover:bg-green-900/40 hover:border-green-700 border border-gray-700 text-xs text-gray-300 hover:text-green-300 transition-colors">
											👍 Хорошо
										</button>
										<button onclick={() => sendFeedback('bad')}
											class="flex items-center gap-1 px-3 py-1 rounded-lg bg-gray-800 hover:bg-red-900/40 hover:border-red-700 border border-gray-700 text-xs text-gray-300 hover:text-red-300 transition-colors">
											👎 Плохо
										</button>
									{/if}
								</div>

								<!-- комментарий к плохому ответу -->
								{#if showBadNote}
									<div class="space-y-2">
										<textarea bind:value={feedbackNote}
											class="w-full h-16 rounded-xl bg-gray-950 border border-gray-700 px-3 py-2 text-sm text-white resize-none focus:outline-none focus:border-red-500 transition-colors"
											placeholder="Что именно не так? (опционально)"></textarea>
										<div class="flex gap-2">
											<button onclick={submitBadNote}
												class="px-4 py-1.5 rounded-lg bg-red-700 text-xs text-white hover:bg-red-600 transition-colors">
												Отправить отзыв
											</button>
											<button onclick={() => { showBadNote = false; feedbackNote = ''; }}
												class="px-4 py-1.5 rounded-lg bg-gray-800 text-xs text-gray-300 hover:bg-gray-700 transition-colors">
												Пропустить
											</button>
										</div>
									</div>
								{/if}
							</div>
						{/if}

						<!-- история запусков -->
						<div class="flex items-center justify-between">
							<button onclick={loadHistory}
								class="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
								{showHistory ? '▲ Скрыть историю' : '▼ История запусков агентов'}
							</button>
						</div>

						{#if showHistory}
							<div class="space-y-2">
								{#if agentHistory.length === 0}
									<p class="text-xs text-gray-600">История пуста.</p>
								{:else}
									{#each agentHistory as h (h.id)}
										<div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
											<div class="flex items-center justify-between gap-2">
												<div class="flex items-center gap-2">
													<span class="text-xs font-medium text-gray-300">{h.agentName}</span>
													{#if h.feedback === 'good'}
														<span class="text-xs text-green-500">👍</span>
													{:else if h.feedback === 'bad'}
														<span class="text-xs text-red-500">👎</span>
													{/if}
													{#if h.isFewShot}
														<span class="text-xs text-indigo-400">✦</span>
													{/if}
												</div>
												<span class="text-xs text-gray-600">{h.created}</span>
											</div>
											{#if h.task}
												<p class="text-xs text-gray-500 mt-1">Задача: {h.task}</p>
											{/if}
											{#if h.emailSubject}
												<p class="text-xs text-gray-400 mt-1 truncate">✉ {h.emailSubject}</p>
											{/if}
										</div>
									{/each}
								{/if}
							</div>
						{/if}
					</div>

				{/if}
	</LeadSlideOver>
{:else}
	<div class="flex flex-col items-center justify-center flex-1 p-8 text-gray-500 text-sm">Загрузка…</div>
{/if}

<!-- ═══ МОДАЛ: ЗАДАЧА ДЛЯ АГЕНТА ════════════════════════════ -->
{#if showAgentTask}
	<button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={() => showAgentTask = false} aria-label="Закрыть"></button>
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
		<div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-md pointer-events-auto">
			<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
				<h3 class="text-sm font-semibold text-white">
					{AGENT_LIST.find(a => a.key === pendingAgent)?.icon}
					{AGENT_LIST.find(a => a.key === pendingAgent)?.label}
				</h3>
				<button onclick={() => showAgentTask = false} class="text-gray-500 hover:text-white text-xl">&times;</button>
			</div>
			<div class="px-6 py-4 space-y-3">
				<p class="text-xs text-gray-500">Агент прочитает переписку с клиентом и применит настроенные правила. Можешь добавить конкретную задачу:</p>
				<textarea
					bind:value={agentTask}
					class="w-full h-24 rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white resize-none focus:outline-none focus:border-indigo-500 transition-colors"
					placeholder="Напр: 'Клиент интересовался ценой, предложи скидку 10%'"
				></textarea>
				<p class="text-xs text-gray-600">Если оставишь пустым — агент сам решит что нужно</p>
			</div>
			<div class="px-6 pb-5 flex gap-3">
				<button onclick={() => showAgentTask = false} class="flex-1 rounded-xl bg-gray-800 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors">Отмена</button>
				<button onclick={runAgent} class="flex-1 rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors">
					▶ Запустить
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- ═══ МОДАЛ: COMPOSE ════════════════════════════════════════ -->
{#if showCompose}
	<button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={() => showCompose = false} aria-label="Закрыть"></button>
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
		<div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-lg pointer-events-auto flex flex-col">
			<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
				<h2 class="text-sm font-semibold text-white">
					✏ Письмо {lead?.company ? '→ ' + lead.company : ''}
				</h2>
				<button onclick={() => showCompose = false} class="text-gray-500 hover:text-white text-xl">&times;</button>
			</div>
			<div class="px-6 py-4 space-y-0">
				<div class="flex items-center gap-3 border-b border-gray-800 py-3">
					<span class="text-xs text-gray-500 w-12 flex-shrink-0">Кому:</span>
					<input bind:value={composeTo} class="flex-1 bg-transparent text-sm text-white outline-none placeholder-gray-600" placeholder="email@example.com" />
				</div>
				<div class="flex items-center gap-3 border-b border-gray-800 py-3">
					<span class="text-xs text-gray-500 w-12 flex-shrink-0">Тема:</span>
					<input bind:value={composeSubject} class="flex-1 bg-transparent text-sm text-white outline-none placeholder-gray-600" placeholder="Тема письма" />
				</div>
				<textarea
					bind:value={composeBody}
					class="w-full h-48 bg-transparent text-sm text-white outline-none resize-none placeholder-gray-600 leading-relaxed py-4"
					placeholder="Текст письма..."
				></textarea>
				{#if composeError}<div class="text-red-400 text-xs pb-2">{composeError}</div>{/if}
				{#if composeSent}<div class="text-green-400 text-xs pb-2">✅ Письмо отправлено!</div>{/if}
			</div>
			<div class="px-6 pb-5 flex items-center justify-between border-t border-gray-800 pt-4">
				<button onclick={() => showCompose = false} class="text-sm text-gray-500 hover:text-white transition-colors">Отмена</button>
				<button onclick={sendEmail} disabled={sendingNew || !composeTo || !composeSubject}
					class="px-6 py-2 rounded-xl bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 transition-colors">
					{sendingNew ? 'Отправка...' : '↑ Отправить'}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- ═══ МОДАЛ: ТРЕД ═══════════════════════════════════════════ -->
{#if selectedThread}
	<button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={closeThread} aria-label="Закрыть"></button>
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
		<div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col pointer-events-auto">

			<div class="flex items-start gap-3 px-6 py-4 border-b border-gray-800 flex-shrink-0">
				<div class="flex-1 min-w-0">
					<h2 class="text-sm font-semibold text-white">{selectedThread.subject || 'Без темы'}</h2>
					<div class="flex items-center gap-2 mt-1">
						<span class="text-xs text-gray-500">{fmtFull(selectedThread.lastMessageAt)}</span>
						<span class="text-xs text-gray-600">·</span>
						<span class="text-xs text-gray-500">{threadMessages.length} сообщ.</span>
					</div>
				</div>
				<button onclick={closeThread} class="text-gray-500 hover:text-white text-2xl leading-none flex-shrink-0">&times;</button>
			</div>

			<div class="flex-1 overflow-y-auto px-6 py-4 space-y-4 min-h-0">
				{#if loadingMsgs}
					<div class="flex items-center gap-2 text-gray-500 text-sm"><span class="animate-spin">⟳</span> Загрузка...</div>
				{:else if threadMessages.length === 0}
					<p class="text-gray-500 text-sm">Нет сообщений.</p>
				{:else}
					{#each threadMessages as msg (msg.id)}
						<div class="rounded-xl border px-4 py-3
							{msg.direction === 'outbound' ? 'border-indigo-800/60 bg-indigo-950/30 ml-6' : 'border-gray-800 bg-gray-900 mr-6'}">
							<div class="flex items-center justify-between mb-2 gap-2">
								<div class="flex items-center gap-2 min-w-0">
									<div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0
										{msg.direction === 'outbound' ? 'bg-indigo-700 text-indigo-200' : 'bg-gray-700 text-gray-300'}">
										{msg.direction === 'outbound' ? '↑' : '↓'}
									</div>
									<span class="text-xs font-semibold text-gray-200 truncate">{msg.sender || '—'}</span>
								</div>
								<span class="text-xs text-gray-500 flex-shrink-0">{fmtFull(msg.sentAt)}</span>
							</div>
							{#if msg.recipients && msg.direction === 'outbound'}
								<p class="text-xs text-gray-600 mb-2">Кому: {msg.recipients}</p>
							{/if}
							<p class="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{msg.body || msg.snippet || '(нет текста)'}</p>
						</div>
					{/each}
				{/if}
			</div>

			<div class="px-6 py-4 border-t border-gray-800 flex-shrink-0">
				<div class="relative">
					<textarea
						bind:value={replyBody}
						class="w-full h-20 rounded-xl bg-gray-900 border border-gray-700 px-4 py-3 pr-28 text-sm text-white
							   resize-none focus:outline-none focus:border-indigo-500 transition-colors"
						placeholder="Написать ответ..."
					></textarea>
					<button
						onclick={sendReply}
						disabled={replyLoading || !replyBody.trim()}
						class="absolute bottom-3 right-3 px-4 py-1.5 rounded-lg bg-indigo-600 text-xs font-semibold text-white
							   hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 transition-colors"
					>{replyLoading ? '...' : '↑ Ответить'}</button>
				</div>
			</div>
		</div>
	</div>
{/if}
