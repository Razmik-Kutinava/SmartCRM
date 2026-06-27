/** Разбор тела письма — убрать цитаты, нормализовать абзацы (зеркало: backend/tests/lib/test_email_thread_body.py). */

const QUOTE_PATTERNS = [
	/\n-{5,}\s*\n/,
	/\nКому:\s*.+[\s\S]{0,200}Тема:\s*.+[\s\S]{0,80}\d{1,2}\.\d{2}\.\d{4}/i,
	/\nFrom:\s*.+\n(Sent|Date):/i,
	/\nОт:\s*.+\n(Отправлено|Дата):/i,
	/\nOn .+ wrote:\s*\n/i,
	/\n-{3,}\s*Original Message\s*-{3,}/i,
	/\n_{3,}\s*\n/,
];

/**
 * Оставляет только «верх» письма — без цепочки ответов ниже разделителя.
 */
export function stripQuotedEmailBody(body) {
	let text = String(body || '').replace(/\r\n/g, '\n').trim();
	if (!text) return '';

	let cutAt = text.length;
	for (const re of QUOTE_PATTERNS) {
		const m = re.exec(text);
		if (m && m.index >= 20 && m.index < cutAt) cutAt = m.index;
	}
	text = text.slice(0, cutAt).trim();

	const sig = text.search(/\n--\s*\n/);
	if (sig > 40) text = text.slice(0, sig).trim();

	return text.replace(/\n{3,}/g, '\n\n').trim();
}

/** Абзацы для отображения (после strip). */
export function emailBodyParagraphs(body) {
	const clean = stripQuotedEmailBody(body);
	if (!clean) return [];
	return clean.split(/\n\n+/).map((p) => p.replace(/\n/g, ' ').trim()).filter(Boolean);
}

/** Однострочный snippet для сайдбара треда. */
export function emailMessageSnippet(body, maxLen = 72) {
	const clean = stripQuotedEmailBody(body) || String(body || '');
	const one = clean.replace(/\s+/g, ' ').trim();
	if (one.length <= maxLen) return one;
	return `${one.slice(0, maxLen - 1)}…`;
}

/** Сортировка сообщений: старые → новые. */
export function sortThreadMessages(messages) {
	return [...(messages || [])].sort((a, b) => {
		const da = a.sentAt ? new Date(a.sentAt).getTime() : 0;
		const db = b.sentAt ? new Date(b.sentAt).getTime() : 0;
		if (da !== db) return da - db;
		return (a.id || 0) - (b.id || 0);
	});
}

export function formatMessageDateShort(iso) {
	if (!iso) return '—';
	const d = new Date(iso);
	if (Number.isNaN(d.getTime())) return '—';
	return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

export function formatMessageDateFull(iso) {
	if (!iso) return '—';
	const d = new Date(iso);
	if (Number.isNaN(d.getTime())) return '—';
	return d.toLocaleString('ru-RU', {
		day: 'numeric',
		month: 'long',
		hour: '2-digit',
		minute: '2-digit',
	});
}

export function senderDisplayName(sender) {
	const s = String(sender || '').trim();
	if (!s) return '—';
	const namePart = s.replace(/<[^>]+>/, '').trim();
	if (namePart) return namePart;
	const m = s.match(/<([^>]+)>/);
	return m ? m[1] : s;
}

export function senderEmail(sender) {
	const s = String(sender || '');
	const m = s.match(/<([^>]+)>/);
	if (m) return m[1];
	if (s.includes('@')) return s.trim();
	return '';
}
