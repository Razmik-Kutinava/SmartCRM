import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	// Один origin с фронтом (5173) — стабильный WebSocket и fetch без CORS в dev
	server: {
		proxy: {
			'/api': {
				target: 'http://127.0.0.1:8000',
				changeOrigin: true
			},
			'/ws/voice': {
				target: 'http://127.0.0.1:8000',
				ws: true,
				changeOrigin: true
			}
		}
	}
});
