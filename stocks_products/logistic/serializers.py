from rest_framework import serializers
from logistic.models import Product, StockProduct, Stock


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'description']


class ProductPositionSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    class Meta:
        model = StockProduct
        fields = ['product', 'quantity', 'price']


class StockSerializer(serializers.ModelSerializer):
    positions = ProductPositionSerializer(many=True)

    class Meta:
        model = Stock
        fields = ['id', 'address', 'positions']

    def create(self, validated_data):
        positions = validated_data.pop('positions')
        stock = super().create(validated_data)

        for position in positions:
            StockProduct.objects.create(stock=stock, **position)

        return stock

    def update(self, instance, validated_data):
        positions_data = validated_data.pop('positions')
        stock = super().update(instance, validated_data)

        # Получаем текущие позиции на складе
        current_position_ids = []

        for position_data in positions_data:
            product = position_data.get('product')
            quantity = position_data.get('quantity')
            price = position_data.get('price')

            # Используем update_or_create для обновления или создания новых позиций
            stock_product, created = StockProduct.objects.update_or_create(
                stock=stock,
                product=product,
                defaults={'quantity': quantity, 'price': price}
            )

            current_position_ids.append(stock_product.id)

        # Удаляем старые позиции, которые не пришли в запросе
        stock.positions.exclude(id__in=current_position_ids).delete()

        return stock


