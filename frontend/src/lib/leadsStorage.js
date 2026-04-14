/**
 * Слой данных лидов.
 * Источник правды — PostgreSQL через /api/leads.
 * localStorage используется только как быстрый кэш для отображения при загрузке
 * (пока не пришёл ответ от API).
 */
import { browser } from '$app/environment';

const CACHE_KEY = 'smartcrm_leads_cache_v2';

/**
 * В dev-режиме используем абсолютный URL до бэкенда напрямую,
 * чтобы не зависеть от Vite proxy (который может не запуститься).
 * CORS в FastAPI разрешён для localhost:5173/5174.
 * В prod PUBLIC_API_URL берётся из .env.
 */
function apiBase() {
	if (!browser) return 'http://127.0.0.1:8000';
	const pub = import.meta.env.PUBLIC_API_URL;
	if (pub) return String(pub).replace(/\/$/, '');
	// В dev используем относительный URL, чтобы Vite proxy проксировал /api к бэкенду.
	return '';
}

const API = () => `${apiBase()}/api/leads`;

// ── Кэш ────────────────────────────────────────────────────────────

function cacheWrite(leads) {
	if (!browser || !Array.isArray(leads)) return;
	try { localStorage.setItem(CACHE_KEY, JSON.stringify(leads)); } catch { /* квота */ }
}

function cacheRead() {
	if (!browser) return null;
	try {
		const raw = localStorage.getItem(CACHE_KEY);
		if (raw) {
			const parsed = JSON.parse(raw);
			if (Array.isArray(parsed) && parsed.length > 0) return parsed;
		}
	} catch { /* пусто */ }
	return null;
}

// ── Демо-данные (показываются, пока API недоступен) ────────────────

export const DEFAULT_LEADS = [
	{
		id: 1,
		company: 'ООО "ТехноСтрой"',
		contact: 'Иван Петров',
		email: 'i.petrov@technostroy.ru',
		phone: '+7 495 123-45-67',
		stage: 'Квалифицирован',
		score: 87,
		source: 'Сайт',
		budget: '500 000 ₽',
		created: '01.04.2026',
		position: 'Директор по закупкам',
		website: 'technostroy.ru',
		employees: '200+',
		industry: 'Строительство',
		city: 'Москва',
		nextCall: '10.04.2026 14:00',
		description: 'Ищут ERP для управления закупками. Сейчас используют Excel.',
		history: [
			{ type: 'call', text: 'Первый звонок. Выявили боли: Excel, согласования по 2 недели.', date: '02.04.2026', author: 'Я' },
			{ type: 'agent', text: 'Аналитик: скоринг обновлён до 87.', date: '01.04.2026', author: 'Аналитик' },
		],
		tasks: [
			{ title: 'Назначить демо', due: '10.04.2026', status: 'pending' },
			{ title: 'Первый звонок', due: '02.04.2026', status: 'done' },
		],
	},
	{ id: 2, company: 'АО "МашПром"', contact: 'Елена Соколова', email: 'e.sokolova@mashprom.ru', phone: '+7 812 234-56-78', stage: 'Переговоры', score: 92, source: 'Холодный звонок', budget: '1 200 000 ₽', created: '28.03.2026', position: '—', website: '—', employees: '—', industry: '—', city: '—', nextCall: '—', description: '', history: [], tasks: [] },
	{ id: 3, company: 'ГК "АвтоЛогист"', contact: 'Дмитрий Козлов', email: 'd.kozlov@autolog.ru', phone: '+7 903 345-67-89', stage: 'Новый', score: 45, source: 'Реклама', budget: '—', created: '05.04.2026', position: '—', website: '—', employees: '—', industry: '—', city: '—', nextCall: '—', description: '', history: [], tasks: [] },
	{ id: 4, company: 'ООО "СтальМет"', contact: 'Анна Иванова', email: 'a.ivanova@stalmet.ru', phone: '+7 916 456-78-90', stage: 'КП отправлено', score: 76, source: 'Рекомендация', budget: '800 000 ₽', created: '02.04.2026', position: '—', website: '—', employees: '—', industry: '—', city: '—', nextCall: '—', description: '', history: [], tasks: [] },
	{ id: 5, company: 'ЗАО "ТрейдГрупп"', contact: 'Сергей Новиков', email: 's.novikov@tgrup.ru', phone: '+7 926 567-89-01', stage: 'Новый', score: 38, source: 'Сайт', budget: '—', created: '07.04.2026', position: '—', website: '—', employees: '—', industry: '—', city: '—', nextCall: '—', description: '', history: [], tasks: [] },
	{ id: 6, company: 'ООО "МаркетПро"', contact: 'Мария Соколова', email: 'm.sokolova@mktpro.ru', phone: '+7 985 678-90-12', stage: 'Выигран', score: 95, source: 'LinkedIn', budget: '300 000 ₽', created: '15.03.2026', position: '—', website: '—', employees: '—', industry: '—', city: '—', nextCall: '—', description: '', history: [], tasks: [] },
	{ id: 7, company: 'ИП Романов К.А.', contact: 'Кирилл Романов', email: 'k.romanov@mail.ru', phone: '+7 977 789-01-23', stage: 'Проигран', score: 20, source: 'Реклама', budget: '150 000 ₽', created: '20.03.2026', position: '—', website: '—', employees: '—', industry: '—', city: '—', nextCall: '—', description: '', history: [], tasks: [] },
];

