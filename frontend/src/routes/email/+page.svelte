<script>
    import { onMount } from 'svelte';
    import {
        fetchEmailAccounts, connectEmailAccount, fetchEmailThreads,
        fetchEmailCampaigns, createCampaign, bindEmailToLead
    } from '$lib/emailStorage.js';
    import { fetchLeads } from '$lib/leadsStorage.js';

    // ─── данные ──────────────────────────────────────────────────
    let accounts    = $state([]);
    let threads     = $state([]);
    let campaigns   = $state([]);
    let leads       = $state([]);

    // ─── навигация ───────────────────────────────────────────────
    let activeFolder = $state('inbox');
    let searchQuery  = $state('');

    // ─── тред ────────────────────────────────────────────────────
    let selectedThread  = $state(null);
    let threadMessages  = $state([]);
    let loadingMessages = $state(false);
    let replyBody       = $state('');
    let replyLoading    = $state(false);

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

    // ─── кампании ────────────────────────────────────────────────
    let selectedAccountId = $state(null);
    let campaignName      = $state('');
    let campaignSubject   = $state('');
    let campaignBody      = $state('');
    let campaignLeadIds   = $state([]);
    let campaignLoading   = $state(false);
    let bindAccountId     = $state(null);
    let bindLeadId        = $state(null);

    let error   = $state('');
    let success = $state('');

    // ─── папки ───────────────────────────────────────────────────
    const folders = [
        { key: 'inbox',    label: 'Входящие',     icon: '📥' },
        { key: 'sent',     label: 'Отправленные', icon: '📤' },
        { key: 'zoho',     label: 'Zoho',         icon: '🔷' },
        { key: 'campaign', label: 'Рассылки',     icon: '📣' },
        { key: 'archive',  label: 'Архив',        icon: '🗂' },
    ];

    // ─── загрузка ────────────────────────────────────────────────
    async function load() {
        try {
            const raw = await fetchEmailAccounts();
            accounts  = raw.filter((v, i, s) => s.findIndex(a => a.username === v.username) === i);
            threads   = await fetchEmailThreads();
            campaigns = await fetchEmailCampaigns();
            leads     = await fetchLeads();
        } catch (e) { error = e.message; }
    }
    onMount(load);

    // ─── фильтрация ──────────────────────────────────────────────
    function getFiltered() {
        let list = threads;
        if (activeFolder === 'inbox')    list = list.filter(t => (t.category === 'inbound' || t.category === 'general') && !t.isArchived);
        if (activeFolder === 'sent')     list = list.filter(t => t.category === 'outbound');
        if (activeFolder === 'zoho')     list = list.filter(t => /zoho/i.test(t.subject + ' ' + t.snippet));
        if (activeFolder === 'campaign') list = list.filter(t => t.category === 'campaign');
        if (activeFolder === 'archive')  list = list.filter(t => t.isArchived);
        if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase();
            list = list.filter(t =>
                (t.subject || '').toLowerCase().includes(q) ||
                (t.snippet  || '').toLowerCase().includes(q)
            );
        }
        return list;
    }

    // ─── группировка по дате ─────────────────────────────────────
    function groupByDate(list) {
        const now       = new Date();
        const today     = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
        const weekAgo   = new Date(today); weekAgo.setDate(today.getDate() - 7);
        const groups    = new Map();
        for (const t of list) {
            const d = t.lastMessageAt ? new Date(t.lastMessageAt) : null;
            let label;
            if (!d) { label = 'Дата неизвестна'; }
            else {
                const day = new Date(d.getFullYear(), d.getMonth(), d.getDate());
                if      (day >= today)     label = 'Сегодня';
                else if (day >= yesterday) label = 'Вчера';
                else if (day >= weekAgo)   label = 'На этой неделе';
                else {
                    label = d.toLocaleString('ru-RU', { month: 'long', year: 'numeric' });
                    label = label.charAt(0).toUpperCase() + label.slice(1);
                }
            }
            if (!groups.has(label)) groups.set(label, []);
            groups.get(label).push(t);
        }
        return groups;
    }

    let grouped = $derived(groupByDate(getFiltered()));

    function folderCount(key) {
        if (key === 'inbox')    return threads.filter(t => (t.category === 'inbound' || t.category === 'general') && !t.isArchived).length;
        if (key === 'sent')     return threads.filter(t => t.category === 'outbound').length;
        if (key === 'zoho')     return threads.filter(t => /zoho/i.test(t.subject + ' ' + t.snippet)).length;
        if (key === 'campaign') return threads.filter(t => t.category === 'campaign').length;
        if (key === 'archive')  return threads.filter(t => t.isArchived).length;
        return 0;
    }

    // ─── compose ─────────────────────────────────────────────────
    function openCompose(to = '', subject = '') {
        composeTo      = to;
        composeSubject = subject;
        composeBody    = '';
        composeError   = '';
        showCompose    = true;
    }

    async function sendNewEmail() {
        composeError = '';
        if (!composeTo || !composeSubject) { composeError = 'Заполни кому и тему'; return; }
        sendingNew = true;
        try {
            const r = await fetch('/api/email/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ to: [composeTo], subject: composeSubject, body: composeBody }),
            });
            if (!r.ok) throw new Error(await r.text());
            threads = await fetchEmailThreads();
            showCompose = false;
            success = `✅ Письмо отправлено на ${composeTo}`;
            activeFolder = 'sent';
        } catch (e) { composeError = '❌ ' + e.message; }
        finally { sendingNew = false; }
    }

    // ─── тред ────────────────────────────────────────────────────
    async function openThread(thread) {
        selectedThread  = thread;
        threadMessages  = [];
        replyBody       = '';
        loadingMessages = true;
        try {
            const r = await fetch(`/api/email/threads/${thread.id}/messages`);
            if (r.ok) threadMessages = await r.json();
        } catch (e) { console.error(e); }
        finally { loadingMessages = false; }
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
            threads   = await fetchEmailThreads();
        } catch (e) { alert('Ошибка: ' + e.message); }
        finally { replyLoading = false; }
    }

    // ─── подключение ─────────────────────────────────────────────
    async function connect() {
        error = ''; success = '';
        if (!name || !username || !password) { error = '❌ Заполни название, email и пароль'; return; }
        connectLoading = true;
        try {
            const result = await connectEmailAccount({ name, provider, username, password, imap_server, imap_port, smtp_server, smtp_port, use_ssl });
            if (result.sync?.error) throw new Error(result.sync.error);
            accounts = await fetchEmailAccounts();
            threads  = await fetchEmailThreads();
            success  = `✅ Подключено. Импортировано ${result.sync?.imported ?? 0} писем.`;
            name = ''; username = ''; password = '';
            showSettings = false;
            activeFolder = 'inbox';
        } catch (e) { error = `❌ ${e.message}`; }
        finally { connectLoading = false; }
    }

    // ─── кампания ────────────────────────────────────────────────
    async function createNewCampaign() {
        if (!selectedAccountId || !campaignName || !campaignSubject || campaignLeadIds.length === 0) {
            error = '❌ Заполни все поля'; return;
        }
        error = ''; success = ''; campaignLoading = true;
        try {
            await createCampaign({ account_id: selectedAccountId, name: campaignName, subject: campaignSubject, body: campaignBody, lead_ids: campaignLeadIds, send_now: false });
            campaigns = await fetchEmailCampaigns();
            success   = `✅ Кампания "${campaignName}" создана.`;
            campaignName = ''; campaignSubject = ''; campaignBody = ''; campaignLeadIds = [];
        } catch (e) { error = `❌ ${e.message}`; }
        finally { campaignLoading = false; }
    }

    function toggleLead(id) {
        campaignLeadIds = campaignLeadIds.includes(id) ? campaignLeadIds.filter(x => x !== id) : [...campaignLeadIds, id];
    }

    // ─── форматирование ──────────────────────────────────────────
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

