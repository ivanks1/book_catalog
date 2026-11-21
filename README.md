Проект "﻿BookMix"

Django-каталог книг с поиском, страницами произведений и авторов.

## Запуск

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python add_data_to_db.py
python manage.py runserver
```

Приложение будет доступно по адресу `http://127.0.0.1:8000/`.

Панель администратора: `http://127.0.0.1:8000/admin/`.

## Импорт каталога через Gemini, Google Books

Задайте ключ API Gemini и Books через переменную окружения, не сохраняя ключ в исходном коде:

```powershell
$env:GEMINI_API_KEY="ваш_ключ"
python gemini_to_db.py --count 15
```

Для общения с Gemini в терминале запустите потоковый чат:

```powershell
python gemini_to_db.py --chat
```

Ответ будет появляться по частям. Чтобы завершить чат, введите `выход`.

Для полной замены существующего каталога используйте `--replace`.
