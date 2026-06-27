/** Типы дел для dropdown (синхрон с backend/core/lead_task_intents.py). */
export const TASK_INTENT_OPTIONS = [
	{ id: '', label: '— Авто по тексту —', tier: '' },
	{ id: 'kp_followup', label: 'Ответ на КП', tier: 'A' },
	{ id: 'kp_send', label: 'Отправить КП', tier: 'A' },
	{ id: 'renewal', label: 'Продление / подписка', tier: 'A' },
	{ id: 'procurement_status', label: 'Согласование закупки', tier: 'A' },
	{ id: 'legal_check', label: 'Чек от легала', tier: 'A' },
	{ id: 'wait_client', label: 'Жду ответ клиента', tier: 'B' },
	{ id: 'email_reply', label: 'Написать / ответить письмом', tier: 'B' },
	{ id: 'call', label: 'Перезвонить', tier: 'B' },
	{ id: 'meeting', label: 'Встреча / ВКС / демо', tier: 'B' },
	{ id: 'vendor_letter', label: 'Письмо вендору / техподдержка', tier: 'B' },
	{ id: 'price_brief', label: 'Прайс / бриф / запрос', tier: 'B' },
	{ id: 'reactivation', label: 'Возобновить работу', tier: 'B' },
	{ id: 'trial_request', label: 'Триалка', tier: 'C' },
	{ id: 'testing', label: 'Тестирование', tier: 'C' },
	{ id: 'find_contacts', label: 'Найти контакты', tier: 'D' },
	{ id: 'mailing', label: 'Рассылка', tier: 'D' },
	{ id: 'application_review', label: 'Просмотр заявки', tier: 'D' },
	{ id: 'version_reminder', label: 'Напоминание (версия / как дела)', tier: 'D' },
	{ id: 'other', label: 'Другое', tier: 'B' },
];

export function taskIntentLabel(intentId) {
	const id = String(intentId || '').trim();
	if (!id) return '';
	const row = TASK_INTENT_OPTIONS.find((o) => o.id === id);
	return row?.label || id;
}
