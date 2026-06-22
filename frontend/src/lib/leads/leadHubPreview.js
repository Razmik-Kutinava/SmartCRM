/** Превью для плиток хаба карточки лида. */
import { dealPathTotals, dealPathNextStep } from '$lib/leads/leadDealPathUi.js';
import { passportHasData } from '$lib/leads/leadPassport.js';
import { slaStatus } from '$lib/tasks/taskSla.js';

export const HUB_PANELS = [
	{ id: 'stages', icon: '📊', title: 'Стадии и документы', accent: 'indigo' },
	{ id: 'card', icon: '👤', title: 'Карточка клиента', accent: 'emerald' },
	{ id: 'activity', icon: '⚡', title: 'Действия и история', accent: 'violet' },
	{ id: 'passport', icon: '🛂', title: 'Паспорт компании', accent: 'sky' },
	{ id: 'tasks', icon: '✓', title: 'Задачи', accent: 'amber' },
	{ id: 'emails', icon: '✉️', title: 'Письма', accent: 'indigo' },
	{ id: 'agents', icon: '🤖', title: 'Агенты', accent: 'rose' },
];

export const PANEL_TITLES = Object.fromEntries(HUB_PANELS.map((p) => [p.id, p.title]));

/** @param {{ lead?: object, leadTasksList?: object[], leadComms?: object[], leadThreads?: object[], agentHistory?: object[] }} ctx */
export function buildHubTilePreviews(ctx) {
	const lead = ctx.lead || {};
	const tasks = ctx.leadTasksList || [];
	const comms = ctx.leadComms || [];
	const threads = ctx.leadThreads || [];

	const { done, total } = dealPathTotals(lead.dealPath);
	const next = dealPathNextStep(lead.dealPath);
	const openTasks = tasks.filter((t) => t.status !== 'done');
	const overdue = openTasks.filter((t) => {
		const s = slaStatus(t);
		return s.label === 'Просрочено' || s.label === 'Сегодня';
	}).length;

	const lastComm = comms[0]?.content || comms[0]?.body || '';
	const previews = {
		stages: {
			preview: next?.title ? `Следующий шаг: ${next.title}` : `Этап: ${lead.stage || '—'}`,
			meta: total > 0 ? `${lead.stage || '—'} · ${done}/${total} шагов` : lead.stage || '—',
		},
		card: {
			preview: [lead.contact, lead.phone !== '—' ? lead.phone : '', lead.email !== '—' ? lead.email : '']
				.filter(Boolean)
				.join(' · ') || 'Контакты и реквизиты',
			meta: lead.inn ? `ИНН ${lead.inn}` : lead.website !== '—' ? lead.website : '',
		},
		activity: {
			preview: lastComm ? String(lastComm).slice(0, 120) : 'Касания, комментарии, лента',
			meta: comms.length ? `${comms.length} записей в ленте` : 'Добавить касание',
		},
		passport: {
			preview: passportHasData(lead)
				? (lead.checko?.company?.okved_name || lead.industry || 'Данные Checko')
				: 'ИНН + ✨ Обогатить для паспорта',
			meta: lead.inn ? `ИНН ${lead.inn}` : 'Паспорт пуст',
		},
		tasks: {
			preview: openTasks[0]?.title || 'Задачи и SLA по лиду',
			meta: openTasks.length
				? `${openTasks.length} открыто${overdue ? ` · ${overdue} срочно` : ''}`
				: 'Нет открытых задач',
		},
		emails: {
			preview: threads[0]?.subject || (lead.email !== '—' ? lead.email : 'Переписка с клиентом'),
			meta: threads.length ? `${threads.length} тредов` : 'Написать письмо',
		},
		agents: {
			preview: 'Маркетолог, аналитик, стратег, экономист',
			meta: (ctx.agentHistory || []).length
				? `${ctx.agentHistory.length} запусков в истории`
				: 'Запуск по кнопке',
		},
	};

	return HUB_PANELS.map((tile) => ({
		...tile,
		preview: previews[tile.id]?.preview || '',
		meta: previews[tile.id]?.meta || '',
	}));
}
