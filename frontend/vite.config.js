import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, process.cwd(), '');
	const apiKey = env.PUBLIC_SMARTCRM_API_KEY || '';

	return {
		plugins: [tailwindcss(), sveltekit()],
		// Один origin с фронтом (5173) — стабильный WebSocket и fetch без CORS в dev
		server: {
			proxy: {
				'/api': {
					target: 'http://127.0.0.1:8000',
					changeOrigin: true,
					// Автоматически добавляем API-ключ во все проксируемые запросы
					headers: apiKey ? { 'X-API-Key': apiKey } : {}
				},
				'/ws/voice': {
					target: 'http://127.0.0.1:8000',
					ws: true,
					changeOrigin: true,
					headers: apiKey ? { 'X-API-Key': apiKey } : {}
				}
			}
		}
	};
});
