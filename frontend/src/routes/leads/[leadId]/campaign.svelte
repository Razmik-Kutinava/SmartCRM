<script>
import { onMount } from 'svelte';
import { createCampaign } from '$lib/emailStorage.js';
import { goto } from '$app/navigation';

export let params;
let leadId = params.leadId;
let subject = $state('');
let body = $state('');
let loading = $state(false);
let error = $state('');
let success = $state('');

async function sendCampaign() {
  loading = true;
  error = '';
  success = '';
  try {
    const result = await createCampaign({
      account_id: null, // можно выбрать позже
      name: `Кампания для лида ${leadId}`,
      subject,
      body,
      lead_ids: [parseInt(leadId)],
      send_now: true,
    });
    success = 'Кампания отправлена!';
    setTimeout(() => goto('/email'), 1500);
  } catch (e) {
    error = e.message;
  } finally {
    loading = false;
  }
}
</script>

<div class="p-6 max-w-xl mx-auto">
  <h1 class="text-2xl font-semibold text-white mb-4">Массовая рассылка для лида #{leadId}</h1>
  <div class="space-y-4">
    <input bind:value={subject} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" placeholder="Тема письма" />
    <textarea bind:value={body} class="w-full h-32 rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" placeholder="Текст письма" />
    <button on:click={sendCampaign} disabled={loading} class="w-full rounded-2xl bg-green-600 px-4 py-3 text-sm font-semibold text-white hover:bg-green-500 transition-colors disabled:bg-gray-600">
      {loading ? 'Отправка...' : 'Отправить кампанию'}
    </button>
    {#if error}
      <div class="text-red-400">{error}</div>
    {/if}
    {#if success}
      <div class="text-green-400">{success}</div>
    {/if}
  </div>
</div>
