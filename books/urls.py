from django.urls import path
from .views import BookAPIView, ShelfAPIView

urlpatterns = [
    path('books/', BookAPIView.as_view(), name='books'),
    path('shelves/pack/', ShelfAPIView.as_view(), name='shelf-pack'),
    path('shelves/', ShelfAPIView.as_view(), name='shelves'),
]
