import email
from urllib import request

from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from django.core.mail import send_mail
import uuid
from django.http import HttpResponse
from django.db import models

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')        
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            return render(request, 'register.html', {'error': 'Passwords do not match', 'user': None})
        
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists', 'user': None})
        
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email already exists', 'user': None})
        
        email_token = str(uuid.uuid4())
        user = User(username=username, email=email, email_token=email_token)
        user.set_password(password)
        user.save()
        
        link = f'http://127.0.0.1:8000/verify/{email_token}/'
        
        send_mail(
            'Verify your email',
            f'Click the link to verify your email: {link}',
            'noreply@exam2.com',
            [email],
        )
        
        return render(request, 'verify_email.html', {'success': 'Check your email to verify', 'user': None})
    
    return render(request, 'register.html', {'user': None})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = User.objects.filter(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                return render(request, 'login.html', {'error': 'Please verify your email first', 'user': None})
            request.session['user_id'] = user.id
            return redirect('home')
        return render(request, 'login.html', {'error': 'Invalid credentials'})
        
    return render(request, 'login.html')


def verify_email(request, token):
    user = User.objects.filter(email_token=token).first()
    if user:
        user.is_active = True
        user.email_token = None
        user.save()
        return render(request, 'verify_email.html', {'success': 'Email verified successfully. You can now log in.', 'user': None})
    return render(request, 'verify_email.html', {'error': 'Invalid verification link.', 'user': None})


def logout_view(request):
    request.session.flush()
    return redirect('login')


def home_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    user = get_object_or_404(User, id=user_id)
    books = Book.objects.all()
    
    # Calculate statistics
    total_books = books.count()
    avg_price = 0
    if books.exists():
        avg_price = round(sum(book.price for book in books) / total_books, 2)
    
    # Get authors with book count
    authors_count = Author.objects.all().annotate(
        books_count=models.Count('book')
    )
    categories_count = Category.objects.count()
    reviews_count = Review.objects.count()
    recent_books = Book.objects.select_related('author', 'category').order_by('-created_at')[:4]
    
    context = {
        'user': user,
        'books': books,
        'total_books': total_books,
        'avg_price': avg_price,
        'authors_count': authors_count,
        'categories_count': categories_count,
        'reviews_count': reviews_count,
        'recent_books': recent_books,
    }
    return render(request, 'home.html', context)


def reset_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        
        if not user:
            return render(request, 'reset_password.html', {'error': 'Email address not found in our system', 'user': None})
        
        if not user.is_active:
            return render(request, 'reset_password.html', {'error': 'Your account is not verified. Please check your email.', 'user': None})
        
        reset_token = str(uuid.uuid4())
        user.reset_token = reset_token
        user.save()
        
        link = f'http://127.0.0.1:8000/reset-password/{reset_token}/'
        try:
            send_mail(
                'Reset Your Password - BookCatalog',
                f'Click this link to reset your password:{link}This link will expire in 24 hours.',
                None,
                [email],
            )
            return render(request, 'reset_password_sent.html')
        except Exception as e:
            return render(request, 'reset_password.html')
    
    return render(request, 'reset_password.html')


def reset_password_confirm_view(request, token):
    user = User.objects.filter(reset_token=token).first()
    
    if not user:
        return render(request, 'reset_password_error.html', {'error': 'Invalid or expired reset link'})
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if not password or not confirm_password:
            return render(request, 'reset_password_confirm.html', {'error': 'All fields are required', 'token': token})
        
        if password != confirm_password:
            return render(request, 'reset_password_confirm.html', {'error': 'Passwords do not match', 'token': token})
        
        if len(password) < 6:
            return render(request, 'reset_password_confirm.html', {'error': 'Password must be at least 6 characters', 'token': token})
        
        user.set_password(password)
        user.reset_token = None
        user.save()
        
        return render(request, 'reset_password_success.html', {'success': 'Password reset successfully. You can now log in.'})
    
    return render(request, 'reset_password_confirm.html', {'token': token})


def book_detail_view(request, book_id):
    user_id = request.session.get('user_id')
    user = get_object_or_404(User, id=user_id) if user_id else None
    book = get_object_or_404(Book.objects.select_related('author', 'category'), id=book_id)
    # Use prefetch_related for reviews to optimize query
    reviews = Review.objects.filter(book=book).select_related('user')
    
    # Use aggregate for average rating (Django ORM)
    from django.db.models import Avg
    avg_rating_data = Review.objects.filter(book=book).aggregate(avg_rating=Avg('rating'))
    avg_rating = avg_rating_data['avg_rating'] or 0
    
    context = {
        'book': book,
        'user': user,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1)
    }
    return render(request, 'book_detail.html', context)


def book_create_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')
        cover_image = request.FILES.get('cover_image')
        author_id = request.POST.get('author')
        category_id = request.POST.get('category')
        author = get_object_or_404(Author, id=author_id)
        category = get_object_or_404(Category, id=category_id) 
        user = get_object_or_404(User, id=user_id)
        book = Book.objects.create(
            title=title,
            description=description,
            price=price,
            cover_image=cover_image,
            author=author,
            category=category,
            created_by=user
        )
        return redirect('book_detail', book_id=book.id)
    authors = Author.objects.all()
    categories = Category.objects.all()
    return render(request, 'book_create.html', {'authors': authors, 'categories': categories})


