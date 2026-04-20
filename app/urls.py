from django.urls import path
from .views import *

urlpatterns = [
    path('', home_view, name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('verify/<str:token>/', verify_email, name='verify_email'),
    path('reset-password/', reset_password_view, name='reset_password'),
    path('reset-password/<str:token>/', reset_password_confirm_view, name='reset_password_confirm'),
    path('change-password/', change_password_view, name='change_password'),
    path('profile/', profile_view, name='profile'),
    path('books/', book_list_view, name='book_list'),
    path('books/<int:book_id>/', book_detail_view, name='book_detail'),
    path('books/add/', book_create_view, name='add_book'),
    path('books/<int:book_id>/edit/', book_update_view, name='edit_book'),
    path('books/<int:book_id>/delete/', book_delete_view, name='delete_book'),
    path('create-author/', create_author, name='create_author'),
    path('create-category/', create_category, name='create_category'),
]