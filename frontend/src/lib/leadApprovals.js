/** Чеклист апрувов/документов (camelCase) — синхрон с backend/core/lead_approvals.py */

export const APPROVAL_KEYS = [
	'lprEstablished',
	'assortmentAgreed',
	'priceAgreed',
	'termsAgreed',
	'paymentTermsAgreed',
	'securityPassed',
	'rebateAgreed',
	'contractSigned',
	'invoiceIssued',
	'contractSent',
	'contractSignedDoc',
	'kpSent',
	'presentationSent',
	'licenseShipped',
];

/** @type {Record<string, string>} */
export const APPROVAL_LABELS_RU = {
	lprEstablished: 'ЛПР установлен',
	assortmentAgreed: 'Ассортимент согласован',
	priceAgreed: 'Цена согласована',
	termsAgreed: 'Условия согласованы',
	paymentTermsAgreed: 'Условия оплаты согласованы',
	securityPassed: 'Пройден security',
	rebateAgreed: 'Скидка согласована',
	contractSigned: 'Договор подписан (факт)',
	invoiceIssued: 'Счёт выставлен',
	contractSent: 'Договор отправлен',
	contractSignedDoc: 'Подписанный договор (документ)',
	kpSent: 'КП отправлено',
	presentationSent: 'Презентация отправлена',
	licenseShipped: 'Лицензия отгружена',
};

export function defaultApprovals() {
	return Object.fromEntries(APPROVAL_KEYS.map((k) => [k, false]));
}

/** @param {Record<string, boolean>|null|undefined} patch */
export function mergeApprovals(base, patch) {
	const out = { ...defaultApprovals(), ...base };
	if (patch && typeof patch === 'object') {
		for (const k of APPROVAL_KEYS) {
			if (k in patch) out[k] = Boolean(patch[k]);
		}
	}
	return out;
}
