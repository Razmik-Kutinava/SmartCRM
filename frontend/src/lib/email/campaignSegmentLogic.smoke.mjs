import {
	buildSegmentFilters,
	campaignLaunchPayload,
	firstExample,
	WITHOUT_INDUSTRY_TOKEN,
} from './campaignSegmentLogic.js';

const seg = buildSegmentFilters({
	stage: 'Новый',
	minScore: 50,
	selectedIndustries: ['IT', WITHOUT_INDUSTRY_TOKEN],
	city: '',
	search: 'acme',
});
if (seg.stage !== 'Новый' || seg.min_score !== 50 || seg.industries?.length !== 2 || seg.search !== 'acme') {
	throw new Error('filters');
}
const launch = campaignLaunchPayload(
	{ accountId: 1, campaignName: 'T', product: 'P', senderName: 'A', senderEmail: 'b@c.ru' },
	{ subject_template: 'S', body_template: 'B', segment: { stage: 'Новый' }, count: 5 }
);
if (!launch.send_now || launch.subject !== 'S') throw new Error('launch');
if (!firstExample([{ subject: 'x' }])) throw new Error('example');
console.log('campaignSegmentLogic smoke OK');
