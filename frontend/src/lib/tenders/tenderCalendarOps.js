const API = '';

export async function fetchTenderCalendarMonth(year, month) {
	const r = await fetch(`${API}/api/tenders/calendar/month?year=${year}&month=${month}`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function fetchTenderNotifications(unreadOnly = false) {
	const q = unreadOnly ? '?unread_only=true' : '';
	const r = await fetch(`${API}/api/tenders/notifications${q}`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function markTenderNotificationsRead({ notificationId = null, all = false } = {}) {
	const r = await fetch(`${API}/api/tenders/notifications/read`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			notification_id: notificationId,
			all
		})
	});
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function scanTenderDeadlines() {
	const r = await fetch(`${API}/api/tenders/calendar/scan-deadlines`, { method: 'POST' });
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}
