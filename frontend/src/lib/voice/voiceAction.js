/** voice_action: store + диспетчер UI-реакций (ARCHITECTURE.md). */
import { get, writable } from 'svelte/store';

/** @type {import('svelte/store').Writable<Record<string, unknown> | null>} */
export const voiceModal = writable(null);

/** @type {import('svelte/store').Writable<Record<string, unknown> | null>} */
export const voiceApprove = writable(null);

/** @type {import('svelte/store').Writable<Record<string, string> | null>} */
export const voiceLeadFilter = writable(null);

/** Контекст аналитики с голоса: period, source, intent */
export const voiceAnalyticsContext = writable(null);

/** Поисковый запрос для /search */
export const voiceSearchQuery = writable(null);

/** Краткое уведомление после voice_action */
export const voiceToast = writable(null);

/** @type {import('svelte/store').Writable<{ text: string, until: number } | null>} */
export const voiceHighlight = writable(null);

/** @type {Record<string, (action: Record<string, unknown>) => void | Promise<void>>} */
const _approveHandlers = {};

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
 * @param {string} intent
 * @param {(action: Record<string, unknown>) => void | Promise<void>} fn
 */
export function registerVoiceApproveHandler(intent, fn) {
	_approveHandlers[intent] = fn;
}

const PERIOD_LABELS = {
	week: 'неделя',
	month: 'месяц',
	quarter: 'квартал',
	year: 'год',
	last_year: 'прошлый год',
};

function flashHighlight(text) {
	if (!text) return;
	const until = Date.now() + 5000;
	voiceHighlight.set({ text, until });
	setTimeout(() => {
		const cur = get(voiceHighlight);
		if (cur?.until === until) voiceHighlight.set(null);
	}, 5200);
}

function applyAnalyticsPayload(action) {
	const payload = action.payload || {};
	const period = payload.period || action.slots?.period;
	const source = payload.source || action.slots?.source;
	if (!period && !source && !action.intent?.startsWith?.('analytics_')) return;
	voiceAnalyticsContext.set({
		period: period ? String(period) : '',
		periodLabel: PERIOD_LABELS[String(period)] || String(period || ''),
		source: source ? String(source) : '',
		intent: String(action.intent || ''),
		title: String(action.title || ''),
	});
}

/**
 * @param {Record<string, unknown>} action
 * @param {{ goto: (url: string) => void }} nav
 */
export function handleVoiceAction(action, { goto }) {
	if (!action || action.type !== 'voice_action') return;

	const ui = String(action.ui || '');
	const intent = String(action.intent || '');

	if (ui === 'navigate' && action.route) {
		applyAnalyticsPayload(action);
		const route = String(action.route);
		if (intent === 'search_web' && action.slots?.query && !route.includes('?')) {
			goto(`${route}?q=${encodeURIComponent(String(action.slots.query))}`);
		} else {
			goto(route);
		}
		if (action.slots?.query) voiceSearchQuery.set(String(action.slots.query));
		flashHighlight(action.title || 'Переход по голосу');
		return;
	}

	if (ui === 'filter') {
		const filt = action.payload?.filter || action.payload;
		if (filt && typeof filt === 'object') {
			voiceLeadFilter.set(/** @type {Record<string, string>} */ (filt));
		}
		if (action.route) goto(String(action.route));
		const minSc = filt?.minScore;
		flashHighlight(
			minSc
				? `Фильтр: скор ≥ ${minSc}`
				: action.title || 'Фильтр списка лидов',
		);
		return;
	}

	if (ui === 'modal') {
		applyAnalyticsPayload(action);
		if (action.route) goto(String(action.route));
		if (action.slots?.query) voiceSearchQuery.set(String(action.slots.query));
		voiceModal.set(action);
		return;
	}

	if (ui === 'approve') {
		voiceApprove.set(action);
		if (action.route && intent === 'send_email') {
			// не уходим сразу — ждём confirm
		} else if (action.route && intent === 'save_to_rag') {
			// modal approve only
		}
	}
}

/** @param {'confirm' | 'reject'} decision */
export async function resolveVoiceApprove(decision) {
	const cur = get(voiceApprove);
	voiceApprove.set(null);
	if (!cur || decision === 'reject') return;

	const payload = /** @type {Record<string, unknown>} */ (cur.payload || {});
	const intent = String(payload.intent || cur.intent || '');

	const handler = _approveHandlers[intent];
	if (handler) {
		try {
			await handler(cur);
		} catch (e) {
			voiceToast.set(e?.message || String(e));
		}
		return;
	}

	dispatchLeadIntent({
		intent,
		slots: payload.slots || {},
		reply: cur.reply || '',
		fromApprove: true,
	});
}

export function closeVoiceModal() {
	voiceModal.set(null);
}
