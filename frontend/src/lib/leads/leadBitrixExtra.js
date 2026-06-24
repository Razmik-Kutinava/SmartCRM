/** Отображение bitrixExtra и сырых UF из tech_json. */

/** @type {Array<{ key: string, label: string }>} */
export const LICENSE_DISPLAY_FIELDS = [
	{ key: 'subscriptionEnd', label: 'Подписка до' },
	{ key: 'deliveryType', label: 'Тип поставки' },
	{ key: 'licenseTerm', label: 'Срок лицензии' },
	{ key: 'reservedUntil', label: 'Резерв до' },
	{ key: 'licenseRegistration', label: 'Licensing email' },
	{ key: 'sublicensee', label: 'Сублицензиат' },
	{ key: 'payerPartner', label: 'Плательщик / партнёр' },
	{ key: 'manager', label: 'Менеджер' },
	{ key: 'participant', label: 'Участник' },
];

function displayValue(val) {
	if (val == null || val === '' || val === false) return '';
	if (typeof val === 'boolean') return val ? 'Да' : '';
	return String(val).trim();
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function bitrixExtraFromLead(lead) {
	return lead?.bitrixExtra && typeof lead.bitrixExtra === 'object' ? lead.bitrixExtra : {};
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function licenseDisplayRows(lead) {
	const extra = bitrixExtraFromLead(lead);
	return LICENSE_DISPLAY_FIELDS.map(({ key, label }) => ({
		key,
		label,
		value: displayValue(extra[key]),
	})).filter((row) => row.value);
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function isRepeatLead(lead) {
	return Boolean(bitrixExtraFromLead(lead).isRepeatLead);
}

function formatUfValue(raw) {
	if (raw == null) return '';
	if (Array.isArray(raw)) {
		return raw
			.map((item) => {
				if (item && typeof item === 'object' && 'VALUE' in item) return String(item.VALUE ?? '');
				return String(item ?? '');
			})
			.filter(Boolean)
			.join(', ');
	}
	if (typeof raw === 'object') {
		const v = raw.VALUE ?? raw.value;
		return v != null ? String(v) : JSON.stringify(raw);
	}
	return String(raw);
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function rawBitrixUfEntries(lead) {
	const uf = lead?.tech?.bitrix24?.uf;
	if (!uf || typeof uf !== 'object') return [];
	return Object.entries(uf)
		.sort(([a], [b]) => a.localeCompare(b, 'ru'))
		.map(([key, value]) => ({ key, value: formatUfValue(value) }))
		.filter((row) => row.value);
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function licensePreviewText(lead) {
	const rows = licenseDisplayRows(lead);
	if (!rows.length) return '';
	const first = rows[0];
	return rows.length > 1 ? `${first.label}: ${first.value} (+${rows.length - 1})` : `${first.label}: ${first.value}`;
}
