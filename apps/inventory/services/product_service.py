from django.db.models import Q

from apps.inventory.repositories.product_repository import ProductRepository


class ProductService:
    @staticmethod
    def list_products(params):
        queryset = ProductRepository.get_queryset()

        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(sku__icontains=search)
            )

        min_price = params.get("min_price")
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)

        max_price = params.get("max_price")
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        in_stock = params.get("in_stock")
        if in_stock is not None:
            if in_stock.lower() in ["true", "1", "yes"]:
                queryset = queryset.filter(stock__gt=0)
            elif in_stock.lower() in ["false", "0", "no"]:
                queryset = queryset.filter(stock__lte=0)

        ordering = params.get("ordering")
        if ordering:
            queryset = queryset.order_by(ordering)

        return queryset

    @staticmethod
    def create_product(validated_data):
        return ProductRepository.create_product(**validated_data)

    @staticmethod
    def update_product(product, validated_data):
        return ProductRepository.update_product(product, **validated_data)

    @staticmethod
    def delete_product(product):
        ProductRepository.delete_product(product)
