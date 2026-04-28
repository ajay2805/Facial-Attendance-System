import { FaCamera, FaTimes, FaUserCheck, FaMapMarkerAlt } from 'react-icons/fa';
import Webcam from 'react-webcam';
import axios from 'axios';
import Swal from 'sweetalert2';
import { useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import '../styles/FaceAttendance.css';

const API_URL = import.meta.env.VITE_API_URL;

const FaceAttendance = ({ onSuccess }) => {
  const webcamRef = useRef(null);
  const [showCamera, setShowCamera] = useState(false);
  const [location, setLocation] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [locationLoading, setLocationLoading] = useState(false);

  const showFaceAlert = (config) => Swal.fire({
    ...config,
    toast: false,
    position: 'center',
    heightAuto: false,
    customClass: {
      container: 'face-swal-container',
      popup: 'face-swal-popup',
      ...config.customClass,
    },
  });

  const getCurrentLocation = () => {
    setLocationError(null);
    setLocationLoading(true);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        position => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
          setLocationLoading(false);
        },
        error => {
          console.error('Location error: ', error);
          let errorMessage = 'Could not fetch location';
          if (error.code === error.PERMISSION_DENIED) {
            errorMessage = 'Location access is required for attendance.';
          } else if (error.code === error.POSITION_UNAVAILABLE) {
            errorMessage = 'Location signal is weak or unavailable.';
          }
          setLocationError(errorMessage);
          setLocationLoading(false);
        }
      );
    } else {
      setLocationError('Geolocation is not supported by this browser.');
      setLocationLoading(false);
    }
  };

  const retryCamera = () => {
    setCameraError(null);
    setShowCamera(false);
    setTimeout(() => setShowCamera(true), 100);
  };

  const handleCaptureAndMark = async () => {
    if (!location) {
      if (locationError) {
        showFaceAlert({
            title: 'Location Required',
            text: locationError,
            icon: 'warning',
            confirmButtonColor: '#3b82f6'
        });
      } else {
        getCurrentLocation();
      }
      return;
    }

    setIsProcessing(true);

    const imageSrc = webcamRef.current.getScreenshot();
    if (!imageSrc) {
      showFaceAlert({
        title: 'Error',
        text: 'Could not capture image. Please try again.',
        icon: 'error',
        confirmButtonColor: '#ef4444',
      });
      setIsProcessing(false);
      return;
    }
    const blob = await (await fetch(imageSrc)).blob();

    const formData = new FormData();
    formData.append('image', blob, `face.jpg`);
    formData.append('latitude', location.latitude);
    formData.append('longitude', location.longitude);

    try {
      const res = await axios.post(`${API_URL}/faceapp/mark-attendance/`, formData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      showFaceAlert({
          title: 'Check-In Successful',
          text: res.data.message || 'Biometric attendance recorded!',
          icon: 'success',
          confirmButtonColor: '#10b981'
      });
      if (onSuccess) onSuccess();
      setShowCamera(false);
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Face not recognized. Please try again.';
      
      if (errorMsg.includes('already marked')) {
          showFaceAlert({
              title: 'Already Checked In',
              text: errorMsg,
              icon: 'info',
              confirmButtonColor: '#3b82f6'
          });
          if (onSuccess) onSuccess(); // Optionally refresh to reflect proper state
          setShowCamera(false);
      } else {
          showFaceAlert({
              title: 'Verification Failed',
              text: errorMsg,
              icon: 'error',
              confirmButtonColor: '#ef4444'
          });
      }
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div>
      <button
        onClick={() => {
          setShowCamera(true);
          getCurrentLocation();
        }}
        className="face-scan-btn"
      >
        <span className="btn-content">
          <FaCamera />
          <span>Scan Face</span>
        </span>
      </button>

      {showCamera && createPortal(
        <div className="face-modal-overlay" onClick={() => setShowCamera(false)}>
          <div className="face-modal-content" onClick={(event) => event.stopPropagation()}>
            <button className="face-close-btn" onClick={() => setShowCamera(false)}>
              <FaTimes />
            </button>

            <div style={{ 
                textAlign: 'center', 
                background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
                margin: '-32px -32px 24px -32px',
                padding: '20px 16px',
                borderTopLeftRadius: '24px',
                borderTopRightRadius: '24px',
                width: 'calc(100% + 64px)',
                flexShrink: 0
            }}>
                <h3 style={{ margin: 0, color: '#ffffff', fontSize: '1.15rem', fontWeight: 700 }}>Face Attendance</h3>
            </div>

            {cameraError ? (
              <div className="permission-error-container" style={{ textAlign: 'center', padding: '20px' }}>
                <div style={{ color: '#ef4444', fontSize: '40px', marginBottom: '16px' }}><FaCamera /></div>
                <p className="error-text" style={{ color: '#ef4444', fontWeight: 600, marginBottom: '16px' }}>{cameraError}</p>
                <button 
                  className="face-capture-btn" 
                  onClick={retryCamera}
                  style={{ background: '#3b82f6' }}
                >
                    Grant Permission
                </button>
              </div>
            ) : (
              <div
                className="webcam-wrapper"
                style={{ position: 'relative', width: '100%', display: 'flex', justifyContent: 'center' }}
              >
                <Webcam
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    className="face-webcam"
                    onUserMediaError={(err) => {
                        console.error('Camera error:', err);
                        setCameraError('Camera access denied. Please check site permissions.');
                    }}
                />
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: '200px',
                    height: '240px',
                    border: '2px dashed rgba(255,255,255,0.5)',
                    borderRadius: '100px',
                    pointerEvents: 'none'
                }}></div>
              </div>
            )}

            <div className="face-btn-container">
              {!location && !locationLoading && (
                <div className="location-warning">
                  {locationError ? (
                    <>
                      <span><FaMapMarkerAlt /> {locationError}</span>
                      <button className="location-retry-btn" onClick={getCurrentLocation}>
                        Retry Location Access
                      </button>
                    </>
                  ) : (
                    <span><FaMapMarkerAlt /> Authenticating location...</span>
                  )}
                </div>
              )}
              
              {locationLoading && (
                <div className="location-warning">
                   <span>Fetching GPS coordinates...</span>
                </div>
              )}

              {location && (
                 <div style={{ color: '#10b981', fontSize: '12px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <FaMapMarkerAlt /> Location Verified
                 </div>
              )}

              <button
                className="face-capture-btn"
                onClick={handleCaptureAndMark}
                disabled={isProcessing || !!cameraError || !location}
              >
                {isProcessing ? (
                  <>
                    <div className="loader-spin" style={{ width: '20px', height: '20px' }}></div>
                    <span>Verifying...</span>
                  </>
                ) : (
                  <>
                    <FaUserCheck />
                    <span>Capture & Mark Attendance</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default FaceAttendance;
