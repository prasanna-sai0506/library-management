from django.urls import path
from .views import BorrowingListCreateAPIView, BorrowingDetailAPIView, BorrowingReturnAPIView

urlpatterns = [
    path('borrowings/', BorrowingListCreateAPIView.as_view(), name='borrowing-list-create'),
    path('borrowings/<int:pk>/', BorrowingDetailAPIView.as_view(), name='borrowing-detail'),
    path('borrowings/<int:pk>/return/', BorrowingReturnAPIView.as_view(), name='borrowing-return'),
]