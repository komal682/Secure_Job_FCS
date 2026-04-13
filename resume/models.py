from django.db import models
from django.conf import settings

class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes', null=True, blank=True)
    encrypted_file = models.BinaryField()
    original_filename = models.CharField(max_length=255)
    parsed_keywords = models.TextField(blank=True, help_text="AI Extracted keywords from the raw PDF")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.original_filename}"
