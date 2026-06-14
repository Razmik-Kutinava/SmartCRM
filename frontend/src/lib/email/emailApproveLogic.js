/** Превью и получатель для апрува отправки на /email. */

/**
 * @param {Array<{ direction?: string, sender?: string }>} messages
 */
export function replyRecipientFromMessages(messages) {
	const inbound = (messages || []).filter((m) => m.direction === 'inbound');
	const last = inbound[inbound.length - 1];
	return String(last?.sender || '').trim();
}

/**
 * @param {{ thread?: { subject?: string }, messages?: unknown[], body?: string }} opts
 */
export function buildReplyApprovePreview({ thread, messages, body }) {
	return {
		title: 'Отправить ответ?',
		kind: 'reply',
		to: replyRecipientFromMessages(/** @type {Array<{direction?: string, sender?: string}>} */ (messages)),
		subject: String(thread?.subject || '').trim(),
		body: String(body || '').trim(),
	};
}

/**
 * @param {{ to?: string, subject?: string, body?: string }} opts
 */
export function buildComposeApprovePreview({ to, subject, body }) {
	return {
		title: 'Отправить письмо?',
		kind: 'compose',
		to: String(to || '').trim(),
		subject: String(subject || '').trim(),
		body: String(body || '').trim(),
	};
}
