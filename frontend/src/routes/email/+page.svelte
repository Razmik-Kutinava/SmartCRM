<script>
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { get } from 'svelte/store';
    import {
        fetchEmailAccounts, connectEmailAccount, syncAllEmailAccounts, fetchEmailThreads,
        fetchEmailCampaigns, createCampaign, fetchEmailSyncStatus, previewCampaignSegment,
        sendEmail, replyToEmail, fetchThreadMessages, analyzeEmailThread,
        startEmailBackfill, deleteEmailAccount
    } from '$lib/emailStorage.js';
    import {
        filterEmailThreads, countEmailFolder, groupThreadsByDate,
        formatThreadTime, syncStatusLabel, createEmptySearchFilters,
        loadStarredThreadIds, toggleStarredThreadId, isEmailPanelFolder
    } from '$lib/email/emailListLogic.js';
    import EmailYandexSidebar from '../../components/email/EmailYandexSidebar.svelte';
    import EmailYandexSearchBar from '../../components/email/EmailYandexSearchBar.svelte';
    import EmailThreadView from '../../components/email/EmailThreadView.svelte';
    import { buildReplyApprovePreview, buildComposeApprovePreview } from '$lib/email/emailApproveLogic.js';
    import { voiceEmailContext } from '$lib/voice/voiceAction.js';
    import EmailApproveModal from '../../components/EmailApproveModal.svelte';
    import EmailNurturePanel from '../../components/EmailNurturePanel.svelte';
    import EmailCampaignPanel from '../../components/EmailCampaignPanel.svelte';
    import { fetchLeads } from '$lib/leadsStorage.js';

    // ─── данные ──────────────────────────────────────────────────
    let accounts    = $state([]);
    let threads     = $state([]);
    let campaigns   = $state([]);
    let leads       = $state([]);

    // ─── навигация ───────────────────────────────────────────────
    let activeFolder = $state('inbox');
    let searchQuery  = $state('');
    let searchFilters = $state(createEmptySearchFilters());
    let starredThreadIds = $state(loadStarredThreadIds());

    // ─── тред ────────────────────────────────────────────────────
    let selectedThread  = $state(null);
    let threadMessages  = $state([]);
    let loadingMessages = $state(false);
    let replyBody       = $state('');
    let replyLoading    = $state(false);
    let approvePreview  = $state(null);
    let approveLoading  = $state(false);
    let analyzeLoading  = $state(false);
    let analyzeResult   = $state(null);
    let analyzeError    = $state('');

    // ─── compose новое письмо ────────────────────────────────────
    let showCompose    = $state(false);
    let composeTo      = $state('');
    let composeSubject = $state('');
    let composeBody    = $state('');
    let sendingNew     = $state(false);
    let composeError   = $state('');

    // ─── настройки (подключение) ─────────────────────────────────
    let showSettings = $state(false);
    let name        = $state('');
    let provider    = $state('generic');
    let username    = $state('');
    let password    = $state('');
    let imap_server = $state('imap.yandex.com');
    let imap_port   = $state(993);
    let smtp_server = $state('smtp.yandex.com');
    let smtp_port   = $state(465);
    let use_ssl     = $state(true);
    let connectLoading = $state(false);
    let syncLoading    = $state(false);
    let backfillStarting = $state(false);
    let removingAccountId = $state(null);

    // ─── кампании ────────────────────────────────────────────────
    let selectedAccountId = $state(null);
    let campaignName      = $state('');
    let campaignSubject   = $state('');
    let campaignBody      = $state('');
    let campaignLeadIds   = $state([]);
    let campaignUseSegment = $state(false);
    let campaignStage     = $state('all');
    let campaignMinScore  = $state(50);
    let campaignSegmentCount = $state(null);
    let campaignLoading   = $state(false);
    let bindAccountId     = $state(null);
    let bindLeadId        = $state(null);
    let filterAccountId   = $state('');
    let syncStatus        = $state(null);

    let error   = $state('');
    let success = $state('');
    let nurtureInitialLeadId = $state(null);

    let filteredThreads = $derived(filterEmailThreads(threads, {
        folder: activeFolder,
        search: searchQuery,
        accountId: filterAccountId || null,
        searchFilters,
        starredIds: starredThreadIds,
    }));
    let grouped = $derived(groupThreadsByDate(filteredThreads));
    let showMailList = $derived(!isEmailPanelFolder(activeFolder));

    function folderCount(key) {
        return countEmailFolder(threads, key, starredThreadIds);
    }

    function onFolderChange() {
        error = '';
        success = '';
        searchQuery = '';
        searchFilters = createEmptySearchFilters();
    }

    function toggleThreadStar(e, threadId) {
        e.stopPropagation();
        starredThreadIds = toggleStarredThreadId(starredThreadIds, threadId);
    }
    async function load() {
        try {
            const raw = await fetchEmailAccounts();
            accounts  = raw.filter((v, i, s) => s.findIndex(a => a.username === v.username) === i);
            if (filterAccountId && !accounts.some(a => String(a.id) === String(filterAccountId))) {
                filterAccountId = '';
            }
            const threadParams = filterAccountId ? { account_id: String(filterAccountId) } : {};
            threads   = await fetchEmailThreads(threadParams);
            campaigns = await fetchEmailCampaigns();
            leads     = await fetchLeads();
            syncStatus = await fetchEmailSyncStatus().catch(() => null);
        } catch (e) { error = e.message; }
    }
    onMount(() => {
        const params = get(page).url.searchParams;
        const subject = params.get('subject');
        const body = params.get('body');
        const to = params.get('to');
        if (subject || body || to) {
            showCompose = true;
            if (subject) composeSubject = subject;
            if (body) composeBody = body;
            if (to) composeTo = to;
        }
        const panel = params.get('panel');
        const leadParam = params.get('lead');
        if (panel === 'nurture' || panel === 'nurture_touch') {
            activeFolder = 'nurture_touch';
            error = '';
            success = '';
        }
        if (leadParam) {
            const lid = parseInt(leadParam, 10);
            if (!Number.isNaN(lid)) nurtureInitialLeadId = lid;
        }
        const unsubVoice = voiceEmailContext.subscribe((ctx) => {
            if (!ctx) return;
            if (ctx.folder) activeFolder = ctx.folder;
            if (ctx.search) searchQuery = ctx.search;
            if (ctx.hint) success = ctx.hint;
            voiceEmailContext.set(null);
        });
        load();
        return () => unsubVoice();
    });

    // ─── compose ─────────────────────────────────────────────────
    function openCompose(to = '', subject = '') {
        composeTo      = to;
        composeSubject = subject;
        composeBody    = '';
        composeError   = '';
        showCompose    = true;
    }

    function sendNewEmail() {
        composeError = '';
        if (!composeTo || !composeSubject) { composeError = 'Заполни кому и тему'; return; }
        if (!composeBody.trim()) { composeError = 'Введите текст письма'; return; }
        approvePreview = buildComposeApprovePreview({
            to: composeTo,
            subject: composeSubject,
            body: composeBody,
        });
    }

    async function confirmApproveSend() {
        if (!approvePreview) return;
        approveLoading = true;
        try {
            if (approvePreview.kind === 'reply' && selectedThread) {
                const data = await replyToEmail({ thread_id: selectedThread.id, body: approvePreview.body });
                threadMessages = [...threadMessages, data.message];
                replyBody = '';
                analyzeResult = null;
                success = '✅ Ответ отправлен';
                await load();
            } else if (approvePreview.kind === 'compose') {
                await sendEmail({
                    to: [approvePreview.to],
                    subject: approvePreview.subject,
                    body: approvePreview.body,
                });
                await load();
                showCompose = false;
                success = `✅ Письмо отправлено на ${approvePreview.to}`;
                activeFolder = 'sent';
                composeTo = '';
                composeSubject = '';
                composeBody = '';
            }
            approvePreview = null;
        } catch (e) {
            const msg = e?.message || String(e);
            if (approvePreview?.kind === 'compose') composeError = '❌ ' + msg;
            else alert('Ошибка: ' + msg);
        } finally {
            approveLoading = false;
            replyLoading = false;
            sendingNew = false;
        }
    }

    function cancelApproveSend() {
        approvePreview = null;
        replyLoading = false;
        sendingNew = false;
    }

    // ─── тред ────────────────────────────────────────────────────
    async function openThread(thread) {
        selectedThread  = thread;
        threadMessages  = [];
        replyBody       = '';
        analyzeResult   = null;
        analyzeError    = '';
        loadingMessages = true;
        try {
            threadMessages = await fetchThreadMessages(thread.id);
        } catch (e) { console.error(e); }
        finally { loadingMessages = false; }
    }

    function closeThread() {
        selectedThread = null;
        threadMessages = [];
        replyBody = '';
        analyzeResult = null;
        analyzeError = '';
    }

    async function runThreadAnalyze() {
        if (!selectedThread) return;
        analyzeLoading = true;
        analyzeError = '';
        try {
            const body = selectedThread.leadId ? { lead_id: selectedThread.leadId } : {};
            analyzeResult = await analyzeEmailThread(selectedThread.id, body);
        } catch (e) {
            analyzeError = e.message || 'Ошибка анализа';
            analyzeResult = null;
        } finally {
            analyzeLoading = false;
        }
    }

    function applyDraftToReply() {
        if (!analyzeResult?.draft) return;
        const subj = analyzeResult.draft.subject || '';
        const text = analyzeResult.draft.body || '';
        replyBody = subj && !text.startsWith(subj)
            ? `Тема: ${subj}\n\n${text}`
            : text;
    }

    function requestSendReply() {
        if (!replyBody.trim() || !selectedThread) return;
        approvePreview = buildReplyApprovePreview({
            thread: selectedThread,
            messages: threadMessages,
            body: replyBody,
        });
    }

    // ─── синхронизация ───────────────────────────────────────────
    async function syncMail() {
        if (!accounts.length) { error = '❌ Сначала подключите почту'; return; }
        error = ''; success = '';
        syncLoading = true;
        try {
            const result = await syncAllEmailAccounts();
            await load();
            const n = result.imported ?? 0;
            const u = (result.updated ?? 0) + (result.fake_fixed ?? 0);
            success = n > 0
                ? `✅ +${n} новых писем`
                : u > 0
                    ? `✅ Обновлено ${u} писем (даты и порядок)`
                    : '✅ Актуально — новых писем нет';
        } catch (e) { error = `❌ ${e.message}`; }
        finally { syncLoading = false; }
    }

    async function startHistoryBackfill() {
        if (!accounts.length) { error = '❌ Сначала подключите почту'; return; }
        error = ''; success = '';
        backfillStarting = true;
        try {
            await startEmailBackfill(false);
            success = '✅ Догрузка истории запущена — идёт в фоне (батчи по 90 дней назад)';
            syncStatus = await fetchEmailSyncStatus().catch(() => null);
        } catch (e) { error = `❌ ${e.message}`; }
        finally { backfillStarting = false; }
    }

    // ─── подключение ─────────────────────────────────────────────
    async function connect() {
        error = ''; success = '';
        if (!name || !username || !password) { error = '❌ Заполни название, email и пароль'; return; }
        connectLoading = true;
        try {
            const result = await connectEmailAccount({ name, provider, username, password, imap_server, imap_port, smtp_server, smtp_port, use_ssl });
            if (result.sync?.error) throw new Error(result.sync.error);
            await load();
            success  = `✅ Подключено. Импортировано ${result.sync?.imported ?? 0} писем.`;
            name = ''; username = ''; password = '';
            showSettings = false;
            activeFolder = 'inbox';
        } catch (e) { error = `❌ ${e.message}`; }
        finally { connectLoading = false; }
    }

    async function disconnectAccount(account) {
        if (!confirm(`Отключить ящик ${account.username}? Вся переписка этого ящика будет удалена из CRM.`)) return;
        error = ''; success = '';
        removingAccountId = account.id;
        try {
            const r = await deleteEmailAccount(account.id, true);
            if (String(filterAccountId) === String(account.id)) filterAccountId = '';
            closeThread();
            await load();
            const rm = r.removed || {};
            success = `✅ Ящик ${account.username} отключён (писем: ${rm.messages ?? 0}, тредов: ${rm.threads ?? 0}).`;
        } catch (e) { error = `❌ ${e.message}`; }
        finally { removingAccountId = null; }
    }

    // ─── кампания ────────────────────────────────────────────────
    async function previewSegment() {
        try {
            const seg = { stage: campaignStage === 'all' ? '' : campaignStage, min_score: Number(campaignMinScore) };
            const r = await previewCampaignSegment(seg);
            campaignSegmentCount = r.count;
        } catch (e) { error = `❌ ${e.message}`; }
    }

    async function createNewCampaign() {
        if (!selectedAccountId || !campaignName || !campaignSubject) {
            error = '❌ Заполни название и тему'; return;
        }
        if (!campaignUseSegment && campaignLeadIds.length === 0) {
            error = '❌ Выбери лидов или сегмент'; return;
        }
        error = ''; success = ''; campaignLoading = true;
        try {
            const payload = {
                account_id: selectedAccountId,
                name: campaignName,
                subject: campaignSubject,
                body: campaignBody,
                send_now: false,
            };
            if (campaignUseSegment) {
                payload.segment = {
                    stage: campaignStage === 'all' ? '' : campaignStage,
                    min_score: Number(campaignMinScore),
                };
            } else {
                payload.lead_ids = campaignLeadIds;
            }
            await createCampaign(payload);
            campaigns = await fetchEmailCampaigns();
            success   = `✅ Кампания "${campaignName}" создана.`;
            campaignName = ''; campaignSubject = ''; campaignBody = ''; campaignLeadIds = [];
            campaignSegmentCount = null;
        } catch (e) { error = `❌ ${e.message}`; }
        finally { campaignLoading = false; }
    }

    function toggleLead(id) {
        campaignLeadIds = campaignLeadIds.includes(id) ? campaignLeadIds.filter(x => x !== id) : [...campaignLeadIds, id];
    }

    async function onAccountFilterChange() {
        await load();
    }
