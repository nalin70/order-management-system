from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from apps.inventory.pagination import ProductPagination
from apps.inventory.permissions import IsAdminOrReadOnly
from apps.inventory.serializers import ProductSerializer
from apps.inventory.services.product_service import ProductService
from apps.inventory.repositories.product_repository import ProductRepository


class ProductListCreateView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        queryset = ProductService.list_products(request.query_params)
        paginator = ProductPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ProductSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(request_body=ProductSerializer)
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = ProductService.create_product(serializer.validated_data)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    @swagger_auto_schema(request_body=ProductSerializer)
    def patch(self, request, pk):
        product = ProductRepository.get_product(pk)
        if not product:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = ProductService.update_product(product, serializer.validated_data)
        return Response(ProductSerializer(product).data)

    def delete(self, request, pk):
        product = ProductRepository.get_product(pk)
        if not product:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        ProductService.delete_product(product)
        return Response(status=status.HTTP_204_NO_CONTENT)
