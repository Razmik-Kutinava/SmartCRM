/** Фильтры сегментов полноты карточки — зеркало core/lead_coverage.py */
export const COVERAGE_FILTERS = [
	{ id: 'all', label: 'Все' },
	{ id: 'card_ready', label: 'Карточка готова' },
	{ id: 'bitrix_full', label: 'B24 полный' },
	{ id: 'bitrix_partial', label: 'B24 частично' },
	{ id: 'bitrix_empty', label: 'B24 пусто' },
	{ id: 'passport', label: 'Паспорт' },
	{ id: 'empty', label: 'Пустые' },
	{ id: 'lost', label: 'Проигран' },
	{ id: 'no_tasks', label: 'Без дел' },
];

export function leadMatchesCoverageFilter(lead, filterId) {
	if (!filterId || filterId === 'all') return true;
	const segs = lead?.coverageSegments || [];
	return segs.includes(filterId);
}
