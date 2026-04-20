from .models import *
from django_filters import django_filters

class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    author = django_filters.CharFilter(field_name='author__name', lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gt')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lt')

    class Meta:
        model = Book
        fields = ['title', 'author', 'category', 'price_min', 'price_max']