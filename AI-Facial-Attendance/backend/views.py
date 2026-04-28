import os
import json
import logging
# import boto3  # Removed S3 dependence
from io import BytesIO
from datetime import datetime

from PIL import Image, ImageOps
import numpy as np
import jwt
import requests
from django.conf import settings
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.utils.timezone import localtime, make_aware, is_naive, now
logger = logging.getLogger(__name__)

try:
    import torch
    from facenet_pytorch import MTCNN, InceptionResnetV1
    # Initialize detector and embedder with more sensitive settings
    device = torch.device('cpu') 
    # thresholds=[0.6, 0.7, 0.7] are defaults; lowering them slightly helps in hard conditions
    mtcnn = MTCNN(
        image_size=160, margin=0, min_face_size=20,
        thresholds=[0.5, 0.6, 0.6], factor=0.709, post_process=True,
        device=device
    )
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
    FACE_RECOGNITION_AVAILABLE = True
except Exception as e:
    FACE_RECOGNITION_AVAILABLE = False
    logger.warning(f"Facenet-PyTorch failed to initialize: {e}")

from .models import Face_Recognization, FaceImageMeta
from core.models import Employee, Status
from timelog.models import TimeLog
from decimal import Decimal
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def _load_face_image(image_file):
    image_file.seek(0)
    with Image.open(image_file) as opened_image:
        img = ImageOps.exif_transpose(opened_image)
        if img.mode != "RGB":
            img = img.convert("RGB")
        else:
            img = img.copy()

    # Use np.array to ensure a base array is created
    img_np = np.array(img, dtype=np.uint8)

    if img_np.ndim != 3 or img_np.shape[2] != 3:
        raise ValueError(f"Unsupported image shape for face recognition: {img_np.shape}")

    # Ensure images are contiguous and explicitly writeable for processing
    if not img_np.flags.c_contiguous or not img_np.flags.writeable:
        img_np = img_np.copy(order='C')

    return img, img_np



@method_decorator(csrf_exempt, name='dispatch')
class FaceRegisterView(View):
    def post(self, request):
        logger.info("Received face registration POST request")

        employee_id = request.POST.get('employee_id')
        username = request.POST.get('username')
        image_file = request.FILES.get('image')
        angle = request.POST.get('angle')

        if not employee_id or not username or not image_file or not angle:
            return JsonResponse({'error': 'Missing data'}, status=400)

        if not FACE_RECOGNITION_AVAILABLE:
            return JsonResponse({'error': 'Face recognition module is not installed on the server.'}, status=503)

        # 1. Read Image
        try:
            img, img_np = _load_face_image(image_file)
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            return JsonResponse({'error': 'Invalid image file'}, status=400)

        # 2. Generate Encoding
        try:
            # Facenet-PyTorch Logic
            # 1. Detect and crop face
            face = mtcnn(img) # mtcnn accepts PIL Image directly
            
            if face is None:
                logger.warning(f"Registration failed: No face detected for {employee_id} at {angle}")
                return JsonResponse({'error': 'No face detected. Please ensure your face is visible and well-lit.'}, status=400)
            
            # 2. Generate embedding
            # Add batch dimension and get embedding
            with torch.no_grad():
                face_embedding = resnet(face.unsqueeze(0)).cpu().numpy()[0].tolist()
            
        except Exception as e:
             logger.error(f"Error generating Facenet encoding: {e}")
             return JsonResponse({'error': f'Failed to process face data: {str(e)}'}, status=500)

        # 3. Save Locally
        relative_path = f"faceapp/dataset/{employee_id}/{angle}.jpg"
        try:
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            
            # Save to default_storage (local media)
            if default_storage.exists(relative_path):
                default_storage.delete(relative_path)
            
            default_storage.save(relative_path, ContentFile(buffer.getvalue()))
            logger.info(f"Saved image locally: {relative_path}")
        except Exception as e:
            return JsonResponse({'error': f'Failed to save locally: {str(e)}'}, status=500)

        # 4. Save Metadata & Encoding to DB
        try:
            employee = Employee.objects.get(employee_id=employee_id)
            FaceImageMeta.objects.create(
                employee=employee,
                angle=angle,
                capture_time=datetime.now(),
                training_status='success',
                image_path=relative_path,
                face_encoding=face_embedding
            )
        except Exception as e:
            return JsonResponse({'error': f"Metadata save failed: {str(e)}"}, status=500)

        return JsonResponse({'message': f'Face data for {angle} registered successfully'})

    # Note: train_model method is REMOVED as it is no longer needed.


