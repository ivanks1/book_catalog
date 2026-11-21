"""Генерация каталога книг через Gemini и импорт в Django."""

import argparse
import json
import os
import random
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Iterable

import django
import requests
from dotenv import load_dotenv
from google import genai


# ---------------------------------------------------------------------
# Загрузка настроек и Django
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "book_catalog.settings")
django.setup()

from books.models import Author, Book, BookDetail  # noqa: E402


# ---------------------------------------------------------------------
# Конфигурация API
# ---------------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"

CACHE_FILE = BASE_DIR / "cover_cache.json"
REQUEST_TIMEOUT = 20
MAX_GEMINI_ATTEMPTS = 3
MAX_GOOGLE_ATTEMPTS = 3
GOOGLE_REQUEST_INTERVAL = 2.0

_session = requests.Session()
_last_google_request = 0.0
_cover_cache: dict[str, str | None] = {}
_google_books_limited = False


# ---------------------------------------------------------------------
# Проверка и подключение Gemini API
# ---------------------------------------------------------------------

def get_gemini_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Не найден GEMINI_API_KEY. Добавьте ключ Gemini в файл .env."
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def ask_gemini(prompt: str, client: genai.Client) -> str:
    """Отправляет запрос Gemini с несколькими попытками при временных сбоях."""
    last_error = None

    for attempt in range(MAX_GEMINI_ATTEMPTS):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            result = getattr(response, "text", None)
            if not result or not result.strip():
                raise RuntimeError("Gemini вернула пустой ответ.")
            return result.strip()
        except Exception as exc:
            last_error = exc
            if attempt < MAX_GEMINI_ATTEMPTS - 1:
                delay = min(30, 3 * (2 ** attempt)) + random.uniform(0, 1)
                print(
                    f"[GEMINI] Ошибка запроса: {exc}. "
                    f"Повтор через {delay:.1f} сек."
                )
                time.sleep(delay)

    raise RuntimeError(f"Не удалось получить ответ Gemini: {last_error}")


def chat_gemini(client: genai.Client) -> None:
    print("Чат с Gemini. Для выхода введите «выход».")

    while True:
        try:
            question = input("\nВы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из чата.")
            return

        if question.lower() in {"выход", "exit", "quit"}:
            return
        if not question:
            continue

        try:
            print("Gemini: ", end="", flush=True)
            for chunk in client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=question,
            ):
                chunk_text = getattr(chunk, "text", None)
                if chunk_text:
                    print(chunk_text, end="", flush=True)
            print()
        except Exception as exc:
            print(f"\n[ОШИБКА GEMINI] {exc}")


# ---------------------------------------------------------------------
# Кэш обложек
# ---------------------------------------------------------------------

def load_cover_cache() -> None:
    global _cover_cache

    if not CACHE_FILE.exists():
        _cover_cache = {}
        return

    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        _cover_cache = data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[КЭШ] Не удалось прочитать кэш: {exc}")
        _cover_cache = {}


