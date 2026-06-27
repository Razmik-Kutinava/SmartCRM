/** Фильтрация и группировка списка `/email` (зеркало: backend/tests/lib/test_email_list_logic.py). */

export const EMAIL_NAV_MAIN = [
	{ key: 'inbox', label: 'Входящие', icon: 'inbox', showCount: true },
	{ key: 'important', label: 'Главное', icon: 'star' },
	{ key: 'with_attachments', label: 'С вложениями', icon: 'attach' },
];

export const EMAIL_NAV_CUSTOM = [
	{ key: 'zoho', label: 'Zoho', showCount: true },
	{ key: 'templates', label: 'Templates' },
	{ key: 'mailing', label: 'рассылка' },
	{ key: 'notifications', label: 'уведомления' },
	{ key: 'archive', label: 'Архив' },
];

export const EMAIL_NAV_SYSTEM = [
	{ key: 'sent', label: 'Отправленные', icon: 'sent' },
	{ key: 'trash', label: 'Удалённые', icon: 'trash', placeholder: true },
	{ key: 'spam', label: 'Спам', icon: 'spam', disabled: true },
	{ key: 'drafts', label: 'Черновики', icon: 'drafts', placeholder: true },
];

/** Панели SmartCRM (не папки IMAP). */
export const EMAIL_NAV_SMARTCRM = [
	{ key: 'campaign_mass', label: 'Массовая (сегмент)', icon: 'campaign' },
	{ key: 'nurture_touch', label: 'Касания (1 лид)', icon: 'nurture' },
	{ key: 'campaigns_manage', label: 'Управление кампаниями', icon: 'manage' },
];

/** @deprecated — используй EMAIL_NAV_* */
export const EMAIL_FOLDERS = [
	{ key: 'inbox', label: 'Входящие', icon: '📥' },
	{ key: 'sent', label: 'Отправленные', icon: '📤' },
	{ key: 'zoho', label: 'Zoho', icon: '🔷' },
	{ key: 'campaign', label: 'Рассылки', icon: '📣' },
	{ key: 'archive', label: 'Архив', icon: '🗂' },
];

export const EMAIL_FILTER_CHIPS = [
	{ key: 'attachments', label: 'С вложениями', icon: 'attach' },
	{ key: 'date', label: 'Дата', icon: 'calendar', panel: true },
	{ key: 'folder', label: 'Папки', icon: 'folder', panel: true },
	{ key: 'from', label: 'От кого', icon: 'from', panel: true },
	{ key: 'to', label: 'Кому', icon: 'to', panel: true },
	{ key: 'more', label: 'Ещё', panel: true },
];

export const EMAIL_FOLDER_FILTER_OPTIONS = [
	{ key: '', label: 'Любая папка' },
	...EMAIL_NAV_MAIN.map((f) => ({ key: f.key, label: f.label })),
	...EMAIL_NAV_CUSTOM.map((f) => ({ key: f.key, label: f.label })),
	...EMAIL_NAV_SYSTEM.filter((f) => !f.disabled && !f.placeholder).map((f) => ({
		key: f.key,
		label: f.label,
	})),
];

const HIDDEN_IN_INBOX = new Set(['outbound', 'campaign', 'archive']);
const STARRED_STORAGE_KEY = 'smartcrm_email_starred_threads';

export function createEmptySearchFilters() {
	return {
		attachments: false,
		dateFrom: '',
		dateTo: '',
		folderKey: '',
		from: '',
		to: '',
		unreadOnly: false,
	};
}

export function loadStarredThreadIds() {
	if (typeof localStorage === 'undefined') return new Set();
	try {
		const raw = localStorage.getItem(STARRED_STORAGE_KEY);
		const arr = raw ? JSON.parse(raw) : [];
		return new Set(Array.isArray(arr) ? arr.map(String) : []);
	} catch {
		return new Set();
	}
}

export function saveStarredThreadIds(set) {
	if (typeof localStorage === 'undefined') return;
	localStorage.setItem(STARRED_STORAGE_KEY, JSON.stringify([...set].map(String)));
}

export function toggleStarredThreadId(set, threadId) {
	const next = new Set(set);
	const key = String(threadId);
	if (next.has(key)) next.delete(key);
	else next.add(key);
	saveStarredThreadIds(next);
	return next;
}

export function threadHasAttachments(thread) {
	if (thread?.hasAttachments === true) return true;
	const text = `${thread?.subject || ''} ${thread?.snippet || ''}`.toLowerCase();
	return /вложен|attachment|\.pdf|\.docx?|\.xlsx?|\.zip|📎/i.test(text);
}

export function isNotificationThread(thread) {
	const from = String(thread?.previewFrom || thread?.from || '').toLowerCase();
	return /noreply|no-reply|notification|mailer-daemon|уведомлен|donotreply/.test(from);
}

export function isTemplateThread(thread) {
	const text = `${thread?.subject || ''} ${thread?.snippet || ''}`.toLowerCase();
	return /template|шаблон/.test(text);
}

function matchFolder(thread, folder, starredIds = new Set()) {
	if (folder === 'inbox') {
		return !HIDDEN_IN_INBOX.has(thread.category) && !thread.isArchived;
	}
	if (folder === 'important') {
		return starredIds.has(String(thread.id));
	}
	if (folder === 'with_attachments') {
		return threadHasAttachments(thread) && !thread.isArchived;
	}
	if (folder === 'sent') return thread.category === 'outbound';
	if (folder === 'zoho') {
		return /zoho/i.test(`${thread.subject || ''} ${thread.snippet || ''}`);
	}
	if (folder === 'templates') return isTemplateThread(thread);
	if (folder === 'mailing' || folder === 'campaign') return thread.category === 'campaign';
	if (folder === 'notifications') return isNotificationThread(thread);
	if (folder === 'archive') return thread.isArchived;
	if (folder === 'trash' || folder === 'drafts' || folder === 'spam') return false;
	return true;
}

