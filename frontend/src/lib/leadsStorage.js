/**
 * Слой данных лидов.
 * Источник правды — PostgreSQL через /api/leads.
 * localStorage используется только как быстрый кэш для отображения при загрузке
 * (пока не пришёл ответ от API).
 */
import { browser } from '$app/environment';
import { apiPatch, apiDelete } from './api.js';
import { defaultApprovals, mergeApprovals } from './leadApprovals.js';
import { formatLeadPatchError } from './leads/stageTransition.js';

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
/** In-memory зеркало: при переполнении localStorage (~5MB) запись молчит, память остаётся. */
let memoryCache = null;

/**
 * Досье исследования, сырые UF и история нужны только карточке, а она
 * читает лид из детального API. В кэше списка они съедали всю квоту
 * localStorage: 3231 лид давал 4.7 МБ, запись падала молча и кэш застывал.
 *
 * На базе от ~2500 лидов даже облегчённый список не влезает в квоту — тогда
 * кэш отключается сам (ключ удаляется), список ждёт ответ API. Настоящее
 * лечение — пагинация `/api/leads`, см. BACKLOG.
 */
const HEAVY_FIELDS = ['checko', 'tech', 'techJson', 'checkoJson', 'bitrixExtra', 'history', 'approvals'];

function cacheSlim(leads) {
	return leads.map((lead) => {
		const slim = { ...lead };
		for (const field of HEAVY_FIELDS) delete slim[field];
		return slim;
	});
}

function cacheWrite(leads) {
	if (!browser || !Array.isArray(leads)) return;
	memoryCache = leads;
	try {
		localStorage.setItem(CACHE_KEY, JSON.stringify(cacheSlim(leads)));
	} catch {
		// Переполнение: старый кэш держит квоту занятой и мешает писать
		// остальные ключи (настройки, порядок плиток) — убираем его.
		try {
			localStorage.removeItem(CACHE_KEY);
		} catch {
			/* приватный режим — остаётся memoryCache */
		}
	}
}

function cacheRead() {
	if (!browser) return null;
	if (Array.isArray(memoryCache) && memoryCache.length > 0) return memoryCache;
	try {
		const raw = localStorage.getItem(CACHE_KEY);
		if (raw) {
			const parsed = JSON.parse(raw);
			if (Array.isArray(parsed) && parsed.length > 0) {
				memoryCache = parsed;
				return parsed;
			}
		}
	} catch { /* пусто */ }
	return null;
}

/** Сброс in-memory кэша (тесты / смена вкладки не трогаем). */
export function clearLeadsMemoryCache() {
	memoryCache = null;
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
/** Полный ответ по одному лиду (включая scoreAdvisory) и обновление кэша списка */
export async function fetchLeadById(id) {
	const n = Number(id);
	if (Number.isNaN(n)) throw new Error('Некорректный id лида');
	const url = `${API()}/${n}`;
	const r = await fetch(url);
	if (!r.ok) {
		const text = await r.text().catch(() => '');
		throw new Error(`GET ${url} → ${r.status}: ${text}`);
	}
	const lead = await r.json();
	const all = readLeadsCache();
	const sameId = (l) => Number(l?.id) === n;
	const idx = all.findIndex(sameId);
	const next = idx >= 0 ? all.map((l) => (sameId(l) ? lead : l)) : [...all, lead];
	cacheWrite(next);
	return lead;
}

export async function apiUpdateLead(id, patch) {
	const path = `/api/leads/${id}`;
	console.log('[API] PATCH', path, patch);
	const r = await apiPatch(path, patch);
	if (!r.ok) {
		const text = await r.text().catch(() => '');
		let parsed = {};
		try {
			parsed = text ? JSON.parse(text) : {};
		} catch {
			/* text */
		}
		throw new Error(formatLeadPatchError(r.status, text, parsed));
	}
	return r.json();
}

/** Удалить лид в БД */
export async function apiDeleteLead(id) {
	const path = `/api/leads/${id}`;
	console.log('[API] DELETE', path);
	const r = await apiDelete(path);
	if (!r.ok) {
		const text = await r.text().catch(() => '');
		throw new Error(`DELETE ${path} → ${r.status}: ${text}`);
	}
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

/** Сегменты полноты карточки + прогресс B24 resync */
export async function fetchLeadCoverage() {
	const r = await fetch(`${API()}/coverage`);
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

/** Справочник менеджеров (ответственный + bitrix_extra.manager) */
export async function fetchLeadManagers() {
	const r = await fetch(`${API()}/managers`);
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

/** Дела по лидам — GET /api/leads/activities (вкладка «Дела» как в B24). */
export async function fetchLeadActivities({ due = 'scheduled', manager = null } = {}) {
	const qs = new URLSearchParams();
	if (due && due !== 'scheduled') qs.set('due', due);
	const mgr = manager && manager !== 'all' ? String(manager).trim() : '';
	if (mgr) qs.set('manager', mgr);
	const url = `${API()}/activities${qs.toString() ? `?${qs}` : ''}`;
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

/** Импорт лидов из AmoCRM. */
export async function apiImportAmo() {
	const r = await fetch(`${API()}/import-amo`, { method: 'POST' });
	const body = await r.json().catch(() => ({}));
	if (!r.ok) throw new Error(body?.detail || `HTTP ${r.status}`);
	return body;
}

/** Импорт сделок из HubSpot. */
export async function apiImportHubspot() {
	const r = await fetch(`${API()}/import-hubspot`, { method: 'POST' });
	const body = await r.json().catch(() => ({}));
	if (!r.ok) throw new Error(body?.detail || `HTTP ${r.status}`);
	return body;
}

/** Импорт лидов из CSV/XLSX (mode: upsert | skip; source — метка базы всем строкам). */
export async function apiImportLeadsCsv(file, mode = 'upsert', source = '', mapping = null) {
	let url = `${API()}/import-csv?mode=${encodeURIComponent(mode)}`;
	if ((source || '').trim()) url += `&source=${encodeURIComponent(source.trim())}`;
	const fd = new FormData();
	fd.append('file', file);
	if (mapping && Object.keys(mapping).length) fd.append('mapping', JSON.stringify(mapping));
	const r = await fetch(url, { method: 'POST', body: fd });
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

/**
 * Превью файла перед импортом: заголовки, первые строки, предложенное сопоставление.
 * @returns {Promise<{ headers: string[], rows: string[][], totalRows: number,
 *   mapping: Record<string, string>, fields: Array<{ id: string, label: string, required: boolean }>,
 *   suggestedSource: string }>}
 */
export async function apiImportPreview(file) {
	const fd = new FormData();
	fd.append('file', file);
	const r = await fetch(`${API()}/import-preview`, { method: 'POST', body: fd });
	const text = await r.text().catch(() => '');
	let body;
	try {
		body = text ? JSON.parse(text) : {};
	} catch {
		body = { detail: text };
	}
	if (!r.ok) {
		const d = body?.detail;
		throw new Error(typeof d === 'string' ? d : text || `HTTP ${r.status}`);
	}
	return body;
}

/** Справочник источников (баз) лидов: [{ name, count, withEmail }] + bases. */
export async function fetchLeadSources() {
	const r = await fetch(`${API()}/sources`);
	if (!r.ok) throw new Error(`Источники лидов: HTTP ${r.status}`);
	const body = await r.json().catch(() => ({}));
	return body.sources || [];
}

/** Базы для переключателя списка: Битрикс + именованные [{ id, label, count, kind }]. */
export async function fetchLeadBases() {
	const r = await fetch(`${API()}/sources`);
	if (!r.ok) throw new Error(`Базы лидов: HTTP ${r.status}`);
	const body = await r.json().catch(() => ({}));
	if (Array.isArray(body.bases) && body.bases.length) return body.bases;
	return (body.sources || []).map((s) => ({
		id: s.name,
		label: s.name,
		name: s.name,
		count: s.count,
		withEmail: s.withEmail,
		kind: 'named',
	}));
}

/** Скачать все лиды CSV. */
export async function downloadLeadsCsvExport() {
	const url = `${API()}/export?format=csv`;
	const r = await fetch(url);
	if (!r.ok) throw new Error(`Экспорт CSV: HTTP ${r.status}`);
	const blob = await r.blob();
	const href = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = href;
	a.download = `leads-${new Date().toISOString().slice(0, 10)}.csv`;
	a.click();
	URL.revokeObjectURL(href);
}

// ── Кэш-совместимые синхронные функции (для SSR-guard) ─────────────

/** Вернуть список из кэша или демо-данные — вызов синхронный, данные могут быть устаревшими */
export function readLeadsCache() {
	return cacheRead() ?? structuredClone(DEFAULT_LEADS);
}

/** Кэш без подмены демо: `null` честно значит «данных ещё нет». */
export function readLeadsCacheOrNull() {
	return cacheRead();
}

/** Демо-витрина: показываем, только когда API недоступен. */
export function demoLeads() {
	return structuredClone(DEFAULT_LEADS);
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
		amountRub: null,
		paidAmountRub: null,
		scoreAdvisory: null,
		approvals: {},
	};
	const merged = {
		...base,
		...raw,
		history: Array.isArray(raw.history) ? raw.history : base.history,
		tasks: Array.isArray(raw.tasks) ? raw.tasks : base.tasks,
	};
	merged.approvals = mergeApprovals(defaultApprovals(), merged.approvals || {});
	return merged;
}

export function getLeadById(id) {
	const n = Number(id);
	if (Number.isNaN(n)) return null;
	const list = readLeadsCache();
	return list.find((l) => Number(l?.id) === n) ?? null;
}
