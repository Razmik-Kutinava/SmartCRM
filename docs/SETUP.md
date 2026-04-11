# SmartCRM — Запуск локально (WSL2 + Linux)

## Требования

- Windows 11 + WSL2 (Ubuntu 22.04+)
- Docker Desktop + docker-compose
- Ollama (локально в WSL2)
- Python 3.11+
- Node.js 20+
- Видеокарта 32GB VRAM (для Qwen 72B)

---

## 1. Ollama — установка моделей

```bash
# Установить Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Скачать модели
ollama pull qwen2.5:14b       # основная модель
ollama pull adrienbrault/nous-hermes2pro-llama3-8b:q8_0  # hermes роутер

# Запустить
ollama serve
```

---

## 2. Переменные окружения

```bash
cp .env.example .env
# Заполни .env своими ключами:
# GROQ_API_KEY — с сайта console.groq.com (бесплатно)
# BRAVE_API_KEY — с api.search.brave.com
# TAVILY_API_KEY — с tavily.com
# SERPER_API_KEY — с serper.dev
```

---

## 3. Запуск через Docker

```bash
# Поднять PostgreSQL + Redis + Nginx
docker-compose up -d postgres redis nginx

# Запустить бэкенд
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Запустить фронтенд
cd frontend
npm install
npm run dev
```

---

## 4. Проверка

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## Частые проблемы

**Ollama не отвечает:** `ollama serve` нужно запускать в WSL2, не в Windows.

**Groq токены закончились:** система автоматически переключится на Ollama.

**Chroma не запускается:** `pip install chromadb` и убедись что порт 8001 свободен.
