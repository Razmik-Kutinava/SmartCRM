<script>
	import { onMount } from 'svelte';

	let minutes = $state(25);
	let seconds = $state(0);
	let running = $state(false);
	let interval = null;

	function tick() {
		if (seconds === 0) {
			if (minutes === 0) {
				stop();
				if (typeof Audio !== 'undefined') {
					try {
						const ctx = new AudioContext();
						const o = ctx.createOscillator();
						const g = ctx.createGain();
						o.connect(g);
						g.connect(ctx.destination);
						o.frequency.value = 880;
						g.gain.value = 0.08;
						o.start();
						setTimeout(() => o.stop(), 200);
					} catch {
						/* ignore */
					}
				}
				return;
			}
			minutes -= 1;
			seconds = 59;
		} else {
			seconds -= 1;
		}
	}

	function start() {
		if (running) return;
		running = true;
		interval = setInterval(tick, 1000);
	}

	function stop() {
		running = false;
		if (interval) clearInterval(interval);
		interval = null;
	}

	function reset() {
		stop();
		minutes = 25;
		seconds = 0;
	}

	function pad(n) {
		return String(n).padStart(2, '0');
	}

	onMount(() => {
		return () => {
			if (interval) clearInterval(interval);
		};
	});
</script>

<div class="flex flex-col flex-1 min-h-0 overflow-hidden">
	<div class="px-6 py-3 border-b border-gray-800 bg-gray-900 shrink-0">
		<h1 class="text-lg font-semibold text-white">Фокус (помидорка)</h1>
		<p class="text-xs text-gray-500">25 минут работы — можно сменить таймер перед стартом</p>
	</div>
	<div class="flex-1 flex flex-col items-center justify-center p-8 gap-6">
		<div class="text-6xl sm:text-7xl font-mono font-bold text-white tabular-nums">
			{pad(minutes)}:{pad(seconds)}
		</div>
		<div class="flex gap-2">
			<button
				type="button"
				disabled={running}
				onclick={() => {
					minutes = 25;
					seconds = 0;
				}}
				class="px-3 py-1.5 rounded-lg bg-gray-800 text-sm text-gray-300 disabled:opacity-40"
			>
				25
			</button>
			<button
				type="button"
				disabled={running}
				onclick={() => {
					minutes = 45;
					seconds = 0;
				}}
				class="px-3 py-1.5 rounded-lg bg-gray-800 text-sm text-gray-300 disabled:opacity-40"
			>
				45
			</button>
			<button
				type="button"
				disabled={running}
				onclick={() => {
					minutes = 5;
					seconds = 0;
				}}
				class="px-3 py-1.5 rounded-lg bg-gray-800 text-sm text-gray-300 disabled:opacity-40"
			>
				5
			</button>
		</div>
		<div class="flex gap-3">
			{#if !running}
				<button
					type="button"
					onclick={start}
					class="px-6 py-2 rounded-xl bg-indigo-600 text-white text-sm font-medium"
				>
					Старт
				</button>
			{:else}
				<button
					type="button"
					onclick={stop}
					class="px-6 py-2 rounded-xl bg-red-800 text-white text-sm font-medium"
				>
					Пауза
				</button>
			{/if}
			<button type="button" onclick={reset} class="px-6 py-2 rounded-xl bg-gray-800 text-gray-300 text-sm">
				Сброс
			</button>
		</div>
	</div>
</div>
