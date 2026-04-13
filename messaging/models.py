from django.db import models
from django.conf import settings

class Thread(models.Model):
    """
    Represents a private conversation between users. 
    Typically exactly 2 participants (Candidate and Employer).
    """
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='threads')
    job_application = models.ForeignKey('jobs.Application', on_delete=models.SET_NULL, null=True, blank=True, related_name='threads')
    group_name = models.CharField(max_length=150, null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Thread {self.id} - updated {self.updated_at}"

    def get_other_participant(self, user):
        """Helper to get the user they are talking to in a 1-on-1 thread."""
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    """
    An individual encrypted message within a Thread.
    The content is never stored in plain text.
    """
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    
    # Store the AES-256 Fernet token
    encrypted_content = models.BinaryField()
    cryptographic_signature = models.TextField(blank=True, help_text="RSA PKCS#1v1.5 signature of plain text message")
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg from {self.sender.email} at {self.created_at}"
