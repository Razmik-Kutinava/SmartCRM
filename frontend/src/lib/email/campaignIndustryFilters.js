/** Чекбоксы отраслей для массового сегмента */

export const WITHOUT_INDUSTRY_TOKEN = '__without_industry__';

/** @param {string[]} selected @param {string} name */
export function toggleIndustry(selected, name) {
	const set = new Set(selected);
	if (set.has(name)) set.delete(name);
	else set.add(name);
	return [...set];
}

/** @param {{ name: string, count?: number }[]} items */
export function selectIndustriesWithLeads(items) {
	return items.filter((it) => (it.count ?? 0) > 0).map((it) => it.name);
}

/** @param {number} withoutCount */
export function withWithoutIndustryToken(names, withoutCount, includeWithout) {
	const base = [...names];
	if (includeWithout && withoutCount > 0 && !base.includes(WITHOUT_INDUSTRY_TOKEN)) {
		base.push(WITHOUT_INDUSTRY_TOKEN);
	}
	return base;
}
