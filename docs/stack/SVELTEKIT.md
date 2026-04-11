# SvelteKit — Фронтенд

## Почему SvelteKit

- Vite под капотом — мгновенный старт (`npm run dev`)
- Нет Virtual DOM — быстрее React/Next.js
- Меньше кода для тех же задач
- WebSocket интеграция проще чем в React
- Tailwind CSS — быстрая вёрстка

## Структура

```
src/
  routes/
    +page.svelte          — дашборд (главная)
    leads/
      +page.svelte        — список лидов
      [id]/+page.svelte   — карточка лида
  components/
    VoiceInput.svelte     — кнопка записи + визуализация
    AgentPanel.svelte     — панель агентов (статус, ответы)
    LeadCard.svelte       — карточка лида
  lib/
    api.js                — HTTP клиент → FastAPI
    websocket.js          — WebSocket → голосовой пайплайн
```

## WebSocket для голоса

```javascript
// src/lib/websocket.js
const ws = new WebSocket('ws://localhost:8000/ws/voice');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.type: "transcript" | "intent" | "agent_result" | "done"
};

// Отправить аудио чанк
ws.send(audioBlob);
```

## Запуск

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
```

## Proxy к бэкенду (vite.config.js)

```javascript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': { target: 'ws://localhost:8000', ws: true }
  }
}
```
