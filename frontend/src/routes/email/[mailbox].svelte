<script>
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { fetchEmailThreads, fetchEmailCampaigns, archiveEmail } from '$lib/emailStorage.js';

    let threads        = $state([]);
    let campaigns      = $state([]);
    let activeTab      = $state('inbox');
    let loading        = $state(true);
    let error          = $state('');
    let selectedThread = $state(null);
    let threadMessages = $state([]);
    let loadingMsgs    = $state(false);

    const tabs = [
        { key: 'inbox',    label: 'Входящие'     },
        { key: 'sent',     label: 'Отправленные' },
        { key: 'campaign', label: 'Рассылки'     },
        { key: 'archive',  label: 'Архив'        },
    ];

    async function load() {
        try {
            loading   = true;
            threads   = await fetchEmailThreads();
            campaigns = await fetchEmailCampaigns();
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    }

    onMount(load);

    function filteredThreads() {
        if (activeTab === 'inbox')    return threads.filter(t => t.category === 'inbound' || t.category === 'general');
        if (activeTab === 'sent')     return threads.filter(t => t.category === 'outbound');
        if (activeTab === 'campaign') return threads.filter(t => t.category === 'campaign');
        if (activeTab === 'archive')  return threads.filter(t => t.isArchived);
        return threads;
    }

    async function openThread(thread) {
        selectedThread = thread;
        threadMessages = [];
        loadingMsgs    = true;
        try {
            const r = await fetch(`/api/email/threads/${thread.id}/messages`);
            if (r.ok) threadMessages = await r.json();
        } catch (e) {
            console.error('Ошибка:', e);
        } finally {
            loadingMsgs = false;
        }
    }

    function closeThread() {
        selectedThread = null;
        threadMessages = [];
    }

    async function handleArchive(emailId) {
        try {
            await archiveEmail(emailId);
            threads = threads.map(t => t.id === emailId ? { ...t, isArchived: true, category: 'archive' } : t);
        } catch (e) {
            alert('Не удалось архивировать: ' + e.message);
        }
    }

    function fmtShort(iso) {
        if (!iso) return '—';
        const d = new Date(iso);
        const today = new Date();
        if (d.toDateString() === today.toDateString())
            return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
    }
</script>

<div class="flex flex-col h-full min-h-0">
    <!-- шапка -->
    <div class="flex items-center gap-2 px-6 pt-4 pb-3 border-b border-gray-800 flex-shrink-0">
        <h1 class="text-lg font-semibold text-white flex-1">Почта</h1>
        <nav class="flex gap-1">
            {#each tabs as tab}
                <button
                    class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors
                           {activeTab === tab.key ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}"
                    onclick={() => activeTab = tab.key}
                >{tab.label}</button>
            {/each}
        </nav>
    </div>

    {#if loading}
        <div class="px-6 py-6 text-gray-500 text-sm">Загрузка...</div>
    {:else if error}
        <div class="px-6 py-4 text-red-400 text-sm">{error}</div>
    {:else}
        <div class="flex-1 overflow-y-auto px-6 py-4 space-y-2 min-h-0">
            {#if filteredThreads().length === 0}
                <p class="text-gray-500 text-sm mt-4">Нет писем в этой категории.</p>
            {:else}
                {#each filteredThreads() as thread (thread.id)}
                    <button
                        class="w-full text-left rounded-xl border border-gray-800 bg-gray-900 px-4 py-3
                               hover:bg-gray-800 hover:border-indigo-700 transition-colors"
                        onclick={() => openThread(thread)}
                    >
                        <div class="flex items-start justify-between gap-2">
                            <span class="text-sm font-semibold text-white truncate flex-1">{thread.subject || 'Без темы'}</span>
                            <span class="text-xs text-gray-500 flex-shrink-0">{fmtShort(thread.lastMessageAt)}</span>
                        </div>
                        <p class="mt-1 text-xs text-gray-400 truncate">{thread.snippet || ''}</p>
                    </button>
                {/each}
            {/if}
        </div>
    {/if}
</div>

<!-- модал треда -->
{#if selectedThread}
    <button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={closeThread} aria-label="Закрыть"></button>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col pointer-events-auto">
            <div class="flex items-start gap-4 px-6 py-4 border-b border-gray-800 flex-shrink-0">
                <div class="flex-1 min-w-0">
                    <h2 class="text-sm font-semibold text-white">{selectedThread.subject || 'Без темы'}</h2>
                    <p class="text-xs text-gray-500 mt-0.5">{selectedThread.category}</p>
                </div>
                <button onclick={closeThread} class="text-gray-500 hover:text-white text-2xl leading-none">&times;</button>
            </div>

            <div class="flex-1 overflow-y-auto px-6 py-4 space-y-4 min-h-0">
                {#if loadingMsgs}
                    <p class="text-gray-500 text-sm">Загрузка...</p>
                {:else if threadMessages.length === 0}
                    <p class="text-gray-500 text-sm">Нет сообщений.</p>
                {:else}
                    {#each threadMessages as msg (msg.id)}
                        <div class="rounded-xl border px-4 py-3
                            {msg.direction === 'outbound' ? 'border-indigo-800 bg-indigo-950/40' : 'border-gray-800 bg-gray-900'}">
                            <div class="flex justify-between mb-1 gap-2">
                                <span class="text-xs font-semibold text-gray-300 truncate">{msg.sender || '—'}</span>
                                <span class="text-xs text-gray-500 flex-shrink-0">{msg.sentAt ? new Date(msg.sentAt).toLocaleString('ru-RU') : msg.created}</span>
                            </div>
                            <p class="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{msg.body || msg.snippet || '(нет текста)'}</p>
                        </div>
                    {/each}
                {/if}
            </div>
        </div>
    </div>
{/if}
