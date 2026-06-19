import {
	openLeadCreateModal,
	closeLeadCreateModal,
	leadCreateVisible,
	leadCreateOpen,
	leadCreateSource,
} from './leadCreateUi.js';

openLeadCreateModal({ source: 'Дашборд' });
let visible = false;
let open = false;
let source = '';
const unsubV = leadCreateVisible.subscribe((v) => { visible = v; });
const unsubO = leadCreateOpen.subscribe((o) => { open = o; });
const unsubS = leadCreateSource.subscribe((s) => { source = s; });
if (!visible || !open || source !== 'Дашборд') throw new Error('open failed');
closeLeadCreateModal();
unsubV();
unsubO();
unsubS();
let stillOpen = true;
leadCreateOpen.subscribe((o) => { stillOpen = o; })();
if (stillOpen) throw new Error('close failed');

console.log('leadCreateUi smoke OK');
