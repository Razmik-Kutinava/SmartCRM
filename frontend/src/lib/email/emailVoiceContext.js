/** Голос → папка и поиск на /email (зеркало: backend/voice/email_context.py). */

const FOLDER_BY_FILTER = {
	inbox: 'inbox',
	unread: 'inbox',
	all: 'inbox',
	sent: 'sent',
	outbound: 'sent',
	archive: 'archive',
	campaign: 'campaign',
	zoho: 'zoho',
};

/**
 * @param {string | null | undefined} filterValue
 */
export function emailFolderFromFilter(filterValue) {
	const key = String(filterValue || 'inbox').trim().toLowerCase();
	return FOLDER_BY_FILTER[key] || 'inbox';
}

/**
 * @param {Record<string, unknown> | null | undefined} payload
 */
export function voiceEmailContextFromPayload(payload) {
	if (!payload || typeof payload !== 'object') return null;
	const folder = payload.folder || emailFolderFromFilter(/** @type {string} */ (payload.filter));
	const hint = String(payload.hint || '').trim();
	const search = String(payload.search || '').trim();
	return { folder, hint, search };
}
