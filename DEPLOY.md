# Как выложить калькулятор в интернет

Приложение — обычный Streamlit-сервер: одно состояние, без базы данных и личных
данных пользователей. Поэтому подходит любой хостинг, который умеет запускать
Docker-контейнер или Python-процесс.

В репозитории уже лежит всё нужное:

| Файл | Зачем |
|---|---|
| `requirements.txt` | прод-зависимости (без pytest) |
| `requirements-dev.txt` | зависимости для тестов |
| `packages.txt` | apt-пакеты для Streamlit Cloud (`fonts-dejavu-core`) |
| `Dockerfile` | образ для VPS / Hugging Face / любого Docker-хостинга |
| `.dockerignore`, `.gitignore` | мусор не уезжает в образ и в git |
| `.streamlit/config.toml` | тёмная тема, headless-режим |
| `assets/` | логотипы для интерфейса и отчётов |

Важно: на Linux обязательны **шрифты DejaVu** (`fonts-dejavu-core`), иначе PDF-экспорт
упадёт с ошибкой «Cyrillic-capable TTF font not found». В Dockerfile и `packages.txt`
это уже учтено.

---

## Вариант A. Streamlit Community Cloud — бесплатно, 5 минут

Самый быстрый путь: даёт публичную ссылку вида
`https://<имя-профиля>-<репозиторий>-<файл>.streamlit.app`.

**Шаги**

1. Создать аккаунт на GitHub и репозиторий (можно приватный — приложение всё равно
   будет публичным).
2. Загрузить проект:
   ```bash
   git init
   git add .
   git commit -m "WasherBot calculator"
   git branch -M main
   git remote add origin https://github.com/<логин>/<репозиторий>.git
   git push -u origin main
   ```
3. Зайти на <https://share.streamlit.io> → **New app** → выбрать репозиторий, ветку
   `main`, файл `app.py` → **Deploy**.
4. Через 2–3 минуты получить ссылку и отправить её кому угодно.

**Плюсы:** ноль настройки, бесплатно, авто-обновление при `git push`.
**Минусы:** приложение засыпает после 12 часов без запросов (первый заход 30–60 с);
1 ГБ RAM; свой домен подключить нельзя; аккаунт и доступность сервиса из РФ могут
зависеть от инфраструктуры GitHub/Streamlit.

---

## Вариант B. Hugging Face Spaces — бесплатно, Docker

1. Аккаунт на <https://huggingface.co> → **New Space**.
2. SDK: **Docker** (файл `Dockerfile` уже есть) → Public.
3. Загрузить файлы проекта (через веб-интерфейс или `git`).
4. Ссылка вида `https://huggingface.co/spaces/<логин>/<имя>`.

**Плюсы:** бесплатно, до 16 ГБ RAM и 2 vCPU, Docker как на VPS.
**Минусы:** страница обёрнута в интерфейс HF (можно открыть в отдельном окне),
свой домен — только на платном плане; сервис зарубежный.

---

## Вариант C. VPS в России — свой домен, ~450–900 ₽/мес  ★ для бизнеса

Полный контроль: свой адрес вида `calc.washerbot.ru`, без «засыпания», оплата
российской картой. Подойдёт Timeweb Cloud, Beget, Selectel, reg.ru — минимальный
тариф 1–2 vCPU / 1–2 ГБ RAM стоит примерно 400–800 ₽/мес.

**Шаги**

1. Создать VPS с Ubuntu 22.04/24.04, запомнить IP.
2. По DNS добавить A-запись `calc.washerbot.ru → IP` (у регистратора домена).
3. Подключиться по SSH и поставить Docker:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
4. Скопировать проект на сервер (git clone или scp), затем:
   ```bash
   cd washerbot-calculator
   docker build -t washerbot-calc .
   docker run -d --name calc --restart unless-stopped \
     -p 127.0.0.1:8501:8501 washerbot-calc
   ```
5. Поставить nginx и HTTPS:
   ```bash
   apt install -y nginx certbot python3-certbot-nginx
   ```
   Конфиг `/etc/nginx/sites-available/calc`:
   ```nginx
   server {
       listen 80;
       server_name calc.washerbot.ru;

       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;      # websocket Streamlit
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 3600;
       }
   }
   ```
   ```bash
   ln -s /etc/nginx/sites-available/calc /etc/nginx/sites-enabled/calc
   rm -f /etc/nginx/sites-enabled/default
   nginx -t && systemctl reload nginx
   certbot --nginx -d calc.washerbot.ru   # бесплатный HTTPS
   ```
6. Проверить `https://calc.washerbot.ru` — калькулятор доступен всем.

**Обновление версии:** `git pull && docker build -t washerbot-calc . && docker restart calc`.

**Плюсы:** свой домен и брендинг, нет лимитов сна, данные и код у вас, рубли.
**Минусы:** нужен человек, который один раз настроит сервер (30–40 минут), и
дальше следит за обновлениями ОС.

---

## Вариант D. Render / Railway / Fly.io

Docker-деплой из GitHub за пару кликов, автодеплой при push.
Бесплатный тариф Render ограничен по памяти и «усыпляет» приложение; Railway/Fly —
от ~5 $/мес. Основное неудобство для РФ — нужна зарубежная банковская карта.

---

## Что выбрать

| Вариант | Цена | Свой домен | Сон | Сложность | Кому |
|---|---|---|---|---|---|
| A. Streamlit Cloud | 0 ₽ | нет | 12 ч | 5 минут | быстро показать, тесты, пилот |
| B. Hugging Face | 0 ₽ | нет | 48 ч | 10 минут | бесплатный запас по памяти |
| C. VPS в РФ | 450–900 ₽/мес | да | нет | 30–40 минут разово | рабочий инструмент для клиентов |
| D. Render/Railway | 0–500 ₽/мес | да | на free — да | 15 минут | если есть зарубежная карта |

**Рекомендация:** начать с **A** (ссылка сегодня, ноль затрат), а когда пойдут
клиенты — перенести на **C** с доменом `calc.washerbot.ru`: контейнер уже готов,
переезд занимает полчаса.

---

## Домен и HTTPS

- Домен `.ru` — 200–400 ₽/год у reg.ru, Timeweb, Beget.
- HTTPS — бесплатный Let's Encrypt (certbot продлевает сам).
- Для Streamlit Cloud/HF свой домен недоступен (только платные планы HF).

## Если нужен доступ по паролю

- Простой вариант: basic-auth в nginx (`htpasswd`) — 5 строк конфига.
- Гибкий: `st.login()` в Streamlit (OIDC через Google/Яндекс) — уже поддерживается
  в Streamlit 1.42+.
- На Streamlit Cloud приватность задаётся видимостью приложения (Viewer-доступ по
  email), но код всё равно остаётся публичным в репозитории.

## Чек-лист перед публикацией

- [ ] `pytest -q` — все тесты зелёные (сейчас 166 passed).
- [ ] `requirements.txt` без dev-зависимостей.
- [ ] `packages.txt` / Dockerfile со шрифтами DejaVu.
- [ ] `.streamlit/config.toml` с темой и `headless = true`.
- [ ] папка `assets/` с логотипами в репозитории.
- [ ] нет секретов и токенов в коде (их и нет — приложение не ходит во внешние API).
- [ ] проверен экспорт PDF на сервере (шрифты) — открыть отчёт после деплоя.
