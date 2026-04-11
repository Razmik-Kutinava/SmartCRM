#!/bin/bash
# Создаёт пользователя и БД smartcrm в PostgreSQL.
# Запуск: sudo bash scripts/setup_db.sh
set -e

echo "=== SmartCRM: настройка PostgreSQL ==="

# Создаём роль и базу данных
sudo -u postgres psql <<'SQL'
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'smartcrm') THEN
    CREATE ROLE smartcrm WITH LOGIN PASSWORD 'smartcrm';
    RAISE NOTICE 'Роль smartcrm создана';
  ELSE
    ALTER ROLE smartcrm WITH PASSWORD 'smartcrm';
    RAISE NOTICE 'Пароль smartcrm обновлён';
  END IF;
END $$;

SELECT 'OK: роль ' || rolname FROM pg_roles WHERE rolname = 'smartcrm';
SQL

sudo -u postgres bash -c "createdb -O smartcrm smartcrm 2>/dev/null && echo '✓ БД smartcrm создана' || echo '✓ БД smartcrm уже существует'"

echo ""
echo "Проверка подключения:"
PGPASSWORD=smartcrm psql -U smartcrm -h 127.0.0.1 -d smartcrm -c "SELECT current_user, version()" 2>&1

echo ""
echo "=== Готово! Теперь запусти: ==="
echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
