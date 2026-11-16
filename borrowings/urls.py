from django.urls import path
from .views import BorrowingListCreateAPIView, BorrowingReturnAPIView

urlpatterns = [
    path('borrowings/', BorrowingListCreateAPIView.as_view(), name='borrowing-list-create'),
    
    path('borrowings/return/', BorrowingReturnAPIView.as_view(), name='borrowing-return'),
]