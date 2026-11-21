import argparse
import json
import os
import re
import sys
from datetime import date
from typing import Iterable

import django
from django.db import transaction
from google import genai


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "book_catalog.settings")
django.setup()

from books.models import Author, Book, BookDetail


MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY не задан. Укажите ключ в переменной окружения. $env:GEMINI_API_KEY=ваш_API_ключ"
        )
    return genai.Client(api_key=api_key)


def ask(question: str, client=None):
    gemini = client or get_client()
    response = gemini.models.generate_content(model=MODEL, contents=question)
    return response.text


def chat(client):
    print("Чат с Gemini. Для выхода введите «выход».")
    while True:
        question = input("Вы: ").strip()
        if question.lower() in {"выход", "exit", "quit"}:
            break
        if not question:
            continue

        print("Gemini: ", end="", flush=True)
        for chunk in client.models.generate_content_stream(
            model=MODEL,
            contents=question,
        ):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print()


def generate_catalog(count: int = 15, client=None) -> list[dict]:
    prompt = f"""
Сгенерируй РОВНО {count} известных литературных произведений.
Верни ТОЛЬКО валидный JSON-массив объектов без Markdown и пояснений.
В массиве должно быть ровно {count} объектов.
Каждый объект имеет поля:
- title: точное название произведения на русском языке
- author: имя автора на русском языке
- publication_date: дата в формате YYYY-MM-DD
- short_desc: краткое описание книги до 300 символов
- description: подробное описание книги до 1000 символов
- author_bio: краткая биография автора до 500 символов
- years_of_age: годы жизни автора, например "1804-1877"
- works: другие известные произведения автора через запятую
- img_src: пустая строка

Не повторяй названия произведений и авторов.
"""
    text = ask(prompt, client)
    match = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if not match:
        raise ValueError("Gemini не вернула JSON-массив")
    try:
        catalog = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini вернула некорректный JSON") from exc
    if not isinstance(catalog, list):
        raise ValueError("Ожидался JSON-массив")
    if len(catalog) != count:
        raise ValueError(
            f"Gemini вернула {len(catalog)} записей вместо запрошенных {count}"
        )
    return catalog


def validate_catalog(catalog: Iterable[dict]) -> list[dict]:
    required = {
        "title",
        "author",
        "publication_date",
        "short_desc",
        "description",
        "author_bio",
        "years_of_age",
        "works",
    }
    validated = []
    for index, item in enumerate(catalog, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Запись {index} не является объектом")
        missing = required - item.keys()
        if missing:
            raise ValueError(
                f"В записи {index} отсутствуют поля: {', '.join(sorted(missing))}"
            )
        if not all(isinstance(item[field], str) and item[field].strip()
                   for field in required):
            raise ValueError(f"Поля записи {index} должны быть непустыми строками")
        try:
            date.fromisoformat(item["publication_date"])
        except ValueError as exc:
            raise ValueError(
                f"Некорректная дата publication_date в записи {index}"
            ) from exc
        validated.append(item)
    return validated


@transaction.atomic
def import_catalog(catalog: Iterable[dict], replace: bool = False) -> tuple[int, int]:
    records = validate_catalog(catalog)
    if not records:
        raise ValueError("Каталог пуст")

    if replace:
        BookDetail.objects.all().delete()
        Book.objects.all().delete()
        Author.objects.all().delete()

    author_count = 0
    book_count = 0
    for item in records:
        author, created = Author.objects.get_or_create(
            name=item["author"].strip(),
            defaults={
                "img_src": item.get("img_src") or None,
                "years_of_age": item["years_of_age"].strip(),
                "bio": item["author_bio"].strip(),
                "works": item["works"].strip(),
            },
        )
        if created:
            author_count += 1

        book, created = Book.objects.update_or_create(
            title=item["title"].strip(),
            author=author,
            defaults={
                "img_src": item.get("img_src") or None,
                "publication_date": date.fromisoformat(item["publication_date"]),
                "short_desc": item["short_desc"].strip(),
            },
        )
        if created:
            book_count += 1

        BookDetail.objects.update_or_create(
            book=book,
            defaults={"description": item["description"].strip()},
        )
    return author_count, book_count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Сгенерировать книги через Gemini и сохранить в SQLite"
    )
    parser.add_argument("-n", "--count", type=int, default=15)
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Запустить интерактивный чат с потоковым выводом ответа",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Удалить существующие авторов, книги и описания перед импортом",
    )
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count должен быть положительным числом")

    try:
        client = get_client()
        if args.chat:
            chat(client)
            return 0
        catalog = generate_catalog(args.count, client)
        author_count, book_count = import_catalog(catalog, replace=args.replace)
    except (RuntimeError, ValueError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    print(
        f"Импортировано: авторов — {author_count}, "
        f"книг — {book_count}; всего обработано записей — {len(catalog)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())