function matchSearchFilters(thread, filters = {}) {
	if (!filters || typeof filters !== 'object') return true;
	if (filters.attachments && !threadHasAttachments(thread)) return false;
	if (filters.from) {
		const q = String(filters.from).trim().toLowerCase();
		const from = String(thread.previewFrom || thread.from || '').toLowerCase();
		if (!from.includes(q)) return false;
	}
	if (filters.to) {
		const q = String(filters.to).trim().toLowerCase();
		const to = String(thread.previewTo || thread.to || thread.recipients || '').toLowerCase();
		if (!to.includes(q)) return false;
	}
	if (filters.folderKey && !matchFolder(thread, filters.folderKey)) return false;
	if (filters.dateFrom || filters.dateTo) {
		const d = thread.lastMessageAt ? new Date(thread.lastMessageAt) : null;
		if (!d || Number.isNaN(d.getTime())) return false;
		if (filters.dateFrom) {
			const from = new Date(filters.dateFrom);
			from.setHours(0, 0, 0, 0);
			if (d < from) return false;
		}
		if (filters.dateTo) {
			const to = new Date(filters.dateTo);
			to.setHours(23, 59, 59, 999);
			if (d > to) return false;
		}
	}
	return true;
}

export function filterEmailThreads(
	threads,
	{ folder = 'inbox', search = '', accountId = null, searchFilters = null, starredIds = null } = {}
) {
	let list = Array.isArray(threads) ? [...threads] : [];
	const stars = starredIds instanceof Set ? starredIds : new Set();

	if (accountId != null && accountId !== '') {
		list = list.filter((t) => t.accountId === accountId);
	}
	if (folder && !['campaign_mass', 'campaigns_manage', 'nurture_touch'].includes(folder)) {
		list = list.filter((t) => matchFolder(t, folder, stars));
	}
	const q = String(search || '').trim().toLowerCase();
	if (q) {
		list = list.filter(
			(t) =>
				String(t.subject || '').toLowerCase().includes(q) ||
				String(t.snippet || '').toLowerCase().includes(q) ||
				String(t.previewFrom || '').toLowerCase().includes(q)
		);
	}
	if (searchFilters) {
		list = list.filter((t) => matchSearchFilters(t, searchFilters));
	}
	return list;
}

export function countEmailFolder(threads, folder, starredIds = null) {
	return filterEmailThreads(threads, { folder, search: '', starredIds }).length;
}

export function isEmailPanelFolder(folder) {
	return ['campaign_mass', 'campaigns_manage', 'nurture_touch', 'campaign'].includes(folder);
}

export function groupThreadsByDate(threads, now = new Date()) {
	const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
	const yesterday = new Date(today);
	yesterday.setDate(today.getDate() - 1);
	const weekAgo = new Date(today);
	weekAgo.setDate(today.getDate() - 7);
	const groups = new Map();

	for (const t of threads) {
		const d = t.lastMessageAt ? new Date(t.lastMessageAt) : null;
		let label;
		if (!d || Number.isNaN(d.getTime())) {
			label = 'Дата неизвестна';
		} else {
			const day = new Date(d.getFullYear(), d.getMonth(), d.getDate());
			if (day >= today) label = 'Сегодня';
			else if (day >= yesterday) label = 'Вчера';
			else if (day >= weekAgo) label = 'На этой неделе';
			else {
				label = d.toLocaleString('ru-RU', { month: 'long', year: 'numeric' });
				label = label.charAt(0).toUpperCase() + label.slice(1);
			}
		}
		if (!groups.has(label)) groups.set(label, []);
		groups.get(label).push(t);
	}
	return groups;
}

export function formatThreadTime(iso, now = new Date()) {
	if (!iso) return '—';
	const d = new Date(iso);
	if (Number.isNaN(d.getTime())) return '—';
	if (d.toDateString() === now.toDateString()) {
		return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
	}
	return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
}

export function syncStatusLabel(status) {
	if (!status) return '';
	const parts = [];
	if (!status.auto_sync_enabled) {
		parts.push(
			status.account_count > 0
				? 'Фоновый синк выключен (EMAIL_AUTO_SYNC_MINUTES=0)'
				: 'Подключите почту для синхронизации'
		);
	} else {
		const mins = status.auto_sync_minutes ?? 5;
		const last = status.last_poll_at
			? new Date(status.last_poll_at).toLocaleString('ru-RU', {
					day: '2-digit',
					month: '2-digit',
					hour: '2-digit',
					minute: '2-digit',
				})
			: 'ещё не было';
		parts.push(`Синк: каждые ${mins} мин · последний ${last}`);
	}
	const bf = status.backfill;
	if (bf?.enabled && !bf.paused) {
		const acc = bf.accounts ? Object.values(bf.accounts) : [];
		const running = acc.find((a) => a.status === 'running');
		const totalImp = acc.reduce((s, a) => s + (a.total_imported || 0), 0);
		if (running) {
			parts.push(`Догрузка истории… +${totalImp} всего`);
		} else if (bf.done_count < acc.length && acc.length) {
			const cursor = acc.find((a) => a.status !== 'done')?.cursor_date;
			parts.push(`Догрузка истории: +${totalImp} писем${cursor ? ` · до ${cursor}` : ''}`);
		} else if (acc.length && bf.done_count === acc.length) {
			parts.push(`История загружена (+${totalImp})`);
		} else {
			parts.push('Догрузка истории включена');
		}
	}
	return parts.join(' · ');
}
