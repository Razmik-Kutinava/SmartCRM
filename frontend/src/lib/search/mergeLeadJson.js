/** Deep-merge checko/tech при enrich/research — не затирать UF Битрикс и паспорт. */

/**
 * @param {unknown} a
 * @param {unknown} b
 * @returns {Record<string, unknown>}
 */
export function isPlainObject(v) {
	return Boolean(v) && typeof v === 'object' && !Array.isArray(v);
}

/**
 * Глубокий merge объектов. Массивы: если оба — берём longer / union для phones/emails.
 * @param {Record<string, unknown>} base
 * @param {Record<string, unknown>} overlay
 */
export function deepMergeObjects(base, overlay) {
	const out = { ...(isPlainObject(base) ? base : {}) };
	if (!isPlainObject(overlay)) return out;
	for (const [key, val] of Object.entries(overlay)) {
		if (val === undefined) continue;
		const prev = out[key];
		if (isPlainObject(prev) && isPlainObject(val)) {
			out[key] = deepMergeObjects(prev, val);
		} else if (Array.isArray(prev) && Array.isArray(val)) {
			if (key === 'phones' || key === 'emails') {
				const merged = [...prev];
				for (const item of val) {
					if (item != null && !merged.includes(item)) merged.push(item);
				}
				out[key] = merged;
			} else {
				out[key] = val.length >= prev.length ? val : prev;
			}
		} else if (val !== null && val !== '') {
			out[key] = val;
		} else if (!(key in out)) {
			out[key] = val;
		}
	}
	return out;
}

/**
 * checkoJson: lead + passport, сохраняем company/financials/analyses.
 * @param {unknown} existing
 * @param {unknown} incoming
 */
export function mergeCheckoJson(existing, incoming) {
	const base = isPlainObject(existing) ? existing : {};
	const over = isPlainObject(incoming) ? incoming : {};
	if (!Object.keys(over).length) return { ...base };
	return deepMergeObjects(base, over);
}

/**
 * techJson: BuiltWith поверх, bitrix24.uf никогда не сносить.
 * @param {unknown} existing
 * @param {unknown} incoming
 */
export function mergeTechJson(existing, incoming) {
	const base = isPlainObject(existing) ? { ...existing } : {};
	const over = isPlainObject(incoming) ? { ...incoming } : {};
	if (!Object.keys(over).length) return base;

	const merged = deepMergeObjects(base, over);
	// Жёстко: bitrix24 из existing, если overlay его не принёс целиком
	if (isPlainObject(base.bitrix24)) {
		if (!isPlainObject(over.bitrix24)) {
			merged.bitrix24 = base.bitrix24;
		} else {
			merged.bitrix24 = deepMergeObjects(base.bitrix24, over.bitrix24);
			if (isPlainObject(base.bitrix24.uf) && !isPlainObject(over.bitrix24.uf)) {
				merged.bitrix24 = { ...merged.bitrix24, uf: base.bitrix24.uf };
			} else if (isPlainObject(base.bitrix24.uf) && isPlainObject(over.bitrix24.uf)) {
				merged.bitrix24 = {
					...merged.bitrix24,
					uf: deepMergeObjects(base.bitrix24.uf, over.bitrix24.uf),
				};
			}
		}
	}
	return merged;
}
