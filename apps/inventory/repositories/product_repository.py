from apps.inventory.models import Product


class ProductRepository:
    @staticmethod
    def get_queryset():
        return Product.objects.all()

    @staticmethod
    def get_product(product_id):
        return Product.objects.filter(id=product_id).first()

    @staticmethod
    def create_product(**validated_data):
        return Product.objects.create(**validated_data)

    @staticmethod
    def update_product(product, **validated_data):
        for attr, value in validated_data.items():
            setattr(product, attr, value)
        product.save()
        return product

    @staticmethod
    def delete_product(product):
        product.delete()
