from django.db import models
import os
import uuid

def audio_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('audio_uploads/', filename)

class AudioFile(models.Model):
    file = models.FileField(upload_to=audio_file_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    stress_score = models.FloatField(null=True, blank=True)
    feature_breakdown = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"Audio {self.id} - Score: {self.stress_score}"