@csrf_exempt
def delete_face(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            employee_id = data.get('employee_id')
            if not employee_id:
                return JsonResponse({'error': 'Employee ID required'}, status=400)

            # Delete from S3
            for angle in ['angle_0.jpg', 'angle_1.jpg', 'angle_2.jpg']: # Adjust if extensions vary, or list objects
                 # A more robust way would be to list objects in the prefix
                 pass 
            
            # Simple approach: Delete DB records first, then try to clean S3
            # In a real app, you might want a more robust cleanup
            
            # Delete Local folder
            try:
                folder_path = f"faceapp/dataset/{employee_id}/"
                # This depends on your storage (FileSystemStorage can't delete dirs easily via default_storage)
                # We can delete known files or use shutil
                import shutil
                full_path = os.path.join(settings.MEDIA_ROOT, folder_path)
                if os.path.exists(full_path):
                    shutil.rmtree(full_path)
            except Exception as e:
                logger.warning(f"Local cleanup failed: {e}")

            FaceImageMeta.objects.filter(employee__employee_id=employee_id).delete()
            
            return JsonResponse({'message': 'All face data deleted successfully.'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@method_decorator(csrf_exempt, name="dispatch")
class FaceAttendanceView(View):
    def post(self, request):
        logger.info("FaceAttendanceView POST request received")

        image_file = request.FILES.get("image")
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        location_name = None

        if not image_file:
            return JsonResponse({"error": "No image provided"}, status=400)

        if not FACE_RECOGNITION_AVAILABLE:
            return JsonResponse({"error": "Face recognition module is not installed on the server."}, status=503)

        # 1. Decode JWT to get Employee ID
        try:
            token = auth_header.split()[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            requesting_employee_id = payload.get("employee_id") or payload.get("emp_id")
        except Exception as e:
            return JsonResponse({"error": "Invalid or missing token"}, status=401)

        # 2. Fetch Stored Encodings for this Employee
        try:
            employee = Employee.objects.get(employee_id=requesting_employee_id)
            stored_metas = FaceImageMeta.objects.filter(employee=employee)
            
            known_encodings = []
            for meta in stored_metas:
                if meta.face_encoding:
                     known_encodings.append(np.array(meta.face_encoding))
            
            if not known_encodings:
                return JsonResponse({"error": "No registered face data found. Please register first."}, status=400)
                
        except Employee.DoesNotExist:
            return JsonResponse({"error": "Employee not found"}, status=404)

        # 3. Process Incoming Image
        try:
            img, _ = _load_face_image(image_file)
            
            # Detect and extract faces
            face = mtcnn(img)
            
            if face is None:
                 return JsonResponse({"error": "No face detected. Please ensure your face is visible."}, status=400)
            
            with torch.no_grad():
                unknown_encoding = resnet(face.unsqueeze(0)).cpu().numpy()[0]
            
            match_found = False
            best_sim = 0.0
            
            # Compare against stored encodings (Cosine Similarity)
            for known_encoding in known_encodings:
                known_encoding = np.array(known_encoding)
                
                # Cosine Similarity
                norm_a = np.linalg.norm(known_encoding)
                norm_b = np.linalg.norm(unknown_encoding)
                sim = float(np.dot(known_encoding, unknown_encoding) / (norm_a * norm_b))
                
                if sim > best_sim:
                    best_sim = sim
                
                # Threshold for Facenet vggface2 model is around 0.6-0.7 for cosine
                if sim >= 0.65:
                    match_found = True
                    break
            
            logger.info(f"Face check for {requesting_employee_id}: Best Similarity = {best_sim}")
            
            if not match_found:
                 return JsonResponse({"error": f"Face mismatch. Verification failed (Sim: {best_sim:.2f})"}, status=403)

        except Exception as e:
            logger.error(f"Facenet recognition pipeline failed: {e}")
            return JsonResponse({"error": f"Recognition failed: {str(e)}"}, status=500)

        # 4. Success - Log Attendance
        # Reverse geocode (Keep existing logic)
        if latitude and longitude:
            try:
                response = requests.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={"lat": latitude, "lon": longitude, "format": "json"},
                    headers={"User-Agent": "attendance-app"},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    location_name = data.get("display_name")
            except Exception as e:
                logger.warning(f"Location lookup failed: {e}")
        
        # Save Scanned Image Locally (Audit Trail)
        try:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            scan_rel_path = f"faceapp/attendance-scans/{requesting_employee_id}/{timestamp_str}.jpg"
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            
            default_storage.save(scan_rel_path, ContentFile(buffer.getvalue()))
        except Exception as e:
            logger.error(f"Failed to save scan: {e}") 
        # Non-critical

        # --- SYNC WITH MAIN TIMELOG SYSTEM ---
        now_dt = timezone.now()
        today = now_dt.date()
        
        # 1. Check Employee Status
        if employee.status != Status.ACTIVE:
            return JsonResponse({"error": f"Cannot mark attendance. Status is {employee.status}"}, status=403)

        # 2. Find or Create TimeLog
        log = TimeLog.objects.filter(employee=employee, punch_date=today).first()
        punch_type = "In"

        if not log:
            # FIRST PUNCH IN today
            log = TimeLog.objects.create(
                employee=employee,
                organization=employee.organization,
                punch_date=today,
                punch_in_time=now_dt.time(),
                initial_punch_in=now_dt.time(),
                status="In",
                work_status="Present",
                total_hours=Decimal('0.00'),
            )
            logger.info(f"Face Scan triggered first Punch-In for {employee.employee_id}")
        else:
            # Already has a log for today. 
            # We just record the scan in Face_Recognization (done below) and don't error out.
            logger.info(f"Face Scan recorded for {employee.employee_id}. TimeLog already exists (Status: {log.status})")
            # If the user is currently 'Out', we could potentially re-punch them 'In' here, 
            # but standardizing with manual punch behavior might be better.
            if log.status == "Out":
                 log.status = "In"
                 log.punch_in_time = now_dt.time()
                 if not log.initial_punch_in:
                     log.initial_punch_in = now_dt.time()
                 log.save()
                 logger.info(f"Face Scan triggered a re-punch-in for {employee.employee_id}")


        # Also keep Face_Recognization audit record
        Face_Recognization.objects.create(
            employee=employee,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
        )

        return JsonResponse({
            "message": f"Facial {punch_type} successful for {employee.first_name}",
            "punch_type": punch_type,
            "time": now_dt.strftime("%H:%M:%S")
        })


@require_GET
def get_face_uploads(request, employee_id):
    data = []
    metas = FaceImageMeta.objects.filter(employee__employee_id=employee_id)
    for meta in metas:
        local_url = f"{settings.MEDIA_URL}{meta.image_path}"

        capture_time = meta.capture_time
        if is_naive(capture_time):
            capture_time = make_aware(capture_time)

        data.append({
            'angle': meta.angle,
            'image_url': local_url,
            'capture_time': localtime(capture_time).strftime('%Y-%m-%d %H:%M:%S'),
            'status': meta.training_status
        })
    return JsonResponse({'uploads': data})

@require_GET
def get_face_scans(request, employee_id):
    try:
        from .models import Face_Recognization
        scans = Face_Recognization.objects.filter(employee__employee_id=employee_id).order_by('-timestamp')
        data = []
        for scan in scans:
            ts = localtime(make_aware(scan.timestamp)) if is_naive(scan.timestamp) else localtime(scan.timestamp)
            data.append({
                'id': scan.id,
                'date': ts.strftime('%Y-%m-%d'),
                'time': ts.strftime('%H:%M:%S'),
                'latitude': scan.latitude,
                'longitude': scan.longitude,
                'location_name': scan.location_name,
            })
        return JsonResponse({'scans': data})
    except Exception as e:
        logger.error(f"Error fetching face scans: {e}")
        return JsonResponse({'error': 'Failed to fetch face scans'}, status=500)

@csrf_exempt
def trigger_training(request):
    # Backward compatibility endpoint (do nothing or return success)
    return JsonResponse({'message': 'Training not required with new system.'})
