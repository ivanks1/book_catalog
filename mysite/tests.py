from django.test import TestCase
from django.urls import reverse

from books.models import Author, Book, BookDetail


class CatalogViewsTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(
            name="Лев Толстой",
            years_of_age="1828-1910",
            bio="Русский писатель.",
            works="Война и мир",
        )
        self.book = Book.objects.create(
            title="Война и мир",
            author=self.author,
            publication_date="1869-01-01",
            short_desc="Исторический роман.",
        )
        BookDetail.objects.create(
            book=self.book,
            description="Подробное описание романа.",
        )

    def test_home_lists_books(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Война и мир")

    def test_search_filters_by_author(self):
        response = self.client.get(reverse("home"), {"q": "Толстой"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Война и мир")

    def test_book_detail_page(self):
        response = self.client.get(
            reverse("book_detail", kwargs={"book_id": self.book.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Подробное описание романа.")

    def test_missing_book_returns_404(self):
        response = self.client.get(
            reverse("book_detail", kwargs={"book_id": 999999})
        )
        self.assertEqual(response.status_code, 404)
