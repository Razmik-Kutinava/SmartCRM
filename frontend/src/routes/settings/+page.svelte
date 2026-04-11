<script>
	let groqKey = $state('gsk_••••••••••••••••');
	let ollamaHost = $state('http://localhost:11434');
	let ollamaModel = $state('qwen2.5:14b');
	let hermesModel = $state('hermes3:latest');
	let braveKey = $state('••••••••••••••••');
	let tavilyKey = $state('••••••••••••••••');
	let serperKey = $state('••••••••••••••••');
</script>

<div class="px-6 py-4 border-b border-gray-800 bg-gray-900 shrink-0">
	<h1 class="text-lg font-semibold text-white">Настройки</h1>
</div>

<div class="flex-1 overflow-y-auto p-6">
	<div class="max-w-xl space-y-6">

		<div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
			<div class="text-sm font-medium text-white">LLM</div>
			{#each [
				['Groq API Key', groqKey, 'gsk_...'],
				['Ollama Host', ollamaHost, 'http://localhost:11434'],
				['Ollama Model', ollamaModel, 'qwen2.5:14b'],
				['Hermes Model', hermesModel, 'hermes3:latest'],
			] as [label, val, placeholder]}
				<div>
					<label class="text-xs text-gray-500 block mb-1">{label}</label>
					<input value={val} placeholder={placeholder} class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500" />
				</div>
			{/each}
		</div>

		<div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
			<div class="text-sm font-medium text-white">Поисковики</div>
			{#each [['Brave Search API Key', braveKey], ['Tavily API Key', tavilyKey], ['Serper API Key', serperKey]] as [label, val]}
				<div>
					<label class="text-xs text-gray-500 block mb-1">{label}</label>
					<input value={val} class="w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500" />
				</div>
			{/each}
		</div>

		<button class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors">Сохранить настройки</button>

	</div>
</div>
