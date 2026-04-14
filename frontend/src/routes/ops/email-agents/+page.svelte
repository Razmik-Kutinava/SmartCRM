<script>
    import { onMount } from 'svelte';

    const AGENTS = [
        { key: 'all',        label: 'Все агенты' },
        { key: 'marketer',   label: 'Маркетолог' },
        { key: 'analyst',    label: 'Аналитик'   },
        { key: 'strategist', label: 'Стратег'    },
        { key: 'economist',  label: 'Экономист'  },
    ];

    // ─── данные ───────────────────────────────────────────────────
    let intents = $state([]);
    let loading = $state(true);
    let error   = $state('');
    let success = $state('');

    // ─── форма создания ──────────────────────────────────────────
    let showForm       = $state(false);
    let formAgent      = $state('marketer');
    let formIntentName = $state('');
    let formKeywords   = $state('');
    let formAction     = $state('');
    let formPriority   = $state(0);
    let formSaving     = $state(false);

    // ─── редактирование ──────────────────────────────────────────
    let editId   = $state(null);

    // ─── тест ────────────────────────────────────────────────────
    let testLeadId  = $state('');
    let testAgent   = $state('marketer');
    let testTask    = $state('');
    let testLoading = $state(false);
    let testResult  = $state(null);
    let testError   = $state('');

    // ─── загрузка ────────────────────────────────────────────────
    async function load() {
        loading = true;
        try {
            const r = await fetch('/api/agents/email-intents');
            if (!r.ok) throw new Error(await r.text());
            intents = await r.json();
        } catch (e) { error = e.message; }
        finally { loading = false; }
    }
    onMount(() => { load(); loadStats(); loadFewShots(); });

    // ─── группировка по агенту ───────────────────────────────────
    function grouped() {
        const map = new Map();
        for (const agent of AGENTS) map.set(agent.key, []);
        for (const i of intents) {
            if (map.has(i.agentName)) map.get(i.agentName).push(i);
        }
        return map;
    }

    // ─── создать / обновить ──────────────────────────────────────
    function openCreate() {
        editId = null; formAgent = 'marketer'; formIntentName = '';
        formKeywords = ''; formAction = ''; formPriority = 0;
        showForm = true;
    }

    function openEdit(intent) {
        editId         = intent.id;
        formAgent      = intent.agentName;
        formIntentName = intent.intentName;
        formKeywords   = intent.triggerKeywords;
        formAction     = intent.actionTemplate;
        formPriority   = intent.priority;
        showForm       = true;
    }

    async function saveIntent() {
        if (!formIntentName || !formAction) { error = 'Заполни название и действие'; return; }
        formSaving = true; error = ''; success = '';
        try {
            const body = {
                agent_name:       formAgent,
                intent_name:      formIntentName,
                trigger_keywords: formKeywords,
                action_template:  formAction,
                priority:         Number(formPriority),
                is_active:        true,
            };
            const url    = editId ? `/api/agents/email-intents/${editId}` : '/api/agents/email-intents';
            const method = editId ? 'PUT' : 'POST';
            const r = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            if (!r.ok) throw new Error(await r.text());
            success = editId ? 'Интент обновлён' : 'Интент создан';
            showForm = false;
            await load();
        } catch (e) { error = '❌ ' + e.message; }
        finally { formSaving = false; }
    }

    async function toggleActive(intent) {
        try {
            await fetch(`/api/agents/email-intents/${intent.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !intent.isActive }),
            });
            await load();
        } catch (e) { error = e.message; }
    }

    async function deleteIntent(id) {
        if (!confirm('Удалить этот интент?')) return;
        try {
            await fetch(`/api/agents/email-intents/${id}`, { method: 'DELETE' });
            await load();
        } catch (e) { error = e.message; }
    }

    // ─── статистика feedback ─────────────────────────────────────
    let stats        = $state({});
    let statsLoading = $state(false);

    async function loadStats() {
        statsLoading = true;
        try {
            const r = await fetch('/api/agents/email/stats');
            if (r.ok) stats = await r.json();
        } catch {}
        finally { statsLoading = false; }
    }

    // ─── few-shot примеры ─────────────────────────────────────────
    let fewShots        = $state([]);
    let fewShotsLoading = $state(false);

    async function loadFewShots() {
        fewShotsLoading = true;
        try {
            const r = await fetch('/api/agents/email/few-shots');
            if (r.ok) fewShots = await r.json();
        } catch {}
        finally { fewShotsLoading = false; }
    }

    async function removeFewShot(runId) {
        if (!confirm('Убрать этот пример из few-shot?')) return;
        try {
            await fetch(`/api/agents/email/few-shots/${runId}`, { method: 'DELETE' });
            await loadFewShots();
            await loadStats();
        } catch (e) { error = e.message; }
    }

    // ─── тест агента ─────────────────────────────────────────────
    async function runTest() {
        if (!testLeadId) { testError = 'Введи ID лида'; return; }
        testLoading = true; testResult = null; testError = '';
        try {
            const r = await fetch('/api/agents/email/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lead_id: Number(testLeadId), agent: testAgent, task: testTask }),
            });
            if (!r.ok) throw new Error(await r.text());
            testResult = await r.json();
        } catch (e) { testError = '❌ ' + e.message; }
        finally { testLoading = false; }
    }

    // сохранить feedback из тест-панели
    async function saveTestFeedback(fb) {
        if (!testResult?.run_id) return;
        try {
            await fetch('/api/agents/email/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ run_id: testResult.run_id, feedback: fb }),
            });
            success = fb === 'good' ? '👍 Сохранено как хороший пример' : '👎 Отмечено';
            await loadStats();
            await loadFewShots();
        } catch (e) { error = e.message; }
    }

    // дефолтные интенты для быстрого заполнения
    const DEFAULTS = [
        { agent: 'marketer',   name: 'Клиент молчит 7+ дней',       keys: 'молч,тишина,не отвеч',  action: 'Напомни о себе мягко. Предложи что-то полезное, не продавай в лоб.' },
        { agent: 'marketer',   name: 'Клиент спрашивает цену',       keys: 'цена,стоимость,сколько', action: 'Предложи отправить коммерческое предложение. Уточни объём и сроки.' },
        { agent: 'marketer',   name: 'Клиент просит demo',           keys: 'demo,демо,показать',     action: 'Назначь демо-звонок. Предложи 3 слота времени.' },
        { agent: 'marketer',   name: 'Клиент возражает по цене',     keys: 'дорого,не вписыва,бюджет', action: 'Переведи разговор на ROI и ценность, а не на цену. Предложи пилот.' },
        { agent: 'strategist', name: 'Клиент не принимает решение',  keys: 'думаем,посовещаем,позже', action: 'Определи ЛПР. Предложи помочь с внутренней презентацией для руководства.' },
        { agent: 'analyst',    name: 'Новое письмо от клиента',      keys: '',                        action: 'Проанализируй тональность и определи следующий шаг.' },
    ];

    async function addDefault(d) {
        try {
            await fetch('/api/agents/email-intents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_name: d.agent, intent_name: d.name, trigger_keywords: d.keys, action_template: d.action, priority: 0, is_active: true }),
            });
            await load();
        } catch (e) { error = e.message; }
    }
</script>

<div class="p-6 space-y-6">

    <!-- шапка -->
    <div class="flex items-center justify-between">
        <div>
            <h2 class="text-lg font-semibold text-white">📧 Агенты на почте</h2>
            <p class="text-xs text-gray-500 mt-0.5">Настрой правила — агенты сами знают как вести себя в каждой ситуации</p>
        </div>
        <button onclick={() => openCreate()}
            class="px-4 py-2 rounded-xl bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors">
            + Добавить правило
        </button>
    </div>

    {#if error}   <div class="px-4 py-3 rounded-xl bg-red-950 border border-red-800 text-red-200 text-sm">{error}</div>   {/if}
    {#if success} <div class="px-4 py-3 rounded-xl bg-green-950 border border-green-800 text-green-200 text-sm">{success}</div> {/if}

    <!-- быстрое добавление дефолтных -->
    {#if intents.length === 0 && !loading}
        <div class="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <p class="text-sm text-gray-400 mb-3">Быстрый старт — добавь готовые правила:</p>
            <div class="flex flex-wrap gap-2">
                {#each DEFAULTS as d}
                    <button onclick={() => addDefault(d)}
                        class="px-3 py-1.5 rounded-lg bg-gray-800 text-xs text-gray-300 hover:bg-gray-700 hover:text-white transition-colors border border-gray-700">
                        + {d.name}
                    </button>
                {/each}
            </div>
        </div>
    {/if}

    <!-- таблица интентов по агентам -->
    {#if loading}
        <div class="text-gray-500 text-sm">Загрузка...</div>
    {:else}
        {#each AGENTS as agent}
            {@const agentIntents = grouped().get(agent.key) ?? []}
            {#if agentIntents.length > 0}
                <div class="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
                    <div class="px-5 py-3 border-b border-gray-800 flex items-center justify-between">
                        <span class="text-sm font-semibold text-white">{agent.label}</span>
                        <span class="text-xs text-gray-500">{agentIntents.length} правил</span>
                    </div>
                    <div class="divide-y divide-gray-800/50">
                        {#each agentIntents as intent (intent.id)}
                            <div class="px-5 py-3 flex items-start gap-4 {intent.isActive ? '' : 'opacity-40'}">
                                <!-- toggle -->
                                <button onclick={() => toggleActive(intent)}
                                    class="mt-0.5 flex-shrink-0 w-8 h-4 rounded-full transition-colors relative {intent.isActive ? 'bg-indigo-600' : 'bg-gray-700'}">
                                    <span class="absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all {intent.isActive ? 'left-4' : 'left-0.5'}"></span>
                                </button>

                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-2">
                                        <span class="text-sm font-medium text-white">{intent.intentName}</span>
                                        {#if intent.priority > 0}
                                            <span class="text-xs px-1.5 py-0.5 rounded bg-indigo-900 text-indigo-300">p{intent.priority}</span>
                                        {/if}
                                    </div>
                                    {#if intent.triggerKeywords}
                                        <div class="text-xs text-gray-500 mt-0.5">Триггеры: {intent.triggerKeywords}</div>
                                    {/if}
                                    <div class="text-xs text-gray-400 mt-1 leading-relaxed">{intent.actionTemplate}</div>
                                </div>

                                <div class="flex items-center gap-2 flex-shrink-0">
                                    <button onclick={() => openEdit(intent)}
                                        class="text-xs text-gray-500 hover:text-white transition-colors px-2 py-1 rounded hover:bg-gray-800">
                                        ✏
                                    </button>
                                    <button onclick={() => deleteIntent(intent.id)}
                                        class="text-xs text-gray-500 hover:text-red-400 transition-colors px-2 py-1 rounded hover:bg-gray-800">
                                        ✕
                                    </button>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        {/each}

        {#if intents.length === 0}
            <p class="text-gray-500 text-sm">Правил пока нет. Добавь первое или используй быстрый старт.</p>
        {/if}
    {/if}

    <!-- ═══ СТАТИСТИКА FEEDBACK ════════════════════════════════════ -->
    <div class="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        <div class="px-5 py-3 border-b border-gray-800 flex items-center justify-between">
            <span class="text-sm font-semibold text-white">📊 Качество агентов (feedback)</span>
            <button onclick={loadStats} class="text-xs text-gray-500 hover:text-white transition-colors">↻ Обновить</button>
        </div>
        {#if statsLoading}
            <div class="px-5 py-4 text-xs text-gray-500">Загрузка...</div>
        {:else if Object.keys(stats).length === 0}
            <div class="px-5 py-4 text-xs text-gray-500">Пока нет данных. Запусти агента и поставь оценку 👍/👎.</div>
        {:else}
            <div class="divide-y divide-gray-800/50">
                {#each Object.entries(stats) as [agentName, s]}
                    {@const pct = s.total > 0 ? Math.round(s.good / s.total * 100) : 0}
                    <div class="px-5 py-3 flex items-center gap-4">
                        <div class="w-28 text-sm text-white font-medium capitalize">{agentName}</div>
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-1">
                                <div class="flex-1 h-1.5 rounded-full bg-gray-800 overflow-hidden">
                                    <div class="h-full rounded-full bg-green-500 transition-all" style="width:{pct}%"></div>
                                </div>
                                <span class="text-xs text-gray-400 w-8 text-right">{pct}%</span>
                            </div>
                            <div class="flex gap-4 text-xs text-gray-500">
                                <span class="text-green-400">👍 {s.good}</span>
                                <span class="text-red-400">👎 {s.bad}</span>
                                <span class="text-gray-500">Всего: {s.total}</span>
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    </div>

    <!-- ═══ FEW-SHOT ПРИМЕРЫ ═══════════════════════════════════════ -->
    <div class="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        <div class="px-5 py-3 border-b border-gray-800 flex items-center justify-between">
            <div>
                <span class="text-sm font-semibold text-white">🌟 Few-shot примеры</span>
                <span class="ml-2 text-xs text-gray-500">Инжектируются в промпт агента при каждом запуске</span>
            </div>
            <button onclick={loadFewShots} class="text-xs text-gray-500 hover:text-white transition-colors">↻ Обновить</button>
        </div>
        {#if fewShotsLoading}
            <div class="px-5 py-4 text-xs text-gray-500">Загрузка...</div>
        {:else if fewShots.length === 0}
            <div class="px-5 py-4 text-xs text-gray-500">
                Few-shot примеров нет. Запусти агента на лиде → поставь 👍 → пример автоматически попадёт сюда.
            </div>
        {:else}
            <div class="divide-y divide-gray-800/50">
                {#each fewShots as shot (shot.id)}
                    <div class="px-5 py-4 flex items-start gap-4">
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 mb-1">
                                <span class="text-xs px-2 py-0.5 rounded bg-indigo-900/60 text-indigo-300 capitalize">{shot.agentName}</span>
                                <span class="text-xs text-gray-500">#{shot.id} · Лид #{shot.leadId} · {shot.created}</span>
                            </div>
                            {#if shot.task}
                                <div class="text-xs text-gray-400 mb-1">Задача: <span class="text-gray-200">{shot.task}</span></div>
                            {/if}
                            {#if shot.emailSubject}
                                <div class="text-xs font-medium text-white mb-0.5">✉ {shot.emailSubject}</div>
                                <div class="text-xs text-gray-400 leading-relaxed line-clamp-3">{shot.emailBody}</div>
                            {:else if shot.summary}
                                <div class="text-xs text-gray-400 leading-relaxed line-clamp-3">{shot.summary}</div>
                            {/if}
                        </div>
                        <button onclick={() => removeFewShot(shot.id)}
                            class="flex-shrink-0 text-xs text-gray-600 hover:text-red-400 transition-colors px-2 py-1 rounded hover:bg-gray-800"
                            title="Убрать из few-shot">
                            ✕
                        </button>
                    </div>
                {/each}
            </div>
        {/if}
    </div>

    <!-- панель теста агента -->
    <div class="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
        <div class="text-sm font-semibold text-white">🧪 Тест агента на лиде</div>
        <p class="text-xs text-gray-500">Укажи ID лида → агент прочитает переписку + применит правила → покажет результат</p>

        <div class="grid grid-cols-3 gap-3">
            <div>
                <label class="text-xs text-gray-500 block mb-1">ID лида</label>
                <input bind:value={testLeadId} type="number" class="w-full rounded-xl bg-gray-950 border border-gray-700 px-4 py-2.5 text-sm text-white" placeholder="Напр. 16" />
            </div>
            <div>
                <label class="text-xs text-gray-500 block mb-1">Агент</label>
                <select bind:value={testAgent} class="w-full rounded-xl bg-gray-950 border border-gray-700 px-4 py-2.5 text-sm text-white">
                    {#each AGENTS.filter(a => a.key !== 'all') as a}
                        <option value={a.key}>{a.label}</option>
                    {/each}
                </select>
            </div>
            <div>
                <label class="text-xs text-gray-500 block mb-1">Задача (опционально)</label>
                <input bind:value={testTask} class="w-full rounded-xl bg-gray-950 border border-gray-700 px-4 py-2.5 text-sm text-white" placeholder="Напр. 'что предложить следующим'" />
            </div>
        </div>

        <button onclick={runTest} disabled={testLoading}
            class="px-6 py-2.5 rounded-xl bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-700 transition-colors">
            {testLoading ? '⟳ Запускаю...' : '▶ Запустить агента'}
        </button>

        {#if testError}
            <div class="text-red-400 text-sm">{testError}</div>
        {/if}

        {#if testResult}
            <div class="space-y-3">
                <div class="text-xs text-gray-500">
                    Агент: <span class="text-white">{testResult.agent}</span> ·
                    Тредов прочитано: <span class="text-white">{testResult.threads_analyzed}</span> ·
                    Правил применено: <span class="text-white">{testResult.intents_applied}</span>
                </div>

                {#if testResult.result?.first_email}
                    <div class="bg-gray-950 border border-indigo-800/50 rounded-xl p-4">
                        <div class="text-xs text-indigo-400 font-semibold mb-2">✉ Черновик письма</div>
                        <div class="text-xs text-gray-500 mb-1">Тема: <span class="text-white">{testResult.result.first_email.subject}</span></div>
                        <div class="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed mt-2">{testResult.result.first_email.body}</div>
                    </div>
                {/if}

                {#if testResult.result?.value_hook}
                    <div class="bg-gray-950 border border-gray-800 rounded-xl p-4 text-sm text-gray-300">
                        <span class="text-xs text-gray-500 block mb-1">💡 Крючок внимания</span>
                        {testResult.result.value_hook}
                    </div>
                {/if}

                {#if testResult.result?.summary}
                    <div class="text-xs text-gray-400 italic">{testResult.result.summary}</div>
                {/if}

                {#if testResult.result?.touch_sequence?.length}
                    <div class="bg-gray-950 border border-gray-800 rounded-xl p-4">
                        <div class="text-xs text-gray-500 mb-2">📅 План касаний</div>
                        <div class="space-y-1">
                            {#each testResult.result.touch_sequence as t}
                                <div class="text-xs text-gray-300">
                                    <span class="text-indigo-400">День {t.day}</span>
                                    · <span class="text-gray-500">{t.channel}</span>
                                    · {t.action}
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}

                <!-- feedback прямо из тест-панели -->
                <div class="flex items-center gap-3 pt-1">
                    <span class="text-xs text-gray-500">Оцени результат:</span>
                    <button onclick={() => saveTestFeedback('good')}
                        class="px-3 py-1.5 rounded-lg text-xs font-medium bg-green-900/40 text-green-300 hover:bg-green-800/60 border border-green-800/50 transition-colors">
                        👍 Хорошо → в few-shot
                    </button>
                    <button onclick={() => saveTestFeedback('bad')}
                        class="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-900/30 text-red-400 hover:bg-red-900/50 border border-red-800/40 transition-colors">
                        👎 Плохо
                    </button>
                </div>
            </div>
        {/if}
    </div>
</div>

<!-- ═══ МОДАЛ: форма интента ═══════════════════════════════════ -->
{#if showForm}
    <button class="fixed inset-0 bg-black/70 z-40 cursor-default" onclick={() => showForm = false} aria-label="Закрыть"></button>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div class="bg-gray-950 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-lg pointer-events-auto">
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
                <h3 class="text-sm font-semibold text-white">{editId ? 'Редактировать правило' : 'Новое правило'}</h3>
                <button onclick={() => showForm = false} class="text-gray-500 hover:text-white text-xl">&times;</button>
            </div>
            <div class="px-6 py-4 space-y-3">
                <div>
                    <label class="text-xs text-gray-500 block mb-1">Агент</label>
                    <select bind:value={formAgent} class="w-full rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white">
                        {#each AGENTS as a}<option value={a.key}>{a.label}</option>{/each}
                    </select>
                </div>
                <div>
                    <label class="text-xs text-gray-500 block mb-1">Название ситуации</label>
                    <input bind:value={formIntentName} class="w-full rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white" placeholder="Клиент молчит 7 дней" />
                </div>
                <div>
                    <label class="text-xs text-gray-500 block mb-1">Ключевые слова-триггеры <span class="text-gray-600">(через запятую, опционально)</span></label>
                    <input bind:value={formKeywords} class="w-full rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white" placeholder="молч, тишина, не отвечает" />
                </div>
                <div>
                    <label class="text-xs text-gray-500 block mb-1">Что делать агенту</label>
                    <textarea bind:value={formAction} class="w-full h-24 rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white resize-none" placeholder="Напомни о себе мягко. Предложи ценность, не продавай в лоб."></textarea>
                </div>
                <div>
                    <label class="text-xs text-gray-500 block mb-1">Приоритет <span class="text-gray-600">(выше = важнее)</span></label>
                    <input type="number" bind:value={formPriority} class="w-32 rounded-xl bg-gray-900 border border-gray-700 px-4 py-2.5 text-sm text-white" />
                </div>
            </div>
            <div class="px-6 pb-5 flex gap-3">
                <button onclick={() => showForm = false} class="flex-1 rounded-xl bg-gray-800 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors">Отмена</button>
                <button onclick={saveIntent} disabled={formSaving} class="flex-1 rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-700 transition-colors">
                    {formSaving ? 'Сохраняю...' : 'Сохранить'}
                </button>
            </div>
        </div>
    </div>
{/if}
