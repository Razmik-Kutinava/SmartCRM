/**
 * WebSocket + HTTP клиент SmartCRM
 * Dev: запросы через Vite proxy (тот же host, что и страница) — WS стабильнее.
 * Prod / override: PUBLIC_API_URL=http://host:8000
 */
import { browser } from '$app/environment';

let ws = null;
let listeners = [];
let reconnectTimer = null;
/** Очередь текста, пока сокет CONNECTING (убирает дубли sendText+setTimeout) */
let pendingTexts = [];
/** Очередь аудио — иначе sendAudio молча теряется, если сокет ещё не OPEN */
let pendingAudioBlobs = [];

function apiBase() {
	const p = import.meta.env.PUBLIC_API_URL;
	if (p) return String(p).replace(/\/$/, '');
	if (import.meta.env.DEV && browser) return '';
	return 'http://127.0.0.1:8000';
}

/** База для fetch (на SSR в dev — абсолютный URL, в браузере — '' для proxy) */
export function getApiUrl() {
	return apiBase();
}

export const API_URL = apiBase();

function wsUrl() {
	const base = apiBase();
	if (base === '' && typeof window !== 'undefined') {
		const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		return `${proto}//${window.location.host}/ws/voice`;
	}
	return `${base.replace(/^http/, 'ws')}/ws/voice`;
}

export function onMessage(fn) {
	listeners.push(fn);
	return () => {
		listeners = listeners.filter((l) => l !== fn);
	};
}

function emit(data) {
	listeners.forEach((fn) => fn(data));
}

function drainPending() {
	if (!ws || ws.readyState !== WebSocket.OPEN) return;
	while (pendingTexts.length) {
		const payload = pendingTexts.shift();
		// payload — уже сериализованный JSON строки (от sendText) или строка текста (старый код)
		if (payload.startsWith('{')) {
			ws.send(payload);
		} else {
			ws.send(JSON.stringify({ type: 'text', text: payload }));
		}
	}
}

async function drainPendingAudio() {
	if (!ws || ws.readyState !== WebSocket.OPEN) return;
	while (pendingAudioBlobs.length) {
		const blob = pendingAudioBlobs.shift();
		const buf = await blob.arrayBuffer();
		if (ws && ws.readyState === WebSocket.OPEN) ws.send(buf);
	}
}

export function connect() {
	if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

	ws = new WebSocket(wsUrl());

	ws.onopen = () => {
		clearTimeout(reconnectTimer);
		emit({ type: 'connected' });
		console.log('[WS] подключён');
		drainPending();
		drainPendingAudio();
	};

	ws.onclose = () => {
		emit({ type: 'disconnected' });
		console.log('[WS] отключён, переподключение через 3с...');
		reconnectTimer = setTimeout(connect, 3000);
	};

	ws.onerror = () => emit({ type: 'error', message: 'WebSocket ошибка соединения' });

	ws.onmessage = (e) => {
		try {
			emit(JSON.parse(e.data));
		} catch {
			/* пусто */
		}
	};
}

export function disconnect() {
	clearTimeout(reconnectTimer);
	pendingTexts = [];
	pendingAudioBlobs = [];
	ws?.close();
	ws = null;
}

/**
 * Отправить текстовую команду.
 * pageContext — опциональный контекст страницы ("Страница: Лиды" и т.п.)
 */
export function sendText(text, pageContext = '') {
	const t = String(text).trim();
	if (!t) return;

	const payload = JSON.stringify({ type: 'text', text: t, page_context: pageContext });

	if (!ws || ws.readyState === WebSocket.CLOSED) {
		pendingTexts.push(payload);
		connect();
		return;
	}
	if (ws.readyState === WebSocket.CONNECTING) {
		pendingTexts.push(payload);
		return;
	}
	if (ws.readyState === WebSocket.OPEN) {
		ws.send(payload);
	}
}

export function sendAudio(blob) {
	if (!blob || blob.size === 0) return;

	if (!ws || ws.readyState === WebSocket.CLOSED) {
		pendingAudioBlobs.push(blob);
		connect();
		return;
	}
	if (ws.readyState === WebSocket.CONNECTING) {
		pendingAudioBlobs.push(blob);
		return;
	}
	if (ws.readyState === WebSocket.OPEN) {
		blob.arrayBuffer().then((buf) => {
			if (ws && ws.readyState === WebSocket.OPEN) ws.send(buf);
		});
	}
}

/** HTTP: текстовая команда без WebSocket */
export async function postCommand(text) {
	const base = getApiUrl();
	const apiKey = import.meta.env.PUBLIC_SMARTCRM_API_KEY || '';
	const headers = { 'Content-Type': 'application/json' };
	if (apiKey) headers['X-API-Key'] = apiKey;
	const r = await fetch(`${base}/api/voice/command`, {
		method: 'POST',
		headers,
		body: JSON.stringify({ text })
	});
	return r.json();
}
