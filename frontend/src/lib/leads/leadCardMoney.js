/** Суммы сделки на карточке лида (₽). */

export function parseMoneyInput(raw) {
	const t = String(raw ?? '').trim().replace(/\s/g, '').replace(',', '.');
	if (t === '') return null;
	const n = Number(t);
	return Number.isFinite(n) ? n : NaN;
}

export function moneyStringsFromLead(lead) {
	if (!lead) return { amount: '', paid: '' };
	const amount =
		lead.amountRub != null && lead.amountRub !== '' ? String(lead.amountRub) : '';
	const paid =
		lead.paidAmountRub != null && lead.paidAmountRub !== '' ? String(lead.paidAmountRub) : '';
	return { amount, paid };
}

/** @returns {{ amountRub: number | null, paidAmountRub: number | null }} */
export function buildMoneyPatch(amountStr, paidStr) {
	const a = parseMoneyInput(amountStr);
	const p = parseMoneyInput(paidStr);
	if (Number.isNaN(a) || Number.isNaN(p)) {
		throw new Error('Введите суммы числами (можно с десятичной точкой).');
	}
	return { amountRub: a, paidAmountRub: p };
}
