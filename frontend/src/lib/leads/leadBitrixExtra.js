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

/** @param {string} raw */
export function parseSubscriptionDate(raw) {
	const s = String(raw || '').trim();
	if (!s) return null;
	let m = s.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})/);
	if (m) return new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
	m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
	if (m) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
	return null;
}

function startOfDay(d) {
	return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function subscriptionEndFromLead(lead) {
	return String(bitrixExtraFromLead(lead).subscriptionEnd || '').trim();
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function deliveryTypeFromLead(lead) {
	return String(bitrixExtraFromLead(lead).deliveryType || '').trim();
}

/**
 * Статус подписки для списка лидов.
 * @param {Record<string, unknown> | null | undefined} lead
 * @param {Date} [now]
 */
export function subscriptionStatus(lead, now = new Date()) {
	const label = subscriptionEndFromLead(lead);
	const parsed = parseSubscriptionDate(label);
	if (!parsed) return { kind: 'none', label: '', cls: '', days: null };
	const today = startOfDay(now);
	const end = startOfDay(parsed);
	const diffDays = Math.round((end.getTime() - today.getTime()) / 86400000);
	if (diffDays < 0) {
		return {
			kind: 'expired',
			label,
			cls: 'text-red-300 bg-red-950/60 border-red-900/50',
			days: diffDays,
		};
	}
	if (diffDays <= 30) {
		return {
			kind: 'expiring',
			label,
			cls: 'text-amber-300 bg-amber-950/50 border-amber-900/40',
			days: diffDays,
		};
	}
	return {
		kind: 'ok',
		label,
		cls: 'text-gray-400 bg-gray-900/50 border-gray-800',
		days: diffDays,
	};
}

/** Бейдж «подписка до» для строки списка. */
export function subscriptionBadgeForLead(lead, now = new Date()) {
	const st = subscriptionStatus(lead, now);
	if (!st.label) return null;
	return st;
}
