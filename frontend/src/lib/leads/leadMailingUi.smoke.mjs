import {
	openLeadMailing,
	closeLeadMailing,
	leadMailingVisible,
	leadMailingLead,
	leadMailingOpen,
} from './leadMailingUi.js';

const lead = { id: 7, company: 'Test' };
openLeadMailing(lead);
let visible = false;
let stored = null;
const unsubV = leadMailingVisible.subscribe((v) => { visible = v; });
const unsubL = leadMailingLead.subscribe((l) => { stored = l; });
if (!visible || !stored || stored.id !== 7) throw new Error('open failed');
closeLeadMailing();
let stillOpen = true;
const unsubO = leadMailingOpen.subscribe((o) => { stillOpen = o; });
unsubO();
unsubV();
unsubL();
if (stillOpen) throw new Error('close failed');
openLeadMailing(null);
leadMailingOpen.subscribe((o) => { stillOpen = o; })();
if (stillOpen) throw new Error('null lead should not open');

console.log('leadMailingUi smoke OK');