// ── API ─────────────────────────────────────────────────────────────

/** Загрузить все лиды из БД */
export async function fetchLeads() {
	const url = API();
	const r = await fetch(url);
	if (!r.ok) throw new Error(`GET ${url} → ${r.status}`);
	const leads = await r.json();
	cacheWrite(leads);
	return leads;
}

/** Создать лид в БД */
export async function apiCreateLead(data) {
	const url = API();
	console.log('[API] POST', url, data);
	const r = await fetch(url, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data),
	});
	if (!r.ok) {
		const text = await r.text().catch(() => '');
		throw new Error(`POST ${url} → ${r.status}: ${text}`);
	}
	return r.json();
}

/** Обновить поля лида в БД */
export async function apiUpdateLead(id, patch) {
	const url = `${API()}/${id}`;
	console.log('[API] PATCH', url, patch);
	const r = await fetch(url, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(patch),
	});
	if (!r.ok) {
		const text = await r.text().catch(() => '');
		throw new Error(`PATCH ${url} → ${r.status}: ${text}`);
	}
	return r.json();
}

/** Удалить лид в БД */
export async function apiDeleteLead(id) {
	const url = `${API()}/${id}`;
	console.log('[API] DELETE', url);
	const r = await fetch(url, { method: 'DELETE' });
	if (!r.ok) throw new Error(`DELETE ${url} → ${r.status}`);
}

/** Сводка: total в Битриксе по фильтру + сколько лидов у нас с bitrix_lead_id */
export async function fetchBitrixImportStats(date_from = '2023-01-01') {
	const url = `${API()}/bitrix-import-stats?date_from=${encodeURIComponent(date_from)}`;
	const r = await fetch(url);
	const text = await r.text().catch(() => '');
	let body;
	try {
		body = text ? JSON.parse(text) : {};
	} catch {
		body = { detail: text };
	}
	if (!r.ok) {
		const d = body?.detail;
		const msg =
			typeof d === 'string'
				? d
				: Array.isArray(d)
					? d.map((x) => x.msg || x).join('; ')
					: d
						? JSON.stringify(d)
						: text || `HTTP ${r.status}`;
		throw new Error(msg);
	}
	return body;
}

/** Импорт лидов из Битрикс24 (на бэкенде нужен BITRIX24_WEBHOOK_URL). max_items=0 — без лимита. */
export async function apiImportBitrix(options = {}) {
	const { date_from = '2023-01-01', max_items = 0 } = options;
	const url = `${API()}/import-bitrix`;
	const r = await fetch(url, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ date_from, max_items }),
	});
	const text = await r.text().catch(() => '');
	let body;
	try {
		body = text ? JSON.parse(text) : {};
	} catch {
		body = { detail: text };
	}
	if (!r.ok) {
		const d = body?.detail;
		const msg =
			typeof d === 'string'
				? d
				: Array.isArray(d)
					? d.map((x) => x.msg || x).join('; ')
					: d
						? JSON.stringify(d)
						: text || `HTTP ${r.status}`;
		throw new Error(msg);
	}
	return body;
}

// ── Кэш-совместимые синхронные функции (для SSR-guard) ─────────────

/** Вернуть список из кэша или демо-данные — вызов синхронный, данные могут быть устаревшими */
export function readLeadsCache() {
	return cacheRead() ?? structuredClone(DEFAULT_LEADS);
}

/** Сохранить список в кэш */
export function writeLeadsCache(leads) {
	cacheWrite(leads);
}

// ── Карточка ─────────────────────────────────────────────────────

/** Подставить дефолты для полей карточки, которых может не быть у голосовых лидов */
export function enrichLeadForCard(raw) {
	if (!raw) return null;
	const base = {
		position: '—',
		website: '—',
		employees: '—',
		industry: '—',
		city: '—',
		responsible: 'Я',
		nextCall: '—',
		description: '',
		history: [],
		tasks: [],
	};
	return {
		...base,
		...raw,
		history: Array.isArray(raw.history) ? raw.history : base.history,
		tasks: Array.isArray(raw.tasks) ? raw.tasks : base.tasks,
	};
}

export function getLeadById(id) {
	const n = Number(id);
	if (Number.isNaN(n)) return null;
	const list = readLeadsCache();
	return list.find((l) => l.id === n) ?? null;
}
