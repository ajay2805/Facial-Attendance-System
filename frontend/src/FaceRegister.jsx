import React, { useState, useRef } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import Swal from 'sweetalert2';

const FaceRegister = () => {
    const webcamRef = useRef(null);
    const [name, setName] = useState('');
    const [isRegistering, setIsRegistering] = useState(false);
    const [capturedImage, setCapturedImage] = useState(null);

    const handleCapture = () => {
        const imageSrc = webcamRef.current.getScreenshot();
        if (imageSrc) {
            setCapturedImage(imageSrc);
        } else {
            Swal.fire('Error', 'Could not capture image from webcam', 'error');
        }
    };

    const handleRetake = () => {
        setCapturedImage(null);
    };

    const handleRegister = async () => {
        if (!name) return Swal.fire('Error', 'Please enter a name', 'error');
        if (!capturedImage) return Swal.fire('Error', 'Please capture an image first', 'error');
        
        setIsRegistering(true);
        try {
            const blob = await (await fetch(capturedImage)).blob();
            const formData = new FormData();
            formData.append('image', blob, 'register.jpg');
            formData.append('name', name);

            const res = await axios.post('http://localhost:8000/api/register/', formData);
            Swal.fire('Success', res.data.message, 'success');
            
            // Reset form
            setName('');
            setCapturedImage(null);
        } catch (err) {
            Swal.fire('Error', err.response?.data?.error || 'Registration failed', 'error');
        } finally {
            setIsRegistering(false);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center', width: '100%' }}>
            <div style={{ width: '100%' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: '#475569' }}>Name</label>
                <input 
                    type="text" 
                    placeholder="Enter Employee Name" 
                    value={name} 
                    onChange={(e) => setName(e.target.value)}
                    style={{ 
                        padding: '12px', 
                        borderRadius: '12px', 
                        border: '1px solid #e2e8f0', 
                        width: '100%',
                        fontSize: '1rem',
                        outline: 'none',
                        transition: 'border-color 0.2s'
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#4f46e5'}
                    onBlur={(e) => e.target.style.borderColor = '#e2e8f0'}
                />
            </div>

            <div style={{ width: '100%', position: 'relative', minHeight: '200px', background: '#f1f5f9', borderRadius: '16px', overflow: 'hidden' }}>
                {!capturedImage ? (
                    <>
                        <Webcam 
                            ref={webcamRef} 
                            screenshotFormat="image/jpeg" 
                            style={{ width: '100%', display: 'block' }} 
                        />
                        <div style={{ padding: '16px', textAlign: 'center' }}>
                            <button 
                                onClick={handleCapture}
                                style={{ 
                                    padding: '12px 24px', 
                                    background: '#4f46e5', 
                                    color: 'white', 
                                    border: 'none', 
                                    borderRadius: '12px', 
                                    cursor: 'pointer',
                                    fontWeight: 600,
                                    width: '100%'
                                }}
                            >
                                📸 Capture Photo
                            </button>
                        </div>
                    </>
                ) : (
                    <>
                        <img 
                            src={capturedImage} 
                            alt="Captured" 
                            style={{ width: '100%', display: 'block' }} 
                        />
                        <div style={{ padding: '16px', display: 'flex', gap: '12px' }}>
                            <button 
                                onClick={handleRetake}
                                style={{ 
                                    flex: 1,
                                    padding: '12px', 
                                    background: '#f1f5f9', 
                                    color: '#475569', 
                                    border: '1px solid #cbd5e1', 
                                    borderRadius: '12px', 
                                    cursor: 'pointer',
                                    fontWeight: 600
                                }}
                            >
                                🔄 Retake
                            </button>
                            <button 
                                onClick={handleRegister} 
                                disabled={isRegistering}
                                style={{ 
                                    flex: 2,
                                    padding: '12px', 
                                    background: '#10b981', 
                                    color: 'white', 
                                    border: 'none', 
                                    borderRadius: '12px', 
                                    cursor: 'pointer',
                                    fontWeight: 600,
                                    opacity: isRegistering ? 0.7 : 1
                                }}
                            >
                                {isRegistering ? 'Registering...' : '✅ Confirm & Register'}
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default FaceRegister;
