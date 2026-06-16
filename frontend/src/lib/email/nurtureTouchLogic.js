/** Точечные касания — пресеты для UI /email */
export const NURTURE_TOUCH_COUNTS = [1, 3, 20];

export const NURTURE_PRODUCT_PRESETS = [
	'Positive Technologies MaxPatrol VM',
	'ManageEngine OpManager',
	'Positive Technologies MaxPatrol SIEM',
];

export const NURTURE_CHAIN_TYPES = [
	{ id: 'new', label: 'Новый продукт', hint: 'Первый контакт' },
	{ id: 'cross', label: 'Cross-sell', hint: 'Дополняющий продукт' },
	{ id: 'upsell', label: 'Upsell', hint: 'Расширение / апгрейд' },
];

export const DEFAULT_TEST_EMAIL = 'ib@agneko.com';

export function nurturePayloadBase(state) {
	return {
		lead_id: state.leadId,
		product_name: state.product,
		email_count: state.touchCount,
		chain_type: state.chainType || 'new',
		sender_name: state.senderName,
		sender_email: state.senderEmail,
		theme_mode: state.themeMode,
		subject_template: state.themeMode === 'manual' ? state.subjectTemplate : undefined,
		body_template: state.themeMode === 'manual' ? state.bodyTemplate : undefined,
	};
}

export function firstEmailForTest(previewEmails) {
	const list = previewEmails || [];
	return list[0] || null;
}
