/** Продукты лида — сводка для хаба и панели. */
export const PRODUCT_STATUS_LABELS = {
	sold: 'Продано',
	pipeline: 'В продаже',
	owned: 'Есть у клиента',
};

/** @param {Array<Record<string, unknown>>} products */
export function leadProductsSummary(products) {
	const rows = Array.isArray(products) ? products : [];
	let sold = 0;
	let pipeline = 0;
	let owned = 0;
	for (const p of rows) {
		const st = String(p.status || '');
		if (st === 'sold') sold += 1;
		else if (st === 'pipeline') pipeline += 1;
		else if (st === 'owned') owned += 1;
	}
	return { sold, pipeline, owned, total: rows.length };
}

/** @param {number | null | undefined} price @param {string} [currency] */
export function formatProductPrice(price, currency = 'RUB') {
	if (price == null || !Number.isFinite(Number(price))) return '—';
	const n = Number(price);
	const cur = String(currency || 'RUB').toUpperCase();
	const formatted = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(n);
	if (cur === 'RUB' || cur === 'RUR') return `${formatted} ₽`;
	return `${formatted} ${cur}`;
}

/** @param {Array<Record<string, unknown>>} products @param {string} status */
export function productsByStatus(products, status) {
	return (products || []).filter((p) => String(p.status || '') === status);
}

/** @param {object} lead */
export function leadProductsFromLead(lead) {
	if (Array.isArray(lead?.leadProducts) && lead.leadProducts.length) {
		return lead.leadProducts;
	}
	const legacy = lead?.productsOwned || lead?.products_owned;
	if (!Array.isArray(legacy)) return [];
	return legacy.map((name) => ({
		name: String(name),
		status: 'owned',
		price: null,
		currency: 'RUB',
		quantity: 1,
		source: 'legacy',
	}));
}

/** @param {object} lead */
export function hubProductsPreview(lead) {
	const products = leadProductsFromLead(lead);
	const s = leadProductsSummary(products);
	if (!s.total) return { preview: 'Нет данных о продуктах', meta: 'Импорт из Битрикс или ручной ввод' };
	const top = products[0];
	const price = top?.price != null ? formatProductPrice(top.price, top.currency) : '';
	const preview = price ? `${top.name} · ${price}` : String(top?.name || 'Продукты');
	const parts = [];
	if (s.sold) parts.push(`${s.sold} продано`);
	if (s.pipeline) parts.push(`${s.pipeline} в продаже`);
	if (s.owned) parts.push(`${s.owned} у клиента`);
	return {
		preview,
		meta: parts.length ? parts.join(' · ') : `${s.total} поз.`,
	};
}