def save_cover_cache() -> None:
    temp_file = CACHE_FILE.with_suffix(".tmp")
    try:
        temp_file.write_text(
            json.dumps(_cover_cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_file.replace(CACHE_FILE)
    except OSError as exc:
        print(f"[КЭШ] Не удалось сохранить кэш: {exc}")


def make_cache_key(title: str, author: str) -> str:
    return f"{title.strip().casefold()}|||{author.strip().casefold()}"


# ---------------------------------------------------------------------
# Google Books API — поиск реальных обложек
# ---------------------------------------------------------------------

def wait_between_google_requests() -> None:
    global _last_google_request

    elapsed = time.monotonic() - _last_google_request
    if elapsed < GOOGLE_REQUEST_INTERVAL:
        time.sleep(GOOGLE_REQUEST_INTERVAL - elapsed)
    _last_google_request = time.monotonic()


def get_book_cover(title: str, author: str) -> str | None:
    """Ищет обложку в Google Books. Ошибка поиска не останавливает импорт."""
    global _google_books_limited

    cache_key = make_cache_key(title, author)
    if cache_key in _cover_cache:
        print(f"[КЭШ] {title}: результат уже сохранён")
        return _cover_cache[cache_key]

    if _google_books_limited:
        print(f"[ОБЛОЖКА] {title}: поиск пропущен — лимит Google Books")
        return None

    if not GOOGLE_BOOKS_API_KEY:
        print(f"[ОБЛОЖКА] {title}: не задан GOOGLE_BOOKS_API_KEY")
        return None

    params = {
        "q": f'intitle:"{title}" inauthor:"{author}"',
        "maxResults": 10,
        "printType": "books",
        "key": GOOGLE_BOOKS_API_KEY,
    }

    for attempt in range(MAX_GOOGLE_ATTEMPTS):
        try:
            wait_between_google_requests()
            response = _session.get(
                GOOGLE_BOOKS_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                _google_books_limited = True
                retry_after = response.headers.get("Retry-After")
                retry_text = (
                    f" Retry-After: {retry_after} сек."
                    if retry_after and retry_after.isdigit()
                    else ""
                )
                print(
                    "[ЛИМИТ API] Google Books вернул HTTP 429."
                    " Поиск обложек отключён до конца этого запуска."
                    f"{retry_text} Импорт книг продолжится без обложек."
                )
                return None

            response.raise_for_status()
            payload = response.json()
            items = payload.get("items", [])

            wanted_title = title.casefold().strip()
            wanted_author = author.casefold().strip()

            for item in items:
                volume = item.get("volumeInfo", {})
                found_title = volume.get("title", "").casefold().strip()
                found_authors = [
                    name.casefold().strip()
                    for name in volume.get("authors", [])
                ]

                title_matches = (
                    wanted_title in found_title
                    or found_title in wanted_title
                )
                author_matches = any(
                    wanted_author in name or name in wanted_author
                    for name in found_authors
                )

                if not title_matches or not author_matches:
                    continue

                image_links = volume.get("imageLinks", {})
                cover = (
                    image_links.get("extraLarge")
                    or image_links.get("large")
                    or image_links.get("medium")
                    or image_links.get("thumbnail")
                    or image_links.get("smallThumbnail")
                )

                if cover:
                    cover = cover.replace("http://", "https://")
                    _cover_cache[cache_key] = cover
                    save_cover_cache()
                    print(f"[ОБЛОЖКА] {title}: найдена")
                    return cover

            _cover_cache[cache_key] = None
            save_cover_cache()
            print(f"[ОБЛОЖКА] {title}: не найдена")
            return None

        except requests.RequestException as exc:
            print(f"[ОШИБКА GOOGLE BOOKS] {title}: {exc}")
            if attempt < MAX_GOOGLE_ATTEMPTS - 1:
                delay = min(30, 4 * (2 ** attempt)) + random.uniform(0, 1)
                print(f"[ПОВТОР] Через {delay:.1f} сек.")
                time.sleep(delay)
        except (ValueError, TypeError) as exc:
            print(f"[ОШИБКА ОТВЕТА GOOGLE BOOKS] {title}: {exc}")
            return None

    # Временные ошибки не сохраняем в кэш, чтобы попробовать в следующий раз.
    print(f"[ОБЛОЖКА] {title}: пропущена после ошибок API")
    return None


# ---------------------------------------------------------------------
# Генерация и проверка каталога через Gemini
# ---------------------------------------------------------------------

def extract_json_array(raw_text: str) -> list:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Gemini не вернула JSON-массив.")

    try:
        data = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini вернула некорректный JSON: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("Ожидался JSON-массив.")
    return data


def generate_catalog(count: int, client: genai.Client) -> list[dict]:
    prompt = f"""
Сгенерируй РОВНО {count} известных литературных произведений.
Верни ТОЛЬКО валидный JSON-массив без Markdown и пояснений.

Каждый объект должен содержать поля:
- title: точное название произведения на русском языке
- author: полное имя автора на русском языке
- publication_date: дата первого опубликования в формате YYYY-MM-DD
- short_desc: краткое описание книги до 300 символов
- description: подробное описание книги до 1000 символов
- author_bio: краткая биография автора до 500 символов
- years_of_age: годы жизни автора, например "1804-1877"
- works: другие известные произведения автора через запятую

Требования:
1. Используй реальные литературные произведения и авторов.
2. Не повторяй произведения.
3. Не повторяй авторов.
4. Все текстовые поля должны быть на русском языке.
5. Даты должны быть корректными.
6. Не добавляй ссылки на изображения и поле img_src.
7. Не добавляй текст до или после JSON-массива.
"""

    raw_text = ask_gemini(prompt, client)
    catalog = extract_json_array(raw_text)

    if len(catalog) != count:
        raise ValueError(
            f"Запрошено {count} книг, Gemini вернула {len(catalog)}. "
            "Попробуйте запустить программу ещё раз или уменьшить --count."
        )
    return catalog


def validate_catalog(catalog: Iterable[dict]) -> list[dict]:
    required = {
        "title", "author", "publication_date", "short_desc",
        "description", "author_bio", "years_of_age", "works",
    }
    validated = []
    seen_books = set()
    seen_authors = set()

    for index, item in enumerate(catalog, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Запись {index} не является объектом.")

        missing = required - item.keys()
        if missing:
            raise ValueError(
                f"В записи {index} отсутствуют поля: "
                f"{', '.join(sorted(missing))}"
            )

        normalized = {}
        for field in required:
            value = item[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Поле {field} в записи {index} должно быть непустой строкой."
                )
            normalized[field] = value.strip()

        try:
            date.fromisoformat(normalized["publication_date"])
        except ValueError as exc:
            raise ValueError(
                f"Некорректная дата в записи {index}: "
                f"{normalized['publication_date']}"
            ) from exc

        book_key = normalized["title"].casefold()
        author_key = normalized["author"].casefold()
        if book_key in seen_books:
            raise ValueError(f"Повторяется книга: {normalized['title']}")
        if author_key in seen_authors:
            raise ValueError(f"Повторяется автор: {normalized['author']}")

        seen_books.add(book_key)
        seen_authors.add(author_key)
        validated.append(normalized)

    return validated


# ---------------------------------------------------------------------
# Импорт данных в Django
# ---------------------------------------------------------------------

def import_catalog(
    catalog: Iterable[dict],
    replace: bool = False,
) -> tuple[int, int]:
    records = validate_catalog(catalog)
    if not records:
        raise ValueError("Каталог пуст.")

    # Сначала выполняем сетевые запросы, чтобы не держать транзакцию БД открытой.
    prepared_records = []
    for index, item in enumerate(records, start=1):
        print(f"\n[{index}/{len(records)}] Обработка: {item['title']}")
        try:
            cover_url = get_book_cover(item["title"], item["author"])
        except Exception as exc:
            print(f"[ПРЕДУПРЕЖДЕНИЕ] Обложка пропущена: {exc}")
            cover_url = None
        prepared_records.append((item, cover_url))

    from django.db import transaction

    author_count = 0
    book_count = 0

    with transaction.atomic():
        if replace:
            print("\n[БАЗА] Удаление старого каталога...")
            BookDetail.objects.all().delete()
            Book.objects.all().delete()
            Author.objects.all().delete()

        for item, cover_url in prepared_records:
            author, author_created = Author.objects.get_or_create(
                name=item["author"],
                defaults={
                    "img_src": cover_url,
                    "years_of_age": item["years_of_age"],
                    "bio": item["author_bio"],
                    "works": item["works"],
                },
            )

            if author_created:
                author_count += 1
            else:
                changed_fields = []
                if not author.img_src and cover_url:
                    author.img_src = cover_url
                    changed_fields.append("img_src")
                if changed_fields:
                    author.save(update_fields=changed_fields)

            book, book_created = Book.objects.update_or_create(
                title=item["title"],
                author=author,
                defaults={
                    "img_src": cover_url,
                    "publication_date": date.fromisoformat(item["publication_date"]),
                    "short_desc": item["short_desc"],
                },
            )

            if book_created:
                book_count += 1

            BookDetail.objects.update_or_create(
                book=book,
                defaults={"description": item["description"]},
            )

    return author_count, book_count


# ---------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Генерация каталога книг через Gemini и импорт в Django."
    )
    parser.add_argument(
        "-n", "--count", type=int, default=15,
        help="Количество книг (по умолчанию: 15).",
    )
    parser.add_argument(
        "--chat", action="store_true",
        help="Запустить интерактивный чат с Gemini.",
    )
    parser.add_argument(
        "--replace", action="store_true",
        help="Удалить существующих авторов, книги и описания перед импортом.",
    )
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count должен быть положительным числом.")

    try:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "Не задан GEMINI_API_KEY. Заполните файл .env."
            )
        if not GOOGLE_BOOKS_API_KEY:
            print(
                "[ПРЕДУПРЕЖДЕНИЕ] Не задан GOOGLE_BOOKS_API_KEY. "
                "Книги импортируются, но поиск обложек работать не будет."
            )

        client = get_gemini_client()

        if args.chat:
            chat_gemini(client)
            return 0

        load_cover_cache()
        print(f"[GEMINI] Модель: {GEMINI_MODEL}")
        print("[GEMINI] Генерация каталога...")

        catalog = generate_catalog(args.count, client)
        print(f"[GEMINI] Получено произведений: {len(catalog)}")

        catalog = validate_catalog(catalog)
        print("\n[DJANGO] Начинаем импорт в базу данных...")

        author_count, book_count = import_catalog(
            catalog,
            replace=args.replace,
        )

        print("\nИмпорт успешно завершён!")
        print(f"Новых авторов: {author_count}")
        print(f"Новых книг: {book_count}")
        print(f"Всего обработано записей: {len(catalog)}")
        return 0

    except KeyboardInterrupt:
        print("\nОперация прервана пользователем.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"\n[ОШИБКА] {exc}", file=sys.stderr)
        return 1
    finally:
        _session.close()


if __name__ == "__main__":
    raise SystemExit(main())
