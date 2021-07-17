import django_filters
from django_filters import NumberFilter, CharFilter
from .models import *


class ProductFilter(django_filters.FilterSet):
    name = CharFilter(field_name="name", lookup_expr='icontains')
    price_from = NumberFilter(field_name="price", lookup_expr='gte')
    price_to = NumberFilter(field_name="price", lookup_expr='lte')

    class Meta:
        model = Product
        fields = {
        }
