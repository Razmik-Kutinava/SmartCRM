import { isLeadCardRoute } from './appSidebar.js';

const assert = (cond, msg) => {
	if (!cond) throw new Error(msg);
};

assert(isLeadCardRoute('/leads/3187'), 'numeric id');
assert(!isLeadCardRoute('/leads/list'), 'list');
assert(!isLeadCardRoute('/leads/funnel'), 'funnel');
assert(!isLeadCardRoute('/leads/analytics'), 'analytics');
assert(!isLeadCardRoute('/'), 'root');

console.log('appSidebar.smoke OK');
