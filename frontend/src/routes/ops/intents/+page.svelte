<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	onMount(() => goto('/ops/intents/traces', { replaceState: true }));
</script>
