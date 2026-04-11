<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	onMount(() => goto('/ops/intents/eval', { replaceState: true }));
</script>
