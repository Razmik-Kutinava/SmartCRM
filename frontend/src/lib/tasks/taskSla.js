/** Статус SLA задачи (зеркало backend/core/task_dates.py). */

export function parseTaskDue(raw) {
	if (!raw || raw === '—') return null;
	const m = String(raw).match(/(\d{1,2})\.(\d{1,2})\.(\d{4})/);
	if (m) {
		const [, dd, mm, yyyy] = m;
		return new Date(Number(yyyy), Number(mm) - 1, Number(dd));
	}
	const iso = String(raw).match(/^(\d{4})-(\d{2})-(\d{2})/);
	if (iso) {
		return new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3]));
	}
	return null;
}

export function slaStatus(task) {
	if (task.status === 'done') return { key: 'done', label: 'Готово', cls: 'text-gray-500' };
	const sla = task.slaDue || task.sla_due;
	if (!sla) return { key: 'no_sla', label: 'SLA не задан', cls: 'text-gray-600' };
	const dt = parseTaskDue(sla);
	if (!dt) return { key: 'unknown', label: `SLA: ${sla}`, cls: 'text-gray-400' };
	const now = new Date();
	now.setHours(0, 0, 0, 0);
	dt.setHours(0, 0, 0, 0);
	if (dt < now) return { key: 'overdue', label: 'Просрочено', cls: 'text-red-400 font-medium' };
	if (dt.getTime() === now.getTime()) return { key: 'today', label: 'Сегодня', cls: 'text-yellow-400' };
	return { key: 'ok', label: 'В срок', cls: 'text-green-400' };
}

/** Бейдж срока задачи в списке */
export function taskDueBadge(task) {
	if (task.status === 'done') {
		return { label: 'Выполнено', cls: 'bg-gray-700/80 text-gray-400' };
	}
	const sla = slaStatus(task);
	if (sla.key === 'overdue') {
		return { label: 'Просрочено', cls: 'bg-red-900/60 text-red-300' };
	}
	if (sla.key === 'today') {
		return { label: 'Сегодня', cls: 'bg-yellow-900/50 text-yellow-300' };
	}
	const due = parseTaskDue(task.due);
	if (due) {
		const now = new Date();
		now.setHours(0, 0, 0, 0);
		due.setHours(0, 0, 0, 0);
		if (due < now) return { label: 'Просрочено', cls: 'bg-red-900/60 text-red-300' };
		if (due.getTime() === now.getTime()) {
			return { label: 'Сегодня', cls: 'bg-yellow-900/50 text-yellow-300' };
		}
	}
	return null;
}
