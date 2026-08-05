from django.shortcuts import render
from rest_framework import viewsets
from .models import Deck, Card
from .serializers import DeckSerializer, CardSerializer

class DeckViewSet(viewsets.ModelViewSet):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer