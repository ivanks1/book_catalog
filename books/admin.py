from django.contrib import admin
from .models import Author, Book, BookDetail


class BookDetailInline(admin.StackedInline):
    model = BookDetail
    extra = 0


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "years_of_age")
    search_fields = ("name", "works")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "publication_date")
    list_filter = ("publication_date",)
    search_fields = ("title", "author__name")
    inlines = (BookDetailInline,)
