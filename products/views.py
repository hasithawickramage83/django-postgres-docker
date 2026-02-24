# from rest_framework import viewsets
# from .models import Product
# from .serializers import ProductSerializer
# from rest_framework.permissions import IsAuthenticated
#
# class ProductViewSet(viewsets.ModelViewSet):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#     permission_classes = [IsAuthenticated]  # Set [] for public access
#
#     def perform_create(self, serializer):
#         serializer.save(created_by=self.request.user)
from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer
from .permissions import IsAdminUserOrReadOnly

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_serializer_context(self):
        return {"request": self.request}