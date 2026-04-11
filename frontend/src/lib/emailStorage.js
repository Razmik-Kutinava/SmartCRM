import { browser } from '$app/environment';

function apiBase() {
    if (!browser) return 'http://127.0.0.1:8000';
    const pub = import.meta.env.PUBLIC_API_URL;
    if (pub) return String(pub).replace(/\/$/, '');
    return '';
}

const EMAIL_API = () => `${apiBase()}/api/email`;

export async function fetchEmailAccounts() {
    const r = await fetch(`${EMAIL_API()}/accounts`);
    if (!r.ok) throw new Error('Ошибка при загрузке почтовых аккаунтов');
    return r.json();
}

export async function connectEmailAccount(body) {
    const r = await fetch(`${EMAIL_API()}/accounts/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!r.ok) {
        const text = await r.text().catch(() => '');
        throw new Error(`Ошибка подключения: ${r.status} ${text}`);
    }
    return r.json();
}

export async function fetchLeadEmails(leadId) {
    const r = await fetch(`${apiBase()}/api/leads/${leadId}/email`);
    if (!r.ok) throw new Error('Ошибка загрузки писем лида');
    return r.json();
}

export async function sendLeadEmail(body) {
    const r = await fetch(`${EMAIL_API()}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!r.ok) {
        const text = await r.text().catch(() => '');
        throw new Error(`Ошибка отправки письма: ${r.status} ${text}`);
    }
    return r.json();
}

export async function replyToEmail(body) {
    const r = await fetch(`${EMAIL_API()}/reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!r.ok) {
        const text = await r.text().catch(() => '');
        throw new Error(`Ошибка ответа: ${r.status} ${text}`);
    }
    return r.json();
}

export async function createCampaign(body) {
    const r = await fetch(`${EMAIL_API()}/campaigns`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!r.ok) {
        const text = await r.text().catch(() => '');
        throw new Error(`Ошибка кампании: ${r.status} ${text}`);
    }
    return r.json();
}

export async function fetchEmailCampaigns() {
    const r = await fetch(`${EMAIL_API()}/campaigns`);
    if (!r.ok) {
        const text = await r.text().catch(() => '');
        throw new Error(`Ошибка загрузки кампаний: ${r.status} ${text}`);
    }
    return r.json();
}

export async function bindEmailToLead(body) {
    const r = await fetch(`${EMAIL_API()}/bind-lead`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!r.ok) {
        const text = await r.text().catch(() => '');
        throw new Error(`Ошибка привязки: ${r.status} ${text}`);
    }
    return r.json();
}

export async function fetchEmailThreads(params = {}) {
    const query = new URLSearchParams(params).toString();
    const r = await fetch(`${EMAIL_API()}/threads?${query}`);
    if (!r.ok) throw new Error('Ошибка загрузки тредов');
    return r.json();
}

export async function archiveEmail(emailId) {
    const r = await fetch(`${EMAIL_API()}/archive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_id: emailId }),
    });
    if (!r.ok) {
        const text = await r.text().catch(() => '');
        throw new Error(`Ошибка архивации: ${r.status} ${text}`);
    }
    return r.json();
}
