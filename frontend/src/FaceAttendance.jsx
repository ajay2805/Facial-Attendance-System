import React, { useState, useRef } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import Swal from 'sweetalert2';

const FaceAttendance = () => {
    const webcamRef = useRef(null);
    const [isProcessing, setIsProcessing] = useState(false);

    const handleAttendance = async () => {
        setIsProcessing(true);

        // Get Location
        navigator.geolocation.getCurrentPosition(async (pos) => {
            const imageSrc = webcamRef.current.getScreenshot();
            if (!imageSrc) {
                setIsProcessing(false);
                return Swal.fire('Error', 'Could not capture image', 'error');
            }

            const blob = await (await fetch(imageSrc)).blob();

            const formData = new FormData();
            formData.append('image', blob, 'scan.jpg');
            formData.append('latitude', pos.coords.latitude);
            formData.append('longitude', pos.coords.longitude);

            try {
                const res = await axios.post('http://localhost:8000/api/mark-attendance/', formData);
                Swal.fire('Success', res.data.message, 'success');
            } catch (err) {
                const errorMsg = err.response?.status === 403 
                    ? '🚫 Face doesn\'t match any registered user.' 
                    : (err.response?.data?.error || 'Recognition failed');
                Swal.fire('Identity Verification', errorMsg, 'error');
            } finally {
                setIsProcessing(false);
            }
        }, (err) => {
            Swal.fire('Error', 'Location access required', 'error');
            setIsProcessing(false);
        });
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center' }}>
            <Webcam ref={webcamRef} screenshotFormat="image/jpeg" style={{ borderRadius: '16px', width: '100%' }} />
            <button 
                onClick={handleAttendance} 
                disabled={isProcessing}
                style={{ padding: '12px 24px', background: '#10b981', color: 'white', border: 'none', borderRadius: '12px', cursor: 'pointer', width: '100%' }}
            >
                {isProcessing ? 'Verifying...' : 'Capture & Mark Attendance'}
            </button>
        </div>
    );
};

export default FaceAttendance;
