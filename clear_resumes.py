import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from resume.models import Resume
Resume.objects.all().delete()
print('Cleared old resumes to allow schema migration.')
