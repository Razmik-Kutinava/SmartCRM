/** Массовая рассылка — сегмент и пресеты (этап B) */
import { NURTURE_PRODUCT_PRESETS, DEFAULT_TEST_EMAIL } from './nurtureTouchLogic.js';
import { WITHOUT_INDUSTRY_TOKEN } from './campaignIndustryFilters.js';

export { NURTURE_PRODUCT_PRESETS, DEFAULT_TEST_EMAIL, WITHOUT_INDUSTRY_TOKEN };

export function buildSegmentFilters(state) {
	const seg = {};
	const stage = (state.stage || '').trim();
	if (stage && stage !== 'all') seg.stage = stage;
	const ms = state.minScore;
	if (ms != null && ms !== '' && !Number.isNaN(Number(ms))) seg.min_score = Number(ms);

	const selected = (state.selectedIndustries || []).filter(Boolean);
	if (selected.length) seg.industries = selected;

	if (state.industryVerified) seg.industry_verified = true;
	const city = (state.city || '').trim();
	if (city) seg.city = city;
	const q = (state.search || '').trim();
	if (q) seg.search = q;
	return seg;
}

export function campaignPreviewPayload(state) {
	return {
		segment: buildSegmentFilters(state),
		product_name: state.product,
		sender_name: state.senderName,
		sender_email: state.senderEmail,
		theme_mode: state.themeMode,
		subject_template: state.themeMode === 'manual' ? state.subjectTemplate : undefined,
		body_template: state.themeMode === 'manual' ? state.bodyTemplate : undefined,
	};
}

export function campaignLaunchPayload(state, preview) {
	return {
		account_id: state.accountId,
		name: state.campaignName || `Сегмент ${new Date().toLocaleDateString('ru-RU')}`,
		subject: preview.subject_template,
		body: preview.body_template,
		segment: preview.segment || buildSegmentFilters(state),
		send_now: true,
		product_name: state.product,
		sender_name: state.senderName,
		sender_email: state.senderEmail,
	};
}

export function firstExample(examples) {
	const list = examples || [];
	return list[0] || null;
}
