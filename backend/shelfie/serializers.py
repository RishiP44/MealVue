from rest_framework import serializers
from typing import Optional, Dict, Any

from .models import LibraryBook
from .services.catalog import get_default_catalog_dict, CatalogEntry


class LibraryBookSerializer(serializers.ModelSerializer):
    """Serializer for persisted personal library books."""

    class Meta:
        model = LibraryBook
        fields = [
            "id",
            "catalog_id",
            "confirmed_title",
            "confirmed_author",
            "edition",
            "source_match_confidence",
            "added_at",
        ]
        read_only_fields = ["id", "added_at"]


class SingleBookConfirmSerializer(serializers.Serializer):
    """Validates confirmation data for an individual book."""
    catalog_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=50)
    confirmed_title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    confirmed_author = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=255)
    edition = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    source_match_confidence = serializers.FloatField(required=False, allow_null=True)

    def validate(self, data):
        catalog_id = data.get("catalog_id")
        title = data.get("confirmed_title", "").strip()

        # If catalog_id is provided, check catalog for canonical values
        if catalog_id:
            catalog_dict = get_default_catalog_dict()
            entry: Optional[CatalogEntry] = catalog_dict.get(catalog_id)
            if entry:
                # Prefer canonical catalog values
                data["confirmed_title"] = entry.title
                data["confirmed_author"] = entry.author
                data["edition"] = entry.edition
            elif not title:
                raise serializers.ValidationError({
                    "confirmed_title": "Title is required for custom/unknown catalog ID."
                })
        elif not title:
            raise serializers.ValidationError({
                "confirmed_title": "Title is required when no catalog_id is provided."
            })

        return data


class LibraryConfirmRequestSerializer(serializers.Serializer):
    """
    Accepts single or batch book confirmation requests:
    { "books": [ { "catalog_id": "BK0001", ... } ] }
    OR { "catalog_id": "BK0001", ... }
    """
    books = SingleBookConfirmSerializer(many=True, required=False)

    def validate(self, data):
        if "books" not in data or not data["books"]:
            # Check if fields were sent at root level (single item)
            single_serializer = SingleBookConfirmSerializer(data=self.initial_data)
            if single_serializer.is_valid(raise_exception=True):
                data["books"] = [single_serializer.validated_data]
        return data


class MatchCorrectionRequestSerializer(serializers.Serializer):
    """Validates user-corrected title/author input for /api/match/."""
    title = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    author = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)

    def validate(self, data):
        t = data.get("title") or ""
        a = data.get("author") or ""
        if not t.strip() and not a.strip():
            raise serializers.ValidationError("At least one of 'title' or 'author' must be provided.")
        return data
