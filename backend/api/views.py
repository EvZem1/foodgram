from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserUserViewSet

from .filters import RecipeFilter
from .models import (
    Tag, Ingredient, Recipe, Favorite,
    ShoppingCart, Subscription
)
from .serializers import (
    UserSerializer, TagSerializer, IngredientSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, RecipeMinifiedSerializer
)

User = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписываться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.method == 'POST':
            if Subscription.objects.filter(user=request.user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=request.user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(user=request.user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Вы не были подписаны на этого автора'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = self.get_serializer(pages, many=True)
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для тегов.
    Разрешены только безопасные методы (GET).
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None  # Отключаем пагинацию для тегов


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для ингредиентов.
    Разрешены только безопасные методы (GET).
    Поиск по названию.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None # Отключаем пагинацию для ингредиентов


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не в избранном'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        cart_item = ShoppingCart.objects.filter(user=request.user, recipe=recipe)
        if cart_item.exists():
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепта нет в списке покупок'},
            status=status.HTTP_400_BAD_REQUEST
        )
    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = user.shopping_cart.all()
        ingredients = {}

        for item in shopping_cart:
            recipe_ingredients = item.recipe.ingredients.through.objects.filter(
                recipe=item.recipe
            )
            for ri in recipe_ingredients:
                name = ri.ingredient.name
                measurement_unit = ri.ingredient.measurement_unit
                amount = ri.amount
                if name in ingredients:
                    ingredients[name]['amount'] += amount
                else:
                    ingredients[name] = {
                        'amount': amount,
                        'measurement_unit': measurement_unit
                    }
        
        shopping_list_text = "Список покупок:\n\n"
        for name, data in ingredients.items():
            shopping_list_text += (
                f"- {name} ({data['measurement_unit']}) — {data['amount']}\n"
            )

        response = HttpResponse(shopping_list_text, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response
