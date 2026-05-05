# AI-Driven Facial Recognition Attendance System

A high-performance biometric attendance solution using **Deep Learning (Facenet-PyTorch)** to eliminate "buddy punching" and ensure 100% accurate time tracking.

## 🚀 Key Features

- **Advanced Computer Vision:** Powered by **Facenet-PyTorch** for state-of-the-art face detection and recognition.
- **Biometric Edge Processing:** 
  - **MTCNN (Multi-task Cascaded Convolutional Networks):** For highly accurate face detection even in low-light or angled conditions.
  - **InceptionResnetV1 (VGGFace2):** For generating high-dimensional (128d) facial embeddings.
- **Cosine Similarity Verification:** Uses mathematical vector comparison with a strict threshold (0.65) to verify identities with minimal false positives.
- **Geofenced Verification:** Captures GPS coordinates (Latitude/Longitude) during scans and performs **Reverse Geocoding** to log the exact physical location of the punch.
- **Zero-Wait Training:** Unlike older systems, this implementation uses **one-shot learning** logic; once a face is registered, it is instantly recognizable across the system without overnight training cycles.
- **Audit Trail:** Automatically saves a JPEG scan of every successful verification for administrative review and audit compliance.

## 🛠️ Technology Stack

- **Backend:** Python / Django / PyTorch
- **Deep Learning Libraries:** 
  - `facenet-pytorch`
  - `torch` / `torchvision`
  - `Pillow (PIL)` (Image preprocessing)
- **Frontend:** React / Webcam API / Canvas API
- **Location Services:** Nominatim OpenStreetMap API (Reverse Geocoding)
- **Database:** PostgreSQL (Storing facial embeddings as JSON vectors)

## 📂 Project Structure

- `backend/`: 
  - `views.py`: Contains the `FaceAttendanceView` for real-time verification and `FaceRegisterView` for onboarding.
  - `models.py`: Database schema for storing facial metadata and audit logs.
- `frontend/`:
  - `FaceAttendance.jsx`: React component that handles the webcam stream, frame capture, and location fetching.

## 🧠 Technical Workflow

1. **Onboarding:** Employee registers their face at different angles. The MTCNN detector crops the face, and InceptionResnetV1 converts it into a unique numerical vector (embedding).
2. **Scan:** When an employee scans their face via the webcam, a new vector is generated from the live frame.
3. **Comparison:** The system performs a **Cosine Similarity** calculation between the live vector and the stored vectors for that specific employee.
4. **Validation:** If the similarity exceeds 0.65, the attendance is marked as successful, and the punch is synced with the main time tracking system.

---
*Developed as a high-security biometric module for the FirstClick HRMS Unified Platform.*
