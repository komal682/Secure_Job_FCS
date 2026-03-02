from django import forms

class ResumeUploadForm(forms.Form):
    resume_file = forms.FileField(label='Upload Resume (PDF/DOCX)')
