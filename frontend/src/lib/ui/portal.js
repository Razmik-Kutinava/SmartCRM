/** Рендер узла в document.body (модалки поверх overflow-hidden). */

/** @type {import('svelte/action').Action<HTMLElement, string | undefined>} */
export function portal(node, target = 'body') {
	const el = typeof target === 'string' ? document.querySelector(target) : target;
	if (!el) return;
	el.appendChild(node);
	return {
		destroy() {
			if (node.parentNode === el) el.removeChild(node);
		},
	};
}
