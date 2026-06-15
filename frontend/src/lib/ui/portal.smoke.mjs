import { portal } from './portal.js';

/** @param {HTMLElement} node */
function mount(node) {
	document.body.appendChild(node);
	return () => {
		if (node.parentNode === document.body) document.body.removeChild(node);
	};
}

if (typeof document !== 'undefined') {
	const host = document.createElement('div');
	host.setAttribute('data-testid', 'portal-smoke-host');
	const cleanup = mount(host);
	if (!document.body.contains(host)) throw new Error('portal mount failed');
	cleanup();
}

console.log('portal smoke OK');
