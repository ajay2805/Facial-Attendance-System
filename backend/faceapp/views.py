import os
import json
import logging
import torch
import numpy as np
from PIL import Image, ImageOps
from io import BytesIO
from django.conf import settings
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from facenet_pytorch import MTCNN, InceptionResnetV1
from .models import Person, AttendanceRecord

logger = logging.getLogger(__name__)

# Initialize AI models
device = torch.device('cpu')
mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20, thresholds=[0.6, 0.7, 0.7], device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

def _get_encoding(image_file):
    img = Image.open(image_file).convert('RGB')
    img = ImageOps.exif_transpose(img)
    face = mtcnn(img)
    if face is None:
        return None
    with torch.no_grad():
        encoding = resnet(face.unsqueeze(0)).cpu().numpy()[0]
    return encoding.tolist()

@method_decorator(csrf_exempt, name='dispatch')
class RegisterFaceView(View):
    def post(self, request):
        name = request.POST.get('name')
        image_file = request.FILES.get('image')

        if not name or not image_file:
            return JsonResponse({'error': 'Name and Image are required'}, status=400)

        encoding = _get_encoding(image_file)
        if encoding is None:
            return JsonResponse({'error': 'No face detected. Try again.'}, status=400)

        person = Person.objects.create(name=name)
        person.set_encoding(encoding)
        person.save()

        return JsonResponse({'message': f'Face registered successfully for {name}!'})

@method_decorator(csrf_exempt, name='dispatch')
class MarkAttendanceView(View):
    def post(self, request):
        image_file = request.FILES.get('image')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')

        if not image_file:
            return JsonResponse({'error': 'Image is required'}, status=400)

        unknown_encoding = _get_encoding(image_file)
        if unknown_encoding is None:
            return JsonResponse({'error': 'No face detected in scan.'}, status=400)
        
        unknown_encoding = np.array(unknown_encoding)
        best_match = None
        highest_sim = 0

        # Compare against all registered people
        for person in Person.objects.all():
            known_encoding = np.array(person.get_encoding())
            # Cosine Similarity
            sim = np.dot(known_encoding, unknown_encoding) / (np.linalg.norm(known_encoding) * np.linalg.norm(unknown_encoding))
            
            if sim > highest_sim:
                highest_sim = sim
                if sim > 0.7: # Threshold
                    best_match = person

        if best_match:
            AttendanceRecord.objects.create(
                person=best_match,
                latitude=lat,
                longitude=lng
            )
            return JsonResponse({'message': f'Attendance marked for {best_match.name}!', 'similarity': round(float(highest_sim), 2)})
        
        return JsonResponse({'error': 'Face not recognized.', 'similarity': round(float(highest_sim), 2)}, status=403)
