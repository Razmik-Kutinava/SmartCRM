/** Подписи breakdown scoreAdvisory для UI карточки лида. */
const LABELS = {
	stage: 'Этап',
	managerScore: 'Балл менеджера',
	baseFromStage: 'База по этапу',
	amountBonus: 'Бонус за сумму ₽',
	approvalBonus: 'Бонус за апрувы',
	overduePenalty: 'Штраф за просрочки',
	overdueOpenTasks: 'Просроченных задач',
	escalatedOpenTasks: 'Эскалированных задач',
	suggestedScore: 'Итого подсказка',
};

/** @param {Record<string, unknown>} breakdown */
export function formatScoreBreakdownLines(breakdown) {
	if (!breakdown || typeof breakdown !== 'object') return [];
	const lines = [];
	for (const [key, label] of Object.entries(LABELS)) {
		if (breakdown[key] == null) continue;
		if (key === 'approvalDetails') continue;
		let val = breakdown[key];
		if (key === 'overduePenalty' || key === 'amountBonus' || key === 'approvalBonus') {
			const sign = key === 'overduePenalty' ? '−' : '+';
			lines.push({ label, value: `${sign}${val}` });
			continue;
		}
		lines.push({ label, value: String(val) });
	}
	const ap = breakdown.approvalDetails;
	if (ap && typeof ap === 'object' && Object.keys(ap).length) {
		lines.push({
			label: 'Апрувы',
			value: Object.entries(ap)
				.map(([k, v]) => `${k}: +${v}`)
				.join(', '),
		});
	}
	return lines;
}
