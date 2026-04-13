from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
User = get_user_model()
class CandidateRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return cleaned_data
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
class EmployerRegistrationForm(CandidateRegistrationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
from .models import CandidateProfile
class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['photo', 
                  'headline', 'location', 'bio', 'summary', 'skills',
                  'visibility',
                  'privacy_photo', 'privacy_headline', 'privacy_location', 'privacy_bio',
                  'privacy_summary', 'privacy_education', 'privacy_experience', 'privacy_skills',
                  'opt_out_view_tracking']
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'location': forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'summary': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500', 'placeholder': 'Python, SQL, React, ...'}),
            'visibility': forms.Select(attrs={'class': 'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md'}),
            'privacy_photo': forms.Select(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md'}),
            'privacy_headline': forms.Select(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md'}),
            'privacy_location': forms.Select(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md'}),
            'privacy_bio': forms.Select(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md'}),
            'privacy_summary': forms.Select(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md'}),
            'privacy_education': forms.Select(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md'}),
            'privacy_experience': forms.Select(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md'}),
            'privacy_skills': forms.Select(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md'}),
            'opt_out_view_tracking': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'})
        }
from .models import Education
class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['school', 'degree', 'field_of_study', 'start_month', 'start_year', 'end_month', 'end_year', 'grade']
