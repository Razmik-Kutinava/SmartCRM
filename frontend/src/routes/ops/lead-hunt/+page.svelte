<script>
	import LeadHuntOperatorPanel from '$lib/leadHunt/LeadHuntOperatorPanel.svelte';
</script>

<div class="max-w-4xl mx-auto p-6 space-y-4">
	<h1 class="text-2xl font-bold text-white">Авто-охота (Lead Hunt)</h1>
	<p class="text-gray-400 text-sm">
		ICP из выигранных → поиск агентами → очередь → CRM.
		<a href="/ops/queue" class="text-indigo-400 underline">Очередь Ops</a>
		·
		<a href="/leadgen" class="text-indigo-400 underline">Лидоген</a>
	</p>
	<LeadHuntOperatorPanel theme="leadgen" />
</div>
