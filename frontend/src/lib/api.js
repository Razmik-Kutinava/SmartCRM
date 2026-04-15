/**
 * Централизованный HTTP-клиент SmartCRM.
 *
 * Автоматически добавляет X-API-Key если задан PUBLIC_SMARTCRM_API_KEY.
 * В dev-режиме без ключа — работает как обычный fetch (ничего не ломается).
 *
 * Использование:
 *   import { apiFetch } from '$lib/api.js';
 *   const data = await apiFetch('/api/leads').then(r => r.json());
 *
 * Чтобы включить auth: добавьте в frontend/.env
 *   PUBLIC_SMARTCRM_API_KEY=ваш-ключ
 */
import { getApiUrl } from './websocket.js';

const API_KEY = import.meta.env.PUBLIC_SMARTCRM_API_KEY || '';

/**
 * Обёртка над fetch: добавляет X-API-Key и базовый URL.
 * @param {string} path  — путь начиная с /api/...
 * @param {RequestInit} [options]
 * @returns {Promise<Response>}
 */
export async function apiFetch(path, options = {}) {
	const base = getApiUrl();
	const headers = new Headers(options.headers || {});

	if (API_KEY) {
		headers.set('X-API-Key', API_KEY);
	}

	return fetch(`${base}${path}`, { ...options, headers });
}

/**
 * JSON GET с авторизацией.
 */
export async function apiGet(path) {
	return apiFetch(path);
}

/**
 * JSON POST с авторизацией.
 */
export async function apiPost(path, body) {
	return apiFetch(path, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
}

/**
 * JSON PATCH с авторизацией.
 */
export async function apiPatch(path, body) {
	return apiFetch(path, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
}

/**
 * DELETE с авторизацией.
 */
export async function apiDelete(path) {
	return apiFetch(path, { method: 'DELETE' });
}
