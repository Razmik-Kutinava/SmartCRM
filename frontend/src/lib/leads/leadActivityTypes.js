/** Типы действий по лиду (единая форма касаний / комментариев / заметок). */
export const ACTIVITY_TYPES = [
	{ value: 'call', label: 'Звонок', channel: 'communication' },
	{ value: 'email', label: 'Письмо', channel: 'communication' },
	{ value: 'vks', label: 'ВКС / онлайн-встреча', channel: 'communication' },
	{ value: 'meeting_offline', label: 'Личная встреча', channel: 'communication' },
	{ value: 'other', label: 'Другое', channel: 'communication' },
	{ value: 'comment', label: 'Комментарий', channel: 'communication' },
	{ value: 'note', label: 'Заметка', channel: 'communication' },
];

/** @deprecated — используй ACTIVITY_TYPES */
export const COMMUNICATION_TYPES = ACTIVITY_TYPES.filter((t) => t.channel === 'communication');

/** @type {Record<string, string>} */
const LABELS = Object.fromEntries(ACTIVITY_TYPES.map((t) => [t.value, t.label]));

/** @param {string} type */
export function activityTypeLabel(type) {
	return LABELS[type] || type;
}

/** @param {string} type */
export function communicationTypeLabel(type) {
	return activityTypeLabel(type);
}
