from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (Tag, Ingredient, Recipe, Favorite, ShoppingCart,
                     Subscription, RecipeIngredient) # <-- ДОБАВЛЕН ИМПОРТ
from .serializers import (UserSerializer, TagSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          RecipeMinifiedSerializer)
from .filters import RecipeFilter

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
            if request.user.follower.filter(author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=request.user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = request.user.follower.filter(author=author)
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
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
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
            if request.user.favorites.filter(recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        favorite = request.user.favorites.filter(recipe=recipe)
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
            if request.user.shopping_cart.filter(recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        cart_item = request.user.shopping_cart.filter(recipe=recipe)
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
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__in_shopping_cart__user=request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        shopping_list_text = "Список покупок:\n\n"
        for item in ingredients:
            shopping_list_text += (
                f"- {item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total_amount']}\n"
            )

        response = HttpResponse(shopping_list_text, content_type='text/plain')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_list.txt"')
        return response
