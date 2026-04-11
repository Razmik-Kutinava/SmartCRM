<script>
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { page } from '$app/stores';
	import { enrichLeadForCard, getLeadById } from '$lib/leadsStorage.js';

	let lead = $state(null);
	let notFound = $state(false);

	function sync() {
		const id = get(page).params.id;
		const raw = getLeadById(id);
		lead = raw ? enrichLeadForCard(raw) : null;
		notFound = !raw;
	}

	onMount(() => {
		sync();
		return page.subscribe(() => sync());
	});

	let activeTab = $state('overview');
	let noteText = $state('');

	const activityHistory = $derived(lead?.history ?? []);
	const leadTasks = $derived(lead?.tasks ?? []);
</script>

{#if notFound}
	<div class="flex flex-col items-center justify-center flex-1 p-8 text-center">
		<p class="text-lg text-white mb-2">Лид не найден</p>
		<p class="text-sm text-gray-500 mb-6">Возможно, он удалён или ссылка устарела.</p>
		<a href="/leads" class="text-indigo-400 hover:text-indigo-300 text-sm">← К списку лидов</a>
	</div>
{:else if lead}
	<!-- Header -->
	<div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900 shrink-0">
		<div class="flex items-center gap-3">
			<a href="/leads" class="text-gray-500 hover:text-white transition-colors text-sm">← Лиды</a>
			<span class="text-gray-700">/</span>
			<span class="text-sm text-white font-medium">{lead.company}</span>
		</div>
		<div class="flex items-center gap-2">
			<button class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">🔍 Исследовать</button>
			<button class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">✉️ Написать</button>
			<button class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">📊 Анализ</button>
			<button class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors">🎙 Голос</button>
		</div>
	</div>

	<div class="flex-1 overflow-hidden flex">
		<!-- Left: Lead info -->
		<div class="w-80 border-r border-gray-800 overflow-y-auto bg-gray-900 shrink-0">
			<div class="p-5 space-y-5">
				<div>
					<div class="text-lg font-bold text-white">{lead.company}</div>
					<div class="text-sm text-gray-400 mt-0.5">{lead.contact} · {lead.position}</div>
					<div class="flex items-center gap-2 mt-2">
						<span class="px-2 py-0.5 bg-blue-900 text-blue-300 text-xs rounded-full font-medium">{lead.stage}</span>
						<span class="text-green-400 font-bold text-sm">{lead.score}/100</span>
					</div>
				</div>

				<div class="space-y-2">
					<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Контакты</div>
					<div class="space-y-1.5 text-sm">
						<div class="flex items-center gap-2 text-gray-300">
							<span class="text-gray-600 w-4">✉</span> {lead.email}
						</div>
						<div class="flex items-center gap-2 text-gray-300">
							<span class="text-gray-600 w-4">✆</span> {lead.phone}
						</div>
						<div class="flex items-center gap-2 text-gray-300">
							<span class="text-gray-600 w-4">🌐</span> {lead.website}
						</div>
					</div>
				</div>

				<div class="space-y-2">
					<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Детали</div>
					<div class="space-y-2 text-sm">
						{#each [
							['Отрасль', lead.industry],
							['Сотрудники', lead.employees],
							['Город', lead.city],
							['Источник', lead.source],
							['Бюджет', lead.budget],
							['Ответственный', lead.responsible],
							['Создан', lead.created],
							['Следующий звонок', lead.nextCall],
						] as [label, value]}
							<div class="flex justify-between">
								<span class="text-gray-500">{label}</span>
								<span class="text-gray-300">{value}</span>
							</div>
						{/each}
					</div>
				</div>

				{#if lead.description}
					<div class="space-y-1.5">
						<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Описание</div>
						<p class="text-sm text-gray-300 leading-relaxed">{lead.description}</p>
					</div>
				{/if}

				<div class="space-y-2">
					<div class="text-xs text-gray-500 uppercase tracking-wide font-medium">Сменить этап</div>
					<div class="grid grid-cols-2 gap-1">
						{#each ['Новый', 'Квалифицирован', 'КП отправлено', 'Переговоры', 'Выигран', 'Проигран'] as stage}
							<button class="px-2 py-1 text-xs rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors text-left">
								{stage}
							</button>
						{/each}
					</div>
				</div>
			</div>
		</div>

		<!-- Right: Activity -->
		<div class="flex-1 flex flex-col overflow-hidden">
			<div class="flex gap-4 px-6 pt-4 border-b border-gray-800 shrink-0">
				{#each [['overview', 'Обзор'], ['tasks', 'Задачи'], ['emails', 'Письма'], ['agents', 'Агенты']] as [id, label]}
					<button
						onclick={() => (activeTab = id)}
						class="pb-3 text-sm transition-colors border-b-2 {activeTab === id
							? 'text-white border-indigo-500'
							: 'text-gray-500 border-transparent hover:text-gray-300'}"
					>
						{label}
					</button>
				{/each}
			</div>

			<div class="flex-1 overflow-y-auto p-6">
				{#if activeTab === 'overview'}
					<div class="mb-5">
						<textarea
							bind:value={noteText}
							placeholder="Добавить заметку или команду агентам..."
							class="w-full bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-lg px-4 py-3 placeholder-gray-600 focus:outline-none focus:border-indigo-500 resize-none h-20"
						></textarea>
						<div class="flex gap-2 mt-2">
							<button class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors">Добавить заметку</button>
							<button class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors">Поручить агенту</button>
						</div>
					</div>

					<div class="space-y-3">
						{#each activityHistory as item}
							<div class="flex gap-3">
								<div
									class="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5
									{item.type === 'agent' ? 'bg-indigo-900 text-indigo-300' : 'bg-gray-800 text-gray-400'} text-xs"
								>
									{item.type === 'call' ? '✆' : item.type === 'agent' ? '⬡' : '✎'}
								</div>
								<div class="flex-1">
									<div class="flex items-center gap-2 mb-0.5">
										<span class="text-xs font-medium {item.type === 'agent' ? 'text-indigo-400' : 'text-gray-400'}">{item.author}</span>
										<span class="text-xs text-gray-600">{item.date}</span>
									</div>
									<p class="text-sm text-gray-300">{item.text}</p>
								</div>
							</div>
						{/each}
					</div>
				{:else if activeTab === 'tasks'}
					<div class="space-y-2">
						{#each leadTasks as task}
							<div class="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
								<div
									class="w-4 h-4 rounded border {task.status === 'done' ? 'bg-green-500 border-green-500' : 'border-gray-600'} flex items-center justify-center shrink-0"
								>
									{#if task.status === 'done'}<span class="text-white text-xs">✓</span>{/if}
								</div>
								<div class="flex-1">
									<div class="text-sm {task.status === 'done' ? 'line-through text-gray-500' : 'text-gray-200'}">{task.title}</div>
									<div class="text-xs text-gray-600">{task.due}</div>
								</div>
							</div>
						{/each}
						<button class="w-full p-3 border border-dashed border-gray-700 rounded-lg text-sm text-gray-500 hover:text-gray-300 hover:border-gray-500 transition-colors">
							+ Добавить задачу
						</button>
					</div>
				{:else if activeTab === 'agents'}
					<div class="space-y-3">
						<div class="text-sm text-gray-400 mb-4">Поручи задачу агентам SmartCRM</div>
						{#each [
							{ agent: 'Маркетолог', desc: 'Исследовать клиента и написать персональное письмо', icon: '✉️' },
							{ agent: 'Аналитик', desc: 'Пересчитать скоринг и дать рекомендации', icon: '📊' },
							{ agent: 'Стратег', desc: 'Дать совет как лучше закрыть эту сделку', icon: '🧠' },
							{ agent: 'Экономист', desc: 'Рассчитать ROI для клиента и подготовить обоснование', icon: '💰' },
							{ agent: 'Тех. спец', desc: 'Подготовить техническое описание под нужды клиента', icon: '⚙️' },
						] as item}
							<div class="flex items-center gap-3 p-4 bg-gray-900 border border-gray-800 hover:border-indigo-800 rounded-lg transition-colors cursor-pointer">
								<span class="text-xl">{item.icon}</span>
								<div class="flex-1">
									<div class="text-sm font-medium text-white">{item.agent}</div>
									<div class="text-xs text-gray-500">{item.desc}</div>
								</div>
								<button class="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-xs text-white rounded-lg transition-colors">Запустить</button>
							</div>
						{/each}
					</div>
				{:else if activeTab === 'emails'}
					<div class="text-center py-12 text-gray-600">
						<div class="text-3xl mb-3">✉️</div>
						<div class="text-sm">Писем пока нет</div>
						<button class="mt-3 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-sm text-white rounded-lg transition-colors">
							Написать письмо с маркетологом
						</button>
					</div>
				{/if}
			</div>
		</div>
	</div>
{:else}
	<div class="flex flex-col items-center justify-center flex-1 p-8 text-gray-500 text-sm">Загрузка…</div>
{/if}
