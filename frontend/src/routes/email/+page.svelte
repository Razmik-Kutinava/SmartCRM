<script>
    import { onMount } from 'svelte';
    import { fetchEmailAccounts, connectEmailAccount, fetchEmailThreads, sendLeadEmail, replyToEmail, fetchLeadEmails, createCampaign, bindEmailToLead, fetchEmailCampaigns } from '$lib/emailStorage.js';
    import { fetchLeads } from '$lib/leadsStorage.js';

    let accounts = $state([]);
    let threads = $state([]);
    let campaigns = $state([]);
    let name = $state('');
    let provider = $state('generic');
    let username = $state('');
    let password = $state('');
    let imap_server = $state('imap.yandex.com');
    let imap_port = $state(993);
    let smtp_server = $state('smtp.yandex.com');
    let smtp_port = $state(465);
    let use_ssl = $state(true);
    let error = $state('');
    let success = $state('');
    let loading = $state(false);
    
    // Email-to-lead binding
    let selectedAccountId = $state(null);
    let selectedLeadId = $state(null);
    let leadEmails = $state([]);
    let availableLeads = $state([]);
    
    // Campaign creation
    let campaignName = $state('');
    let campaignSubject = $state('');
    let campaignBody = $state('');
    let campaignLeadIds = $state([]);
    let campaignLoading = $state(false);

    async function load() {
        try {
            const fetchedAccounts = await fetchEmailAccounts();
            accounts = fetchedAccounts.filter((value, index, self) => self.findIndex(v => v.username === value.username) === index);
            threads = await fetchEmailThreads();
            campaigns = await fetchEmailCampaigns();
            availableLeads = await fetchLeads();
        } catch (e) {
            console.error('Ошибка загрузки email данных:', e);
            error = e.message;
        }
    }

    onMount(load);

    async function handleBindEmailToLead() {
        if (!selectedAccountId || !selectedLeadId) {
            error = 'Выберите почту и лида';
            return;
        }
        try {
            error = '';
            success = '';
            const result = await bindEmailToLead({
                account_id: selectedAccountId,
                lead_id: selectedLeadId,
            });
            const lead = availableLeads.find(l => l.id === selectedLeadId);
            const account = accounts.find(a => a.id === selectedAccountId);
            success = `✅ Email ${account?.username} успешно привязана к лиду ${lead?.company}`;
            selectedAccountId = null;
            selectedLeadId = null;
        } catch (e) {
            console.error('Ошибка привязки:', e);
            error = `❌ Ошибка привязки: ${e.message}`;
        }
    }

    async function createNewCampaign() {
        if (!selectedAccountId || !campaignName || !campaignSubject || campaignLeadIds.length === 0) {
            error = 'Заполни все поля и выбери минимум одного лида';
            return;
        }
        try {
            error = '';
            success = '';
            campaignLoading = true;
            const result = await createCampaign({
                account_id: selectedAccountId,
                name: campaignName,
                subject: campaignSubject,
                body: campaignBody,
                lead_ids: campaignLeadIds,
                send_now: false,
            });
            campaigns = await fetchEmailCampaigns();
            success = `Кампания "${campaignName}" создана. Она сохранена в черновиках.`;
            campaignName = '';
            campaignSubject = '';
            campaignBody = '';
            campaignLeadIds = [];
        } catch (e) {
            console.error('Ошибка создания кампании:', e);
            error = `❌ ${e.message}`;
        } finally {
            campaignLoading = false;
        }
    }

    function toggleLeadSelection(leadId) {
        if (campaignLeadIds.includes(leadId)) {
            campaignLeadIds = campaignLeadIds.filter(id => id !== leadId);
        } else {
            campaignLeadIds = [...campaignLeadIds, leadId];
        }
    }

    async function connect() {
        error = '';
        success = '';
        loading = true;
        console.log('Попытка подключения:', { name, username, imap_server, imap_port });
        try {
            if (!name || !username || !password) {
                throw new Error('Заполни все обязательные поля (название, email, пароль)');
            }
            const payload = {
                name,
                provider,
                username,
                password,
                imap_server,
                imap_port,
                smtp_server,
                smtp_port,
                use_ssl,
            };
            console.log('Отправка запроса:', payload);
            const result = await connectEmailAccount(payload);
            console.log('Результат подключения:', result);
            if (result.sync?.error) {
                throw new Error(result.sync.error);
            }
            accounts = await fetchEmailAccounts();
            threads = await fetchEmailThreads();
            campaigns = await fetchEmailCampaigns();
            success = `✅ Аккаунт ${result.account.name} подключён. Импортировано ${result.sync.imported || 0} писем.`;
            // Очистить форму после успеха
            name = '';
            username = '';
            password = '';
        } catch (e) {
            console.error('Ошибка подключения:', e);
            error = `❌ Ошибка: ${e.message}`;
        } finally {
            loading = false;
        }
    }
