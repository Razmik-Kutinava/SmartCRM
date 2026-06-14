/** Фильтрация и группировка списка `/email` (зеркало: backend/tests/lib/test_email_list_logic.py). */

export const EMAIL_FOLDERS = [
	{ key: 'inbox', label: 'Входящие', icon: '📥' },
	{ key: 'sent', label: 'Отправленные', icon: '📤' },
	{ key: 'zoho', label: 'Zoho', icon: '🔷' },
	{ key: 'campaign', label: 'Рассылки', icon: '📣' },
	{ key: 'archive', label: 'Архив', icon: '🗂' },
];

const HIDDEN_IN_INBOX = new Set(['outbound', 'campaign', 'archive']);

export function filterEmailThreads(threads, { folder = 'inbox', search = '', accountId = null } = {}) {
	let list = Array.isArray(threads) ? [...threads] : [];
	if (accountId != null && accountId !== '') {
		list = list.filter((t) => t.accountId === accountId);
	}
	if (folder === 'inbox') {
		list = list.filter((t) => !HIDDEN_IN_INBOX.has(t.category) && !t.isArchived);
	} else if (folder === 'sent') {
		list = list.filter((t) => t.category === 'outbound');
	} else if (folder === 'zoho') {
		list = list.filter((t) => /zoho/i.test(`${t.subject || ''} ${t.snippet || ''}`));
	} else if (folder === 'campaign') {
		list = list.filter((t) => t.category === 'campaign');
	} else if (folder === 'archive') {
		list = list.filter((t) => t.isArchived);
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
	return list;
}

export function countEmailFolder(threads, folder) {
	return filterEmailThreads(threads, { folder, search: '' }).length;
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
	if (!status.auto_sync_enabled) {
		return status.account_count > 0
			? 'Фоновый синк выключен (EMAIL_AUTO_SYNC_MINUTES=0)'
			: 'Подключите почту для синхронизации';
	}
	const mins = status.auto_sync_minutes ?? 5;
	const last = status.last_poll_at
		? new Date(status.last_poll_at).toLocaleString('ru-RU', {
				day: '2-digit',
				month: '2-digit',
				hour: '2-digit',
				minute: '2-digit',
			})
		: 'ещё не было';
	return `Фоновый синк: каждые ${mins} мин · последний ${last}`;
}
