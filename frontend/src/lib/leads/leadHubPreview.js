/** Превью для плиток хаба карточки лида. */
import { passportHasData } from '$lib/leads/leadPassport.js';
import { hubProductsPreview } from '$lib/leads/leadProducts.js';
import { licensePreviewText } from '$lib/leads/leadBitrixExtra.js';
import { slaStatus } from '$lib/tasks/taskSla.js';

/** 5 плиток: Клиент · Работа · Письма · Продукты · Агенты */
export const HUB_PANELS = [
	{ id: 'client', icon: '👤', title: 'Клиент', accent: 'emerald' },
	{ id: 'work', icon: '⚡', title: 'Работа', accent: 'violet' },
	{ id: 'emails', icon: '✉️', title: 'Письма', accent: 'indigo' },
	{ id: 'products', icon: '📦', title: 'Продукты', accent: 'emerald' },
	{ id: 'agents', icon: '🤖', title: 'Агенты', accent: 'rose' },
];

export const PANEL_TITLES = Object.fromEntries(HUB_PANELS.map((p) => [p.id, p.title]));

/** @param {{ lead?: object, leadTasksList?: object[], leadComms?: object[], leadThreads?: object[], agentHistory?: object[] }} ctx */
export function buildHubTilePreviews(ctx) {
	const lead = ctx.lead || {};
	const tasks = ctx.leadTasksList || [];
	const comms = ctx.leadComms || [];
	const threads = ctx.leadThreads || [];

	const openTasks = tasks.filter((t) => t.status !== 'done');
	const overdue = openTasks.filter((t) => {
		const s = slaStatus(t);
		return s.label === 'Просрочено' || s.label === 'Сегодня';
	}).length;

	const lastComm = comms[0]?.content || comms[0]?.body || '';
	const productsHub = hubProductsPreview(lead);
	const contactLine = [lead.contact, lead.phone !== '—' ? lead.phone : '', lead.email !== '—' ? lead.email : '']
		.filter(Boolean)
		.join(' · ');

	const previews = {
		client: {
			preview: contactLine || (passportHasData(lead) ? 'Паспорт заполнен' : 'Карточка и паспорт'),
			meta: [
				lead.inn ? `ИНН ${lead.inn}` : '',
				Array.isArray(lead.contacts) && lead.contacts.length ? `${lead.contacts.length} контакт(ов)` : '',
				licensePreviewText(lead),
				passportHasData(lead) ? 'паспорт ✓' : 'паспорт пуст',
			]
				.filter(Boolean)
				.join(' · ') || (lead.website !== '—' ? lead.website : ''),
		},
		work: {
			preview: openTasks[0]?.title || lastComm?.slice?.(0, 120) || 'История и задачи',
			meta: [
				openTasks.length ? `${openTasks.length} задач` : 'нет задач',
				overdue ? `${overdue} срочно` : '',
				comms.length ? `${comms.length} в ленте` : '',
			]
				.filter(Boolean)
				.join(' · '),
		},
		products: productsHub,
		emails: {
			preview: threads[0]?.subject || (lead.email !== '—' ? lead.email : 'Переписка и рассылка'),
			meta: threads.length ? `${threads.length} тредов` : 'Написать / цепочки',
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
