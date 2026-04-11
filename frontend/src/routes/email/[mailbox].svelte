<script>
import { onMount } from 'svelte';
import { fetchEmailAccounts, fetchEmailThreads, fetchEmailCampaigns } from '$lib/emailStorage.js';
import { archiveEmail } from '$lib/emailStorage.js';

let accounts = $state([]);
let threads = $state([]);
let campaigns = $state([]);
let activeTab = $state('inbox');
let loading = $state(true);
let error = $state('');

const tabs = [
  { key: 'inbox', label: 'Входящие' },
  { key: 'sent', label: 'Исходящие' },
  { key: 'campaign', label: 'Рассылки' },
  { key: 'archive', label: 'Архив' },
];

async function load() {
  try {
    loading = true;
    accounts = await fetchEmailAccounts();
    threads = await fetchEmailThreads();
    campaigns = await fetchEmailCampaigns();
  } catch (e) {
    error = e.message;
  } finally {
    loading = false;
  }
}

onMount(load);

async function handleArchiveEmail(emailId) {
  try {
    await archiveEmail(emailId);
    threads = threads.map(thread => thread.id === emailId ? { ...thread, category: 'archive' } : thread);
  } catch (e) {
    console.error('Ошибка архивации:', e);
    alert('Не удалось архивировать письмо.');
  }
}

function filteredThreads() {
  if (activeTab === 'inbox') return threads.filter(t => t.category === 'inbound' || t.category === 'general');
  if (activeTab === 'sent') return threads.filter(t => t.category === 'outbound');
  if (activeTab === 'campaign') return threads.filter(t => t.category === 'campaign');
  if (activeTab === 'archive') return threads.filter(t => t.category === 'archive');
  return threads;
}
</script>

<div class="p-6">
  <h1 class="text-2xl font-semibold text-white mb-4">Почта</h1>
  <div class="flex gap-2 mb-6">
    {#each tabs as tab}
      <button class="px-4 py-2 rounded-xl text-sm font-semibold transition-colors {activeTab === tab.key ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-300'}" on:click={() => activeTab = tab.key}>
        {tab.label}
      </button>
    {/each}
  </div>
  {#if loading}
    <div class="text-gray-400">Загрузка...</div>
  {:else if error}
    <div class="text-red-400">{error}</div>
  {:else}
    <div class="space-y-4">
      {#if filteredThreads().length}
        {#each filteredThreads() as thread}
          <div class="rounded-xl border border-gray-800 bg-gray-950 p-4 cursor-pointer hover:bg-gray-900 transition" on:click={() => openThread(thread)}>
            <div class="flex items-center justify-between">
              <div class="text-sm font-semibold text-white">{thread.subject}</div>
              <div class="text-xs text-gray-500">{thread.category}</div>
            </div>
            <div class="mt-2 text-xs text-gray-400">{thread.snippet}</div>
            <div class="mt-1 text-xs text-gray-500">{thread.lastMessageAt ? new Date(thread.lastMessageAt).toLocaleString('ru-RU') : '—'}</div>
          </div>
        {/each}
      {:else}
        <div class="text-gray-500">Нет писем в этой категории.</div>
      {/if}
    </div>

    {#if selectedThread}
      <div class="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
        <div class="bg-gray-950 rounded-xl shadow-xl max-w-2xl w-full p-6 relative">
          <button class="absolute top-2 right-2 text-gray-400 hover:text-white" on:click={closeThread}>&times;</button>
          <div class="mb-2 text-lg font-bold text-white">{selectedThread.subject}</div>
          <div class="mb-1 text-xs text-gray-400">От: {selectedThread.sender}</div>
          <div class="mb-1 text-xs text-gray-400">Кому: {selectedThread.recipients}</div>
          {#if selectedThread.cc}
            <div class="mb-1 text-xs text-gray-400">Копия: {selectedThread.cc}</div>
          {/if}
          <div class="mb-1 text-xs text-gray-400">Дата: {selectedThread.sent_at ? new Date(selectedThread.sent_at).toLocaleString('ru-RU') : '—'}</div>
          <div class="my-4 whitespace-pre-line text-sm text-gray-200">{selectedThread.body}</div>
          {#if selectedThread.attachments && selectedThread.attachments.length}
            <div class="mt-4">
              <div class="font-semibold text-gray-300 mb-2">Вложения:</div>
              <ul class="list-disc ml-6">
                {#each selectedThread.attachments as att}
                  <li><a class="text-indigo-400 hover:underline" href={att.url} target="_blank">{att.filename}</a></li>
                {/each}
              </ul>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  <script>
  let selectedThread = $state(null);
  function openThread(thread) {
    selectedThread = thread;
  }
  function closeThread() {
    selectedThread = null;
  }
  </script>
  {/if}
</div>
