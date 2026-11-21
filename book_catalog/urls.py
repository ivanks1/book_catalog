from django.contrib import admin
from django.urls import path
from mysite import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('authors/<int:author_id>/', views.author_detail, name='author_detail'),
]
