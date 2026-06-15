import {
	MAILING_TYPE_NURTURE,
	LEAD_MAILING_TYPES,
	enabledMailingTypes,
	getMailingType,
	emailPanelDeepLink,
} from './leadMailingTypes.js';

const lead = { id: 42, company: 'Test Co' };

if (LEAD_MAILING_TYPES.length < 1) throw new Error('empty registry');
if (!getMailingType(MAILING_TYPE_NURTURE)) throw new Error('nurture missing');
if (enabledMailingTypes(lead).length !== 1) throw new Error('enabled count');
if (enabledMailingTypes(null).length !== 0) throw new Error('null lead');
const link = emailPanelDeepLink(42);
if (!link.includes('lead=42') || !link.includes('panel=nurture')) throw new Error('bad link');

console.log('leadMailingTypes smoke OK');
