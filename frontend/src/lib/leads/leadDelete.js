/** Подтверждение и удаление лида (список + карточка). */

import { apiDeleteLead, readLeadsCache, writeLeadsCache } from '$lib/leadsStorage.js';

/**
 * @param {{ id: number, company?: string }} lead
 * @returns {Promise<boolean>} true если удалён
 */
export async function confirmAndDeleteLead(lead) {
	if (!lead?.id) return false;
	const name = lead.company || `#${lead.id}`;
	if (!confirm(`Удалить лид «${name}» из базы? Это действие нельзя отменить.`)) {
		return false;
	}
	await apiDeleteLead(lead.id);
	const next = readLeadsCache().filter((l) => l.id !== lead.id);
	writeLeadsCache(next);
	return true;
}
