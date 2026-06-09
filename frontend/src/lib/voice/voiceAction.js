/** voice_action: store + диспетчер UI-реакций (ARCHITECTURE.md). */
import { get, writable } from 'svelte/store';

/** @type {import('svelte/store').Writable<Record<string, unknown> | null>} */
export const voiceModal = writable(null);

/** @type {import('svelte/store').Writable<Record<string, unknown> | null>} */
export const voiceApprove = writable(null);

/** @type {import('svelte/store').Writable<Record<string, string> | null>} */
export const voiceLeadFilter = writable(null);

/** Колбэк страницы лидов для CRUD после апрува */
let _leadIntentHandler = null;

/** @param {(data: Record<string, unknown>) => void | Promise<void>} fn */
export function registerLeadIntentHandler(fn) {
	_leadIntentHandler = fn;
}

/** @param {Record<string, unknown>} data */
export function dispatchLeadIntent(data) {
	_leadIntentHandler?.(data);
}

/**
 * @param {Record<string, unknown>} action
 * @param {{ goto: (url: string) => void }} nav
 */
export function handleVoiceAction(action, { goto }) {
	if (!action || action.type !== 'voice_action') return;

	const ui = String(action.ui || '');

	if (ui === 'navigate' && action.route) {
		goto(String(action.route));
		return;
	}

	if (ui === 'filter') {
		const filt = action.payload?.filter || action.payload;
		if (filt && typeof filt === 'object') {
			voiceLeadFilter.set(/** @type {Record<string, string>} */ (filt));
		}
		if (action.route) goto(String(action.route));
		return;
	}

	if (ui === 'modal') {
		if (action.route) goto(String(action.route));
		voiceModal.set(action);
		return;
	}

	if (ui === 'approve') {
		voiceApprove.set(action);
	}
}

/** @param {'confirm' | 'reject'} decision */
export function resolveVoiceApprove(decision) {
	const cur = get(voiceApprove);
	voiceApprove.set(null);
	if (!cur || decision === 'reject') return;
	const payload = cur.payload || {};
	dispatchLeadIntent({
		intent: payload.intent,
		slots: payload.slots || {},
		reply: cur.reply || '',
		fromApprove: true,
	});
}

export function closeVoiceModal() {
	voiceModal.set(null);
}
