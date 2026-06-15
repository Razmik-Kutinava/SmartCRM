import {
	buildSegmentFilters,
	campaignLaunchPayload,
	firstExample,
} from './campaignSegmentLogic.js';

const seg = buildSegmentFilters({ stage: 'Новый', minScore: 50, industry: 'IT', city: '', search: 'acme' });
if (seg.stage !== 'Новый' || seg.min_score !== 50 || seg.industry !== 'IT' || seg.search !== 'acme') {
	throw new Error('filters');
}
const launch = campaignLaunchPayload(
	{ accountId: 1, campaignName: 'T', product: 'P', senderName: 'A', senderEmail: 'b@c.ru' },
	{ subject_template: 'S', body_template: 'B', segment: { stage: 'Новый' }, count: 5 }
);
if (!launch.send_now || launch.subject !== 'S') throw new Error('launch');
if (!firstExample([{ subject: 'x' }])) throw new Error('example');
console.log('campaignSegmentLogic smoke OK');
