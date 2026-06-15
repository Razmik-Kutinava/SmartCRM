/** Ф3: голосовой follow-up — да / нет / короче. */
import { get } from 'svelte/store';
import {
	voiceApprove,
	voiceModal,
	resolveVoiceApprove,
	voiceToast,
} from './voiceAction.js';
import { reviseVoiceDraft } from './voiceReviseDraft.js';

const CONFIRM_RE =
	/\b(да|давай|ок|окей|подтверждаю|отправляй|отправь|согласен|согласна|подтверди|yes|confirm)\b/i;
const REJECT_RE = /\b(нет|отмена|отмени|стоп|не надо|не нужно|cancel|reject|отклон)\b/i;
const REVISE_RE = /\b(переделай|короче|сократи|укороти|кратче|сократи текст|shorter)\b/i;

/** @param {string} text */
export function parseVoiceFollowup(text) {
	const t = String(text || '').trim();
	if (!t) return null;
	if (REJECT_RE.test(t)) return 'reject';
	if (REVISE_RE.test(t)) return 'revise';
	if (CONFIRM_RE.test(t)) return 'confirm';
	return null;
}

/** @param {string} text @returns {Promise<boolean>} */
export async function tryHandleVoiceFollowup(text) {
	const decision = parseVoiceFollowup(text);
	if (!decision) return false;

	const approve = get(voiceApprove);
	const modal = get(voiceModal);

	if (decision === 'revise') {
		const target = modal || approve;
		if (!target) return false;
		const draft = target.payload?.draft_email;
		const reply = target.payload?.reply || target.reply;
		if (!draft && !reply) return false;
		try {
			const revised = await reviseVoiceDraft({
				subject: draft?.subject || '',
				body: draft?.body || String(reply || ''),
			});
			if (modal) {
				voiceModal.set({
					...modal,
					payload: {
						...modal.payload,
						draft_email: revised,
						revised: true,
					},
				});
			} else if (approve) {
				voiceApprove.set({
					...approve,
					payload: {
						...approve.payload,
						draft_email: revised,
						revised: true,
					},
				});
			}
			voiceToast.set('Черновик сокращён — скажите «да» или нажмите Подтвердить');
			return true;
		} catch (e) {
			voiceToast.set(e?.message || String(e));
			return true;
		}
	}

	if (approve) {
		if (decision === 'confirm') {
			await resolveVoiceApprove('confirm');
			voiceToast.set('Подтверждено голосом');
		} else {
			await resolveVoiceApprove('reject');
			voiceToast.set('Отменено голосом');
		}
		return true;
	}

	return false;
}

/** Есть ли ожидающий апрув или черновик для follow-up. */
export function hasVoiceFollowupContext() {
	const approve = get(voiceApprove);
	const modal = get(voiceModal);
	if (approve) return true;
	if (!modal) return false;
	return Boolean(modal.payload?.draft_email || modal.payload?.reply);
}
