
from django.db import models


# Модель автора
class Author(models.Model):
    name = models.CharField(max_length=200)
    img_src = models.URLField(blank=True, null=True)
    years_of_age = models.CharField(max_length=50)
    bio = models.TextField()
    works = models.TextField()

    def __str__(self):
        return self.name


# Модель книги
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='books'
    )
    img_src = models.URLField(blank=True, null=True)
    publication_date = models.DateField()
    short_desc = models.TextField()

    def __str__(self):
        return self.title


# Модель подробного описания книги
class BookDetail(models.Model):
    book = models.OneToOneField(
        Book,
        on_delete=models.CASCADE,
        related_name='details'
    )
    description = models.TextField()

    def __str__(self):
        return f'Описание: {self.book.title}'