</script>

<!-- ═══ LAYOUT (Yandex Mail) ═════════════════════════════════ -->
<div class="flex h-full min-h-0 overflow-hidden bg-white">

    <EmailYandexSidebar
        bind:activeFolder
        bind:filterAccountId
        {accounts}
        {syncLoading}
        folderCount={folderCount}
        onCompose={() => openCompose()}
        onSync={syncMail}
        onSettings={() => { showSettings = !showSettings; }}
        onFolderChange={onFolderChange}
        onAccountFilterChange={onAccountFilterChange}
    />

    <!-- ── ПРАВАЯ ЧАСТЬ ── -->
    <div class="flex flex-col flex-1 min-w-0 min-h-0 overflow-hidden bg-white">

        {#if error}   <div class="mx-5 mt-3 px-4 py-2.5 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex-shrink-0">{error}</div>   {/if}
        {#if success} <div class="mx-5 mt-3 px-4 py-2.5 rounded-xl bg-green-50 border border-green-200 text-green-800 text-sm flex-shrink-0">{success}</div> {/if}
        {#if syncStatus && showMailList}
            <div class="mx-5 mt-2 px-4 py-2 rounded-xl bg-gray-50 border border-gray-100 text-gray-500 text-xs flex-shrink-0 flex flex-wrap items-center gap-3">
                <span class="flex-1 min-w-0">{syncStatusLabel(syncStatus)}</span>
                {#if accounts.length && syncStatus.backfill?.enabled}
                    <button
                        type="button"
                        class="text-[#0066cc] hover:underline whitespace-nowrap disabled:opacity-50"
                        disabled={backfillStarting}
                        onclick={startHistoryBackfill}
                        data-testid="email-backfill-start"
                    >{backfillStarting ? 'Запуск…' : 'Догрузить всю историю'}</button>
                {/if}
            </div>
        {/if}

        {#if showMailList}

            <EmailYandexSearchBar bind:searchQuery bind:searchFilters onSearch={() => {}} />

            <div class="flex-1 overflow-y-auto min-h-0 px-5 pb-6">
                {#if accounts.length === 0}
                    <div class="mt-10 text-center">
                        <p class="text-gray-500 text-sm mb-3">Почта не подключена</p>
                        <button class="px-5 py-2.5 rounded-2xl bg-[#ffdb4d] text-sm font-semibold text-gray-900 hover:bg-[#ffcc00] transition-colors" onclick={() => showSettings = true}>
                            Подключить почту
                        </button>
                    </div>
                {:else if grouped.size === 0}
                    <p class="mt-6 text-gray-500 text-sm">
                        {searchQuery || searchFilters.attachments ? 'Ничего не найдено по фильтрам.' : 'Нет писем в этой папке.'}
                    </p>
                {:else}
                    {#each grouped as [label, items]}
                        <div class="sticky top-0 z-10 py-2 mt-2 bg-white/95 backdrop-blur-sm">
                            <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">{label}</span>
                        </div>
                        <div class="space-y-px mb-2">
                            {#each items as thread (thread.id)}
                                <div
                                    role="button"
                                    tabindex="0"
                                    class="w-full text-left flex items-start gap-3 px-3 py-3 rounded-xl
                                           hover:bg-gray-50 transition-colors group border border-transparent hover:border-gray-100 cursor-pointer"
                                    onclick={() => openThread(thread)}
                                    onkeydown={(e) => e.key === 'Enter' && openThread(thread)}
                                >
                                    <span
                                        role="button"
                                        tabindex="0"
                                        class="flex-shrink-0 mt-1 p-0.5 text-gray-300 hover:text-amber-400 {starredThreadIds.has(String(thread.id)) ? 'text-amber-400' : ''}"
                                        onclick={(e) => toggleThreadStar(e, thread.id)}
                                        onkeydown={(e) => e.key === 'Enter' && toggleThreadStar(e, thread.id)}
                                        aria-label="Важное"
                                    >
                                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill={starredThreadIds.has(String(thread.id)) ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="2"><path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
                                    </span>
                                    <div class="flex-shrink-0 w-9 h-9 rounded-full bg-[#ffdb4d]/40 flex items-center justify-center text-sm font-bold text-gray-800 select-none mt-0.5">
                                        {(thread.subject || '?').charAt(0).toUpperCase()}
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <div class="flex items-baseline justify-between gap-2">
                                            <span class="text-sm font-semibold text-gray-900 truncate">
                                                {thread.subject || 'Без темы'}
                                            </span>
                                            <span class="text-xs text-gray-500 flex-shrink-0">{formatThreadTime(thread.lastMessageAt)}</span>
                                        </div>
                                        {#if thread.previewFrom}
                                            <p class="text-xs text-gray-500 truncate">{thread.previewFrom}</p>
                                        {/if}
                                        <p class="text-xs text-gray-400 truncate mt-0.5">{thread.snippet || ''}</p>
                                    </div>
                                </div>
                            {/each}
                        </div>
                    {/each}
                {/if}
            </div>
        {/if}

        {#if activeFolder === 'nurture_touch'}
            <EmailNurturePanel {accounts} {leads} bind:error bind:success initialLeadId={nurtureInitialLeadId} />
        {/if}

        {#if activeFolder === 'campaign_mass'}
            <EmailCampaignPanel {accounts} bind:error bind:success />
        {/if}

        <!-- ════ УПРАВЛЕНИЕ КАМПАНИЯМИ ════ -->
        {#if activeFolder === 'campaigns_manage' || activeFolder === 'campaign'}
            <div class="flex-1 overflow-y-auto min-h-0 px-5 py-4 space-y-5">
                <div class="grid gap-5 lg:grid-cols-[2fr_1fr]">
                    <div class="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
                        <p class="text-xs text-gray-400 uppercase tracking-wide font-semibold">Новая кампания</p>
                        <select bind:value={selectedAccountId} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5 text-sm text-white">
                            <option value={null}>Выбери аккаунт...</option>
                            {#each accounts as a}<option value={a.id}>{a.name} ({a.username})</option>{/each}
                        </select>
                        <input bind:value={campaignName}    class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5 text-sm text-white" placeholder="Название кампании" />
                        <input bind:value={campaignSubject} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5 text-sm text-white" placeholder="Тема письма" />
                        <textarea bind:value={campaignBody} class="w-full h-28 rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5 text-sm text-white resize-none" placeholder="Текст письма... {{company}} {{contact}}"></textarea>
                        <label class="flex items-center gap-2 text-sm text-gray-300">
                            <input type="checkbox" bind:checked={campaignUseSegment} data-testid="campaign-use-segment" class="accent-indigo-500" />
                            Рассылка по сегменту (stage + min score)
                        </label>
                        {#if campaignUseSegment}
                            <div class="grid grid-cols-2 gap-2">
                                <select bind:value={campaignStage} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white">
                                    <option value="all">Все этапы</option>
                                    <option value="Новый">Новый</option>
                                    <option value="Квалифицирован">Квалифицирован</option>
                                    <option value="Переговоры">Переговоры</option>
                                </select>
                                <input type="number" bind:value={campaignMinScore} class="rounded-xl bg-gray-950 border border-gray-800 px-3 py-2 text-sm text-white" placeholder="Min score" />
                            </div>
                            <button type="button" onclick={previewSegment} class="text-xs text-indigo-400 hover:underline">Предпросмотр сегмента</button>
                            {#if campaignSegmentCount != null}
                                <p class="text-xs text-gray-500" data-testid="campaign-segment-count">Лидов в сегменте: {campaignSegmentCount}</p>
                            {/if}
                        {/if}
                        <button onclick={createNewCampaign} disabled={campaignLoading}
                            class="w-full rounded-xl bg-green-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-green-500 disabled:bg-gray-700 transition-colors">
                            {campaignLoading ? 'Создание...' : 'Создать черновик кампании'}
                        </button>
                    </div>
                    <div class="bg-gray-900 border border-gray-800 rounded-2xl p-5">
                        <p class="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-3">Лиды ({campaignLeadIds.length})</p>
                        <div class="space-y-1 max-h-72 overflow-y-auto">
                            {#each leads as lead (lead.id)}
                                <label class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800 cursor-pointer transition-colors">
                                    <input type="checkbox" checked={campaignLeadIds.includes(lead.id)} onchange={() => toggleLead(lead.id)} class="accent-indigo-500" />
                                    <div class="min-w-0">
                                        <div class="text-sm text-white truncate">{lead.company}</div>
                                        <div class="text-xs text-gray-500 truncate">{lead.contact_email || 'нет email'}</div>
                                    </div>
                                </label>
                            {/each}
                        </div>
                    </div>
                </div>
                <div>
                    <p class="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-3">Все кампании ({campaigns.length})</p>
                    {#if campaigns.length}
                        <div class="space-y-2">
                            {#each campaigns as c (c.id)}
                                <div class="rounded-xl border border-gray-800 bg-gray-900 px-4 py-3 flex items-center justify-between gap-3">
                                    <div class="min-w-0">
                                        <div class="text-sm font-semibold text-white truncate">{c.name}</div>
                                        <div class="text-xs text-gray-400 truncate">{c.subject}</div>
                                        <div class="text-xs text-gray-600 mt-1">Лидов: {c.leadIds?.length ?? 0} · Отправлено: {c.sentCount} · {c.created}</div>
                                    </div>
                                    <span class="flex-shrink-0 text-xs px-2 py-1 rounded-full {c.status === 'sent' ? 'bg-green-900 text-green-300' : 'bg-gray-800 text-gray-400'}">
                                        {c.status === 'sent' ? 'Отправлено' : 'Черновик'}
                                    </span>
                                </div>
                            {/each}
                        </div>
                    {:else}
                        <p class="text-sm text-gray-500">Пока нет кампаний.</p>
                    {/if}
                </div>
            </div>
        {/if}
    </div>
</div>

<!-- ═══ МОДАЛ: НАСТРОЙКИ ПОДКЛЮЧЕНИЯ ════════════════════════ -->
{#if showSettings}
    <button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={() => showSettings = false} aria-label="Закрыть"></button>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-lg pointer-events-auto">
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
                <h2 class="text-sm font-semibold text-white">⚙ Подключить почту</h2>
                <button onclick={() => showSettings = false} class="text-gray-500 hover:text-white text-xl">&times;</button>
            </div>
            <div class="px-6 py-4 space-y-3">
                <div class="px-4 py-3 rounded-xl bg-yellow-950 border border-yellow-800 text-xs text-yellow-200 leading-relaxed">
                    ⚠️ Для Яндекс.Почты нужен <strong>пароль приложения</strong>, не обычный.
                    <a href="https://id.yandex.ru/security/app-passwords" target="_blank" rel="noreferrer" class="underline ml-1">Создать →</a>
                </div>
                <input bind:value={name}     class="w-full rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white" placeholder="Название аккаунта" />
                <input bind:value={username} class="w-full rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white" placeholder="email@yandex.ru" />
                <input type="password" bind:value={password} class="w-full rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white" placeholder="Пароль приложения" />
                <div class="grid grid-cols-2 gap-3">
                    <input bind:value={imap_server} class="rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white" placeholder="imap.yandex.com" />
                    <input type="number" bind:value={imap_port} class="rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white" />
                    <input bind:value={smtp_server} class="rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white" placeholder="smtp.yandex.com" />
                    <input type="number" bind:value={smtp_port} class="rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white" />
                </div>
                {#if error}<div class="text-red-400 text-sm">{error}</div>{/if}
                {#if success}<div class="text-green-400 text-sm">{success}</div>{/if}
            </div>
            <div class="px-6 pb-5 flex gap-3">
                <button onclick={() => showSettings = false} class="flex-1 rounded-xl bg-gray-800 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors">Отмена</button>
                <button onclick={connect} disabled={connectLoading} class="flex-1 rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-700 transition-colors">
                    {connectLoading ? 'Подключение...' : 'Подключить'}
                </button>
            </div>

            {#if accounts.length}
                <div class="px-6 pb-5 border-t border-gray-800 pt-4">
                    <p class="text-xs text-gray-500 uppercase tracking-wide mb-2">Подключённые аккаунты</p>
                    {#each accounts as a (a.id)}
                        <div class="flex items-center justify-between gap-3 py-1.5">
                            <div class="text-sm text-gray-300 min-w-0 truncate">{a.name} <span class="text-gray-500">({a.username})</span></div>
                            <button
                                onclick={() => disconnectAccount(a)}
                                disabled={removingAccountId === a.id}
                                class="flex-shrink-0 text-xs px-3 py-1 rounded-lg bg-red-900/40 border border-red-800 text-red-300 hover:bg-red-900/70 disabled:opacity-50 transition-colors"
                                data-testid="email-account-disconnect"
                            >{removingAccountId === a.id ? 'Отключение…' : 'Отключить'}</button>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </div>
{/if}

<!-- ═══ МОДАЛ: COMPOSE ═══════════════════════════════════════ -->
{#if showCompose}
    <button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={() => showCompose = false} aria-label="Закрыть"></button>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-lg pointer-events-auto flex flex-col">
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
                <h2 class="text-sm font-semibold text-white">✏ Новое письмо</h2>
                <button onclick={() => showCompose = false} class="text-gray-500 hover:text-white text-xl">&times;</button>
            </div>
            <div class="px-6 py-4 space-y-3">
                <div class="flex items-center gap-3 border-b border-gray-800 pb-3">
                    <span class="text-xs text-gray-500 w-12 flex-shrink-0">Кому:</span>
                    <input bind:value={composeTo} class="flex-1 bg-transparent text-sm text-white outline-none placeholder-gray-600" placeholder="email@example.com" />
                </div>
                <div class="flex items-center gap-3 border-b border-gray-800 pb-3">
                    <span class="text-xs text-gray-500 w-12 flex-shrink-0">Тема:</span>
                    <input bind:value={composeSubject} class="flex-1 bg-transparent text-sm text-white outline-none placeholder-gray-600" placeholder="Тема письма" />
                </div>
                <textarea
                    bind:value={composeBody}
                    class="w-full h-48 bg-transparent text-sm text-white outline-none resize-none placeholder-gray-600 leading-relaxed"
                    placeholder="Текст письма..."
                ></textarea>
                {#if composeError}<div class="text-red-400 text-xs">{composeError}</div>{/if}
            </div>
            <div class="px-6 pb-5 flex items-center justify-between">
                <button onclick={() => showCompose = false} class="text-sm text-gray-500 hover:text-white transition-colors">Отмена</button>
                <button onclick={sendNewEmail} disabled={sendingNew || !composeTo || !composeSubject || !composeBody.trim()}
                    class="px-6 py-2 rounded-xl bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 transition-colors">
                    ↑ Отправить
                </button>
            </div>
        </div>
    </div>
{/if}

<!-- ═══ ТРЕД (Yandex: одно письмо + сайдбар) ═══════════════════ -->
<EmailThreadView
    thread={selectedThread}
    messages={threadMessages}
    loading={loadingMessages}
    bind:replyBody
    {replyLoading}
    {approveLoading}
    analyzeLoading={analyzeLoading}
    analyzeResult={analyzeResult}
    analyzeError={analyzeError}
    onClose={closeThread}
    onAnalyze={runThreadAnalyze}
    onApplyDraft={applyDraftToReply}
    onReply={requestSendReply}
/>

<EmailApproveModal
    preview={approvePreview}
    loading={approveLoading}
    onConfirm={confirmApproveSend}
    onCancel={cancelApproveSend}
/>
