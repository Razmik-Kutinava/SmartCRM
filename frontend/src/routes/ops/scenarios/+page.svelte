<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => goto('/ops/intents/scenarios', { replaceState: true }));
</script>

<div class="px-6 py-12 text-center text-sm text-gray-500">
	Переход к сценариям…
</div>