def book_delete_view(request, book_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    book = get_object_or_404(Book, id=book_id)
    if book.created_by.id != user_id:
        return render(request, 'book_delete.html', {'error': 'You do not have permission to delete this book', 'book': book})
    book.delete()
    return redirect('home')


def book_list_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    # Get all books with select_related for optimization
    books = Book.objects.select_related('author', 'category')
    
    # Search by title (title__icontains)
    search = request.GET.get('search')
    if search:
        books = books.filter(title__icontains=search)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        books = books.filter(category_id=category_id)
    
    # Filter by author
    author_id = request.GET.get('author')
    if author_id:
        books = books.filter(author_id=author_id)
    
    # Filter by price range (price__gte, price__lte)
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min:
        books = books.filter(price__gte=price_min)
    if price_max:
        books = books.filter(price__lte=price_max)
    
    # Get all categories and authors for filter dropdowns
    categories = Category.objects.all()
    authors = Author.objects.all()
    
    return render(request, 'book_list.html', {
        'books': books,
        'categories': categories,
        'authors': authors,
        'search': search or '',
    })


def book_update_view(request, book_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    book = get_object_or_404(Book, id=book_id)
    if book.created_by.id != user_id:
        return render (request, 'book_update.html', {'error': 'You do not have permission to update this book', 'book': book})
    
    if request.method == 'POST':
        book.title = request.POST.get('title')
        book.description = request.POST.get('description')
        book.price = request.POST.get('price')
        if request.FILES.get('cover_image'):
            book.cover_image = request.FILES.get('cover_image')
        author_id = request.POST.get('author')
        category_id = request.POST.get('category')
        book.author = get_object_or_404(Author, id=author_id)
        book.category = get_object_or_404(Category, id=category_id) 
        book.save()
        return redirect('book_detail', book_id=book.id)
    authors = Author.objects.all()
    categories = Category.objects.all()
    return render(request, 'book_update.html', {'book': book, 'authors': authors, 'categories': categories})


def review_create_view(request, book_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    book = get_object_or_404(Book, id=book_id)
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        text = request.POST.get('text')
        rating = request.POST.get('rating')
        Review.objects.create(book=book, user=user, text=text, rating=rating)
        return redirect('book_detail', book_id=book.id)
    return render(request, 'review_create.html', {'book': book})


def review_delete_view(request, book_id, review_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    review = get_object_or_404(Review, id=review_id)

    if review.user.id != user_id:
        return render(request, 'review_delete.html', {'error': 'You do not have permission to delete this review', 'review': review})
    
    review.delete()
    return redirect('book_detail', book_id=book_id)


def review_update_view(request, book_id, review_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    review = get_object_or_404(Review, id=review_id)
    if review.user.id != user_id:
        return render(request, 'review_update.html', {'error': 'You do not have permission to update this review', 'review': review})
    
    if request.method == 'POST':
        review.text = request.POST.get('text')
        review.rating = request.POST.get('rating')
        review.save()
        return redirect('book_detail', book_id=book_id)
    return render(request, 'review_update.html', {'review': review})


def profile_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    user = get_object_or_404(User, id=user_id)
    user_books = Book.objects.filter(created_by=user).select_related('category', 'author')
    
    context = {
        'user': user,
        'user_books': user_books,
        'books_count': user_books.count(),
    }
    return render(request, 'profile.html', context)


def change_password_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not user.check_password(current_password):
            return render(request, 'change_password.html', {'error': 'Current password is incorrect', 'user': user})
        
        if new_password != confirm_password:
            return render(request, 'change_password.html', {'error': 'New passwords do not match', 'user': user})
        
        if len(new_password) < 6:
            return render(request, 'change_password.html', {'error': 'Password must be at least 6 characters', 'user': user})
        
        if current_password == new_password:
            return render(request, 'change_password.html', {'error': 'New password must be different from current password', 'user': user})
        
        user.set_password(new_password)
        user.save()
        
        return render(request, 'change_password.html', {'success': 'Password changed successfully! You can continue using your account.', 'user': user})
    
    return render(request, 'change_password.html', {'user': user})


def create_author(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        bio = request.POST.get('bio')
        if not full_name or not bio:
            return render(request, 'author_create.html', {'error': 'Все поля обязательны', 'user': request.user})
        Author.objects.create(full_name=full_name, bio=bio)
        return redirect('home')
    return render(request, 'author_create.html', {'user': request.user})


def create_category(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    if request.method == 'POST':
        name = request.POST.get('name')
        if not name:
            return render(request, 'category_create.html', {'error': 'Название обязательно', 'user': request.user})
        Category.objects.create(name=name)
        return redirect('home')
    return render(request, 'category_create.html', {'user': request.user})
