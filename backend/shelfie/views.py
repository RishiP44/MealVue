import logging
import io
from PIL import Image, UnidentifiedImageError
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from .models import LibraryBook
from .serializers import (
    LibraryBookSerializer,
    LibraryConfirmRequestSerializer,
    MatchCorrectionRequestSerializer,
)
from .services.pipeline import get_default_pipeline
from .services.matcher import get_default_matcher

logger = logging.getLogger(__name__)

# Maximum allowed image upload size (15 MB)
MAX_IMAGE_SIZE_BYTES = 15 * 1024 * 1024


def error_response(code: str, message: str, http_status=status.HTTP_400_BAD_REQUEST) -> Response:
    """Standardized API error response format."""
    return Response(
        {
            "error": {
                "code": code,
                "message": message,
            }
        },
        status=http_status,
    )


@api_view(["GET"])
def health_check(request):
    """Health check endpoint returning HTTP 200 and {'status': 'ok'}."""
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def analyze_shelf(request):
    """
    POST /api/analyze/
    Accepts multipart/form-data with 'image' file.
    Executes: Detection -> Crop -> Hosted VLM -> Deterministic Matcher.
    Returns transient analysis result with items, summary, and pipeline metrics.
    """
    if "image" not in request.FILES:
        return error_response("missing_image", "An 'image' file field is required in multipart/form-data.")

    image_file = request.FILES["image"]

    if image_file.size > MAX_IMAGE_SIZE_BYTES:
        return error_response(
            "image_too_large",
            f"Uploaded image size ({image_file.size} bytes) exceeds maximum limit of {MAX_IMAGE_SIZE_BYTES} bytes."
        )

    try:
        raw_bytes = image_file.read()
        pil_image = Image.open(io.BytesIO(raw_bytes))
        pil_image.verify()  # Fast structural verification
        # Re-open after verify() closes the stream
        pil_image = Image.open(io.BytesIO(raw_bytes))
    except (UnidentifiedImageError, Exception) as exc:
        logger.warning(f"Image decode failed: {exc}")
        return error_response("invalid_image", "The uploaded file could not be decoded as a valid image.")

    pipeline = get_default_pipeline()

    try:
        result = pipeline.analyze_image(pil_image)
        return Response(result.to_dict(), status=status.HTTP_200_OK)
    except ValueError as exc:
        # Handles missing API key or configuration error
        err_msg = str(exc)
        if "OPENROUTER_API_KEY" in err_msg:
            return error_response(
                "configuration_error",
                "Vision-Language service is not configured on the server.",
                http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return error_response("pipeline_error", err_msg, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as exc:
        logger.exception(f"Unexpected pipeline failure: {exc}")
        return error_response(
            "pipeline_failure",
            "An unexpected error occurred during bookshelf analysis.",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@parser_classes([JSONParser])
def match_correction(request):
    """
    POST /api/match/
    Reruns deterministic catalog matching on user-corrected title/author text.
    Does NOT call detector, VLM, or modify database.
    """
    serializer = MatchCorrectionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            "invalid_request",
            serializer.errors.get("non_field_errors", ["Invalid title or author input."])[0]
        )

    title = serializer.validated_data.get("title")
    author = serializer.validated_data.get("author")

    matcher = get_default_matcher()
    match_result = matcher.match_book(title=title, author=author, limit=3)

    return Response(match_result.to_dict(), status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@parser_classes([JSONParser])
def library_books(request):
    """
    GET /api/library/
    Returns all confirmed books in the personal library ordered by -added_at.

    POST /api/library/
    Persists one or multiple confirmed books into the SQLite personal library.
    Deduplicates cleanly if a catalog_id already exists in the library.
    """
    if request.method == "GET":
        books = LibraryBook.objects.all()
        serializer = LibraryBookSerializer(books, many=True)
        return Response(
            {
                "count": books.count(),
                "books": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    elif request.method == "POST":
        serializer = LibraryConfirmRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("invalid_request", str(serializer.errors))

        books_to_add = serializer.validated_data.get("books", [])
        if not books_to_add:
            return error_response("empty_request", "No valid books provided for addition.")

        persisted_books = []
        added_count = 0
        duplicate_count = 0

        for b_data in books_to_add:
            cat_id = b_data.get("catalog_id")
            title = b_data.get("confirmed_title")
            author = b_data.get("confirmed_author")
            edition = b_data.get("edition")
            conf = b_data.get("source_match_confidence")

            # Duplicate check policy by catalog_id
            if cat_id:
                existing = LibraryBook.objects.filter(catalog_id=cat_id).first()
                if existing:
                    duplicate_count += 1
                    persisted_books.append(existing)
                    continue

            # Also prevent exact title+author duplicates if catalog_id is absent
            if not cat_id and title:
                existing = LibraryBook.objects.filter(
                    confirmed_title__iexact=title.strip(),
                    confirmed_author__iexact=(author or "").strip()
                ).first()
                if existing:
                    duplicate_count += 1
                    persisted_books.append(existing)
                    continue

            new_book = LibraryBook.objects.create(
                catalog_id=cat_id,
                confirmed_title=title,
                confirmed_author=author,
                edition=edition,
                source_match_confidence=conf,
            )
            added_count += 1
            persisted_books.append(new_book)

        out_serializer = LibraryBookSerializer(persisted_books, many=True)
        return Response(
            {
                "status": "success",
                "added_count": added_count,
                "duplicate_count": duplicate_count,
                "books": out_serializer.data,
            },
            status=status.HTTP_201_CREATED if added_count > 0 else status.HTTP_200_OK,
        )
