from rest_framework import serializers
from .models import Deck, Card

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'front', 'back', 'deck']

class DeckSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)

    class Meta:
        model = Deck
        fields = ['id', 'name', 'description', 'cards']