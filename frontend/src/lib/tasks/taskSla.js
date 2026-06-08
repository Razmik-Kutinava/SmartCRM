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
