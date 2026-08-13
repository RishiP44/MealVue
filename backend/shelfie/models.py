from django.db import models


class LibraryBook(models.Model):
    """
    Persisted personal library book confirmed explicitly by the user.
    Scan and review states remain transient; only confirmed books are saved here.
    """
    catalog_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    confirmed_title = models.CharField(max_length=255)
    confirmed_author = models.CharField(max_length=255, null=True, blank=True)
    edition = models.CharField(max_length=100, null=True, blank=True)
    source_match_confidence = models.FloatField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at", "-id"]
        verbose_name = "Library Book"
        verbose_name_plural = "Library Books"

    def __str__(self):
        author_str = f" by {self.confirmed_author}" if self.confirmed_author else ""
        return f"{self.confirmed_title}{author_str}"