<!-- ═══ LAYOUT ════════════════════════════════════════════════ -->
<div class="flex h-full min-h-0 overflow-hidden">

    <!-- ── ЛЕВАЯ ПАНЕЛЬ ── -->
    <aside class="flex flex-col w-52 flex-shrink-0 border-r border-gray-800 bg-gray-950">

        <!-- кнопки действий -->
        <div class="px-3 pt-4 pb-3 space-y-1.5">
            <button
                class="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors"
                onclick={() => openCompose()}
            >✏ Написать письмо</button>
            <button
                class="w-full flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-800 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
                onclick={() => showSettings = !showSettings}
            >⚙ Подключить почту</button>
        </div>

        <!-- папки -->
        <nav class="flex-1 overflow-y-auto px-2 pt-1 space-y-0.5">
            {#each folders as f}
                {@const cnt = folderCount(f.key)}
                <button
                    class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors text-left
                           {activeFolder === f.key ? 'bg-indigo-600 text-white font-semibold' : 'text-gray-300 hover:bg-gray-800 hover:text-white'}"
                    onclick={() => { activeFolder = f.key; error = ''; success = ''; searchQuery = ''; }}
                >
                    <span class="text-base leading-none">{f.icon}</span>
                    <span class="flex-1">{f.label}</span>
                    {#if cnt > 0}
                        <span class="text-xs rounded-full px-1.5 py-0.5 min-w-[20px] text-center
                            {activeFolder === f.key ? 'bg-indigo-400/40' : 'bg-gray-700 text-gray-400'}">
                            {cnt}
                        </span>
                    {/if}
                </button>
            {/each}

            <!-- разделитель + Рассылки как раздел -->
            <div class="pt-3 pb-1 px-3">
                <div class="text-xs text-gray-600 uppercase tracking-wider">Кампании</div>
            </div>
            <button
                class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors text-left
                       {activeFolder === 'campaigns_manage' ? 'bg-indigo-600 text-white font-semibold' : 'text-gray-300 hover:bg-gray-800 hover:text-white'}"
                onclick={() => { activeFolder = 'campaigns_manage'; error = ''; success = ''; }}
            >
                <span class="text-base leading-none">📋</span>
                <span>Управление</span>
            </button>
        </nav>

        <!-- аккаунт внизу -->
        {#if accounts.length}
            <div class="px-4 py-3 border-t border-gray-800">
                <div class="text-xs text-gray-400 font-medium truncate">{accounts[0].username}</div>
                <div class="text-xs text-gray-600 mt-0.5">
                    {accounts[0].lastSyncedAt
                        ? new Date(accounts[0].lastSyncedAt).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
                        : 'Не синхронизировано'}
                </div>
            </div>
        {:else}
            <div class="px-4 py-3 border-t border-gray-800">
                <div class="text-xs text-gray-600">Почта не подключена</div>
            </div>
        {/if}
    </aside>

    <!-- ── ПРАВАЯ ЧАСТЬ ── -->
    <div class="flex flex-col flex-1 min-w-0 min-h-0 overflow-hidden">

        <!-- уведомления -->
        {#if error}   <div class="mx-5 mt-3 px-4 py-2.5 rounded-xl bg-red-950  border border-red-800  text-red-200  text-sm flex-shrink-0">{error}</div>   {/if}
        {#if success} <div class="mx-5 mt-3 px-4 py-2.5 rounded-xl bg-green-950 border border-green-800 text-green-200 text-sm flex-shrink-0">{success}</div> {/if}

        <!-- ════ СПИСОК ПИСЕМ ════ -->
        {#if activeFolder !== 'campaign' && activeFolder !== 'campaigns_manage'}

            <!-- поиск -->
            <div class="px-5 pt-4 pb-3 flex-shrink-0">
                <div class="relative">
                    <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm pointer-events-none">🔍</span>
                    <input
                        bind:value={searchQuery}
                        class="w-full rounded-xl bg-gray-900 border border-gray-700 pl-9 pr-8 py-2.5 text-sm text-white
                               placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
                        placeholder="Поиск по теме и содержимому..."
                    />
                    {#if searchQuery}
                        <button class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white text-xs" onclick={() => searchQuery = ''}>✕</button>
                    {/if}
                </div>
            </div>

            <!-- письма -->
            <div class="flex-1 overflow-y-auto min-h-0 px-5 pb-6">
                {#if accounts.length === 0}
                    <div class="mt-10 text-center">
                        <p class="text-gray-400 text-sm mb-3">Почта не подключена</p>
                        <button class="px-5 py-2.5 rounded-xl bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors" onclick={() => showSettings = true}>
                            ⚙ Подключить почту
                        </button>
                    </div>
                {:else if grouped.size === 0}
                    <p class="mt-6 text-gray-500 text-sm">
                        {searchQuery ? `Ничего не найдено по «${searchQuery}»` : 'Нет писем в этой папке.'}
                    </p>
                {:else}
                    {#each grouped as [label, items]}
                        <div class="sticky top-0 z-10 py-2 mt-2 bg-gray-950/90 backdrop-blur-sm">
                            <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">{label}</span>
                        </div>
                        <div class="space-y-px mb-2">
                            {#each items as thread (thread.id)}
                                <button
                                    class="w-full text-left flex items-start gap-3 px-3 py-3 rounded-lg
                                           hover:bg-gray-800/70 transition-colors group"
                                    onclick={() => openThread(thread)}
                                >
                                    <div class="flex-shrink-0 w-9 h-9 rounded-full bg-indigo-900/60 flex items-center justify-center text-sm font-bold text-indigo-300 select-none mt-0.5">
                                        {(thread.subject || '?').charAt(0).toUpperCase()}
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
                    {/each}
                {/if}
            </div>
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
                        <textarea bind:value={campaignBody} class="w-full h-28 rounded-xl bg-gray-950 border border-gray-800 px-4 py-2.5 text-sm text-white resize-none" placeholder="Текст письма..."></textarea>
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
                        <div class="text-sm text-gray-300">{a.name} <span class="text-gray-500">({a.username})</span></div>
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
                <button onclick={sendNewEmail} disabled={sendingNew || !composeTo || !composeSubject}
                    class="px-6 py-2 rounded-xl bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 transition-colors">
                    {sendingNew ? 'Отправка...' : '↑ Отправить'}
                </button>
            </div>
        </div>
    </div>
{/if}

<!-- ═══ МОДАЛ: ТРЕД ══════════════════════════════════════════ -->
{#if selectedThread}
    <button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={closeThread} aria-label="Закрыть"></button>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col pointer-events-auto">

            <!-- заголовок -->
            <div class="flex items-start gap-3 px-6 py-4 border-b border-gray-800 flex-shrink-0">
                <div class="flex-1 min-w-0">
                    <h2 class="text-sm font-semibold text-white">{selectedThread.subject || 'Без темы'}</h2>
                    <div class="flex items-center gap-3 mt-1">
                        <span class="text-xs text-gray-500">{selectedThread.category}</span>
                        <span class="text-xs text-gray-600">·</span>
                        <span class="text-xs text-gray-500">{fmtFull(selectedThread.lastMessageAt)}</span>
                        <span class="text-xs text-gray-600">·</span>
                        <span class="text-xs text-gray-500">{threadMessages.length} сообщ.</span>
                    </div>
                </div>
                <button onclick={closeThread} class="text-gray-500 hover:text-white text-2xl leading-none flex-shrink-0">&times;</button>
            </div>

            <!-- сообщения -->
            <div class="flex-1 overflow-y-auto px-6 py-4 space-y-4 min-h-0">
                {#if loadingMessages}
                    <div class="flex items-center gap-2 text-gray-500 text-sm">
                        <span class="animate-spin">⟳</span> Загрузка сообщений...
                    </div>
                {:else if threadMessages.length === 0}
                    <p class="text-gray-500 text-sm">Нет сообщений в этом треде.</p>
                {:else}
                    {#each threadMessages as msg (msg.id)}
                        <div class="rounded-xl border px-4 py-3
                            {msg.direction === 'outbound' ? 'border-indigo-800/60 bg-indigo-950/30 ml-8' : 'border-gray-800 bg-gray-900 mr-8'}">
                            <div class="flex items-center justify-between mb-2 gap-2">
                                <div class="flex items-center gap-2 min-w-0">
                                    <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0
                                        {msg.direction === 'outbound' ? 'bg-indigo-700 text-indigo-200' : 'bg-gray-700 text-gray-300'}">
                                        {(msg.sender || '?').charAt(0).toUpperCase()}
                                    </div>
                                    <span class="text-xs font-semibold text-gray-200 truncate">{msg.sender || '—'}</span>
                                    {#if msg.recipients && msg.direction === 'outbound'}
                                        <span class="text-xs text-gray-600 truncate">→ {msg.recipients}</span>
                                    {/if}
                                </div>
                                <span class="text-xs text-gray-500 flex-shrink-0">{fmtFull(msg.sentAt)}</span>
                            </div>
                            <p class="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{msg.body || msg.snippet || '(нет текста)'}</p>
                        </div>
                    {/each}
                {/if}
            </div>

            <!-- ответ -->
            <div class="px-6 py-4 border-t border-gray-800 flex-shrink-0">
                <div class="relative">
                    <textarea
                        bind:value={replyBody}
                        class="w-full h-24 rounded-xl bg-gray-900 border border-gray-700 px-4 py-3 pr-28 text-sm text-white
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