</script>

<div class="p-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
            <h1 class="text-2xl font-semibold text-white">Email-интеграция</h1>
            <p class="text-sm text-gray-400 mt-1">Подключай почтовые аккаунты, синхронизируй письма и связывай их с лидами.</p>
        </div>
        <a href="/leads" class="text-sm text-indigo-400 hover:text-indigo-300">← Вернуться к лидам</a>
    </div>

    {#if error}
        <div class="mt-4 p-4 rounded-xl bg-red-950 text-red-200">{error}</div>
    {/if}
    {#if success}
        <div class="mt-4 p-4 rounded-xl bg-green-950 text-green-200">{success}</div>
    {/if}

    <div class="mt-6 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <div class="space-y-4 bg-gray-900 border border-gray-800 rounded-3xl p-5">
            <div class="text-sm text-gray-400 uppercase tracking-wide">Подключить почту</div>
            <div class="grid gap-3">
                <label class="text-sm text-gray-300">Название аккаунта</label>
                <input bind:value={name} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" placeholder="Моя почта" />
                <label class="text-sm text-gray-300">Email</label>
                <input bind:value={username} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" placeholder="user@example.com" />
                <label class="text-sm text-gray-300">Пароль / app password</label>
                <input type="password" bind:value={password} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" placeholder="Пароль почты" />
                <div class="grid gap-3 md:grid-cols-2">
                    <div>
                        <label class="text-sm text-gray-300">IMAP сервер</label>
                        <input bind:value={imap_server} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" />
                    </div>
                    <div>
                        <label class="text-sm text-gray-300">IMAP порт</label>
                        <input type="number" bind:value={imap_port} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" />
                    </div>
                </div>
                <div class="grid gap-3 md:grid-cols-2">
                    <div>
                        <label class="text-sm text-gray-300">SMTP сервер</label>
                        <input bind:value={smtp_server} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" />
                    </div>
                    <div>
                        <label class="text-sm text-gray-300">SMTP порт</label>
                        <input type="number" bind:value={smtp_port} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" />
                    </div>
                </div>
                <button on:click={connect} class="w-full rounded-2xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors" disabled={loading}>
                    {loading ? 'Подключение...' : 'Подключить и синхронизировать'}
                </button>
            </div>
        </div>

        <div class="space-y-4">
            <div class="bg-gray-900 border border-gray-800 rounded-3xl p-5">
                <div class="text-sm text-gray-400 uppercase tracking-wide">Подключённые аккаунты</div>
                {#if accounts.length}
                    <div class="mt-4 space-y-3">
                        {#each accounts as account}
                            <div class="rounded-2xl border border-gray-800 bg-gray-950 p-3 text-sm text-white">
                                <div class="font-medium">{account.name}</div>
                                <div class="text-gray-400 text-xs mt-1">{account.username}</div>
                                <div class="mt-2 text-xs text-gray-500">Последняя синхронизация: {account.lastSyncedAt ?? 'никогда'}</div>
                            </div>
                        {/each}
                    </div>
                {:else}
                    <div class="mt-4 text-sm text-gray-500">Аккаунтов ещё нет. Подключи любой IMAP/SMTP-почтовый ящик.</div>
                {/if}
            </div>
            <div class="bg-gray-900 border border-gray-800 rounded-3xl p-5">
                <div class="text-sm text-gray-400 uppercase tracking-wide">Последние ветки переписки</div>
                {#if threads.length}
                    <div class="mt-4 space-y-3">
                        {#each threads as thread}
                            <div class="rounded-2xl border border-gray-800 bg-gray-950 p-3">
                                <div class="text-sm font-medium text-white">{thread.subject}</div>
                                <div class="text-xs text-gray-400 mt-1">{thread.snippet}</div>
                                <div class="flex items-center justify-between mt-2 text-xs text-gray-500">
                                    <span>{thread.category}</span>
                                    <span>{thread.lastMessageAt ? new Date(thread.lastMessageAt).toLocaleString('ru-RU') : '—'}</span>
                                </div>
                            </div>
                        {/each}
                    </div>
                {:else}
                    <div class="mt-4 text-sm text-gray-500">Пока нет синхронизированных тредов.</div>
                {/if}
            </div>
        </div>
    </div>

    <!-- Привязка email к лиду -->
    <div class="mt-8">
        <h2 class="text-xl font-semibold text-white mb-4">Привязка почты к лидам</h2>
        <div class="bg-gray-900 border border-gray-800 rounded-3xl p-5 space-y-4">
            <div class="grid gap-4 md:grid-cols-2">
                <div>
                    <label class="text-sm text-gray-300 block mb-2">Выбери почтовый аккаунт</label>
                    <select bind:value={selectedAccountId} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white">
                        <option value={null}>Выбери аккаунт...</option>
                        {#each accounts as account}
                            <option value={account.id}>{account.name} ({account.username})</option>
                        {/each}
                    </select>
                </div>
                <div>
                    <label class="text-sm text-gray-300 block mb-2">Выбери лида</label>
                    <select bind:value={selectedLeadId} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white">
                        <option value={null}>Выбери лида...</option>
                        {#each availableLeads as lead}
                            <option value={lead.id}>{lead.company} ({lead.contact_email || 'нет email'})</option>
                        {/each}
                    </select>
                </div>
            </div>
            <button on:click={handleBindEmailToLead} class="w-full rounded-2xl bg-purple-600 px-4 py-3 text-sm font-semibold text-white hover:bg-purple-500 transition-colors">
                Привязать почту к лиду
            </button>
        </div>
    </div>

    <!-- Создание кампании рассылок -->
    <div class="mt-8">
        <h2 class="text-xl font-semibold text-white mb-4">Создать кампанию рассылок</h2>
        <div class="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <div class="bg-gray-900 border border-gray-800 rounded-3xl p-5 space-y-4">
                <div>
                    <label class="text-sm text-gray-300 block mb-2">Аккаунт для отправки</label>
                    <select bind:value={selectedAccountId} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white">
                        <option value={null}>Выбери аккаунт...</option>
                        {#each accounts as account}
                            <option value={account.id}>{account.name} ({account.username})</option>
                        {/each}
                    </select>
                </div>
                <div>
                    <label class="text-sm text-gray-300 block mb-2">Название кампании</label>
                    <input bind:value={campaignName} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" placeholder="Летняя акция 2026" />
                </div>
                <div>
                    <label class="text-sm text-gray-300 block mb-2">Тема письма</label>
                    <input bind:value={campaignSubject} class="w-full rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" placeholder="Получай скидку 20% на все услуги" />
                </div>
                <div>
                    <label class="text-sm text-gray-300 block mb-2">Текст письма</label>
                    <textarea bind:value={campaignBody} class="w-full h-32 rounded-xl bg-gray-950 border border-gray-800 px-4 py-3 text-sm text-white" placeholder="Добро пожаловать! Мы рады пригласить вас на..." />
                </div>
                <button on:click={createNewCampaign} disabled={campaignLoading} class="w-full rounded-2xl bg-green-600 px-4 py-3 text-sm font-semibold text-white hover:bg-green-500 transition-colors disabled:bg-gray-600">
                    {campaignLoading ? 'Создание...' : 'Создать кампанию'}
                </button>
            </div>

            <div class="bg-gray-900 border border-gray-800 rounded-3xl p-5">
                <div class="text-sm text-gray-400 uppercase tracking-wide mb-4">Выбранные лиды ({campaignLeadIds.length})</div>
                {#if availableLeads.length}
                    <div class="space-y-2 max-h-96 overflow-y-auto">
                        {#each availableLeads as lead}
                            <label class="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-800 transition-colors cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    checked={campaignLeadIds.includes(lead.id)}
                                    on:change={() => toggleLeadSelection(lead.id)}
                                    class="rounded"
                                />
                                <div>
                                    <div class="text-sm font-medium text-white">{lead.company}</div>
                                    <div class="text-xs text-gray-400">{lead.contact_email || 'нет email'}</div>
                                </div>
                            </label>
                        {/each}
                    </div>
                {:else}
                    <div class="text-sm text-gray-500">Нет лидов для выбора. Добавь лидов в раздел "Лиды".</div>
                {/if}
            </div>
        </div>
    </div>

    <!-- Список кампаний -->
    <div class="mt-8">
        <h2 class="text-xl font-semibold text-white mb-4">Кампании рассылок</h2>
        <div class="bg-gray-900 border border-gray-800 rounded-3xl p-5">
            {#if campaigns.length}
                <div class="space-y-3">
                    {#each campaigns as campaign}
                        <div class="rounded-2xl border border-gray-800 bg-gray-950 p-4">
                            <div class="flex items-center justify-between gap-3">
                                <div>
                                    <div class="text-sm font-semibold text-white">{campaign.name}</div>
                                    <div class="text-xs text-gray-400">{campaign.subject}</div>
                                </div>
                                <div class="text-xs text-gray-500">{campaign.status}</div>
                            </div>
                            <div class="mt-3 text-xs text-gray-400">Лидов: {campaign.leadIds.length} · Отправлено: {campaign.sentCount}</div>
                            <div class="mt-2 text-xs text-gray-500">Создано: {campaign.created}</div>
                        </div>
                    {/each}
                </div>
            {:else}
                <div class="text-sm text-gray-500">Пока нет кампаний. Создай новую кампанию выше.</div>
            {/if}
        </div>
    </div>
</div>
