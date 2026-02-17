from django.db import transaction
from rest_framework import serializers
from .models import Product, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image']

    def get_image(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    images_upload = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    discounted_price = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'product_model',
            'product_dimension',
            'description',
            'price',
            'discount_percentage',
            'discounted_price',
            'promotion_text',
            'is_active',
            'quantity',
            'created_by',
            'created_at',
            'updated_at',
            'images',
            'images_upload'
        ]

    def get_discounted_price(self, obj):
        return obj.discounted_price()

    def create(self, validated_data):
        images_data = validated_data.pop('images_upload', [])

        with transaction.atomic():
            product = Product.objects.create(**validated_data)

            for image in images_data:
                ProductImage.objects.create(
                    product=product,
                    image=image
                )

        return product

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images_upload', None)

        # update product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # replace images if new ones uploaded
        if images_data is not None:
            with transaction.atomic():
                instance.images.all().delete()

                for image in images_data:
                    ProductImage.objects.create(
                        product=instance,
                        image=image
                    )

        return instance
