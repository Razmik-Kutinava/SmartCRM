/** Обработчики approve для voice_action (email, RAG). */
import { apiPost } from '$lib/api.js';
import { sendEmail, replyToEmail } from '$lib/emailStorage.js';

/**
 * @param {Record<string, unknown>} action
 * @returns {Promise<{ ok: boolean, message: string, gotoUrl?: string }>}
 */
export async function handleSendEmailApprove(action) {
	const payload = /** @type {Record<string, unknown>} */ (action.payload || {});
	const slots = /** @type {Record<string, unknown>} */ (payload.slots || action.slots || {});
	const draft = /** @type {{ subject?: string, body?: string } | undefined} */ (payload.draft_email);
	const body = String(draft?.body || slots.body || slots.content || '').trim();
	const threadId = slots.thread_id ?? slots.threadId;

	if (threadId && body) {
		try {
			await replyToEmail({ thread_id: Number(threadId), body });
			return { ok: true, message: 'Ответ в переписке отправлен' };
		} catch (e) {
			return { ok: false, message: e?.message || String(e) };
		}
	}

	const to = String(slots.target || slots.to || slots.email || '').trim();
	const subject = String(draft?.subject || slots.subject || 'Письмо из SmartCRM');

	if (!to) {
		return {
			ok: false,
			message: 'Откройте почту и укажите получателя',
			gotoUrl: `/email?${new URLSearchParams({ subject, body }).toString()}`,
		};
	}

	try {
		await sendEmail({ to: [to], subject, body });
		return { ok: true, message: `Письмо отправлено: ${to}` };
	} catch (e) {
		return { ok: false, message: e?.message || String(e) };
	}
}

/**
 * @param {Record<string, unknown>} action
 */
export async function handleSaveToRagApprove(action) {
	const payload = /** @type {Record<string, unknown>} */ (action.payload || {});
	const slots = /** @type {Record<string, unknown>} */ (payload.slots || action.slots || {});
	const text = String(slots.content || slots.question || action.reply || '').trim();
	if (!text) throw new Error('Нет текста для сохранения в RAG');

	const r = await apiPost('/api/rag/ingest', {
		title: `voice-${new Date().toISOString().slice(0, 19)}`,
		text,
		tags: 'voice',
		for_agent: 'all',
	});
	if (!r.ok) {
		const detail = await r.text().catch(() => '');
		throw new Error(detail || `HTTP ${r.status}`);
	}
	const data = await r.json();
	return {
		ok: true,
		message: `Сохранено в RAG: ${data.chunks ?? 0} чанков`,
	};
}
