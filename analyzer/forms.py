from django import forms
from .models import AudioFile

class AudioUploadForm(forms.ModelForm):
    class Meta:
        model = AudioFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'accept': 'audio/*'})
        }