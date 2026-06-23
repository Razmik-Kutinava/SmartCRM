/** Суммы сделки на карточке лида (₽ и валюта Битрикс). */

export function parseMoneyInput(raw) {
	const t = String(raw ?? '').trim().replace(/\s/g, '').replace(',', '.');
	if (t === '') return null;
	const n = Number(t);
	return Number.isFinite(n) ? n : NaN;
}

/** @returns {{ amount: number | null, currency: string }} */
export function dealAmountFromLead(lead) {
	if (!lead) return { amount: null, currency: '' };
	const raw = lead.amount ?? lead.dealAmount;
	const currency = String(lead.currency ?? lead.dealCurrency ?? '').trim().toUpperCase();
	if (raw == null || raw === '') return { amount: null, currency };
	const n = Number(raw);
	return { amount: Number.isFinite(n) ? n : null, currency };
}

/** Подпись суммы сделки для шапки карточки: «15 780 USD». */
export function formatDealAmountLabel(lead) {
	const { amount, currency } = dealAmountFromLead(lead);
	if (amount == null || amount <= 0) {
		const budget = String(lead?.budget || '').trim();
		return budget && budget !== '—' ? budget : '';
	}
	const formatted = amount.toLocaleString('ru-RU', { maximumFractionDigits: 2 });
	return currency ? `${formatted} ${currency}` : formatted;
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
