from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from books.models import Author, Book


def home(request):
    query = request.GET.get("q", "").strip()
    books = Book.objects.select_related("author").prefetch_related("details")
    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(author__name__icontains=query)
            | Q(short_desc__icontains=query)
        )
    return render(
        request,
        "index.html",
        {"books": books.order_by("title"), "query": query},
    )


def book_detail(request, book_id):
    book = get_object_or_404(
        Book.objects.select_related("author").prefetch_related("details"),
        id=book_id,
    )
    return render(request, "book_detail.html", {"book": book})


def author_detail(request, author_id):
    author = get_object_or_404(
        Author.objects.prefetch_related("books"),
        id=author_id,
    )
    return render(request, "author_detail.html", {"author": author})
