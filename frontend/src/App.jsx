import React, { useState } from 'react';
import FaceRegister from './FaceRegister';
import FaceAttendance from './FaceAttendance';

function App() {
  const [activeTab, setActiveTab] = useState('attendance');

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      padding: '40px',
      minHeight: '100vh',
      backgroundColor: '#f8fafc',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      <div style={{ background: 'white', padding: '32px', borderRadius: '24px', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)', width: '100%', maxWidth: '400px' }}>
        <h1 style={{ textAlign: 'center', color: '#1e293b', marginBottom: '24px' }}>Face Attendance</h1>
        
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', background: '#f1f5f9', padding: '4px', borderRadius: '12px' }}>
          <button 
            onClick={() => setActiveTab('attendance')}
            style={{ flex: 1, padding: '10px', border: 'none', borderRadius: '8px', background: activeTab === 'attendance' ? 'white' : 'transparent', fontWeight: 600, cursor: 'pointer', boxShadow: activeTab === 'attendance' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none' }}
          >
            Scan Face
          </button>
          <button 
            onClick={() => setActiveTab('register')}
            style={{ flex: 1, padding: '10px', border: 'none', borderRadius: '8px', background: activeTab === 'register' ? 'white' : 'transparent', fontWeight: 600, cursor: 'pointer', boxShadow: activeTab === 'register' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none' }}
          >
            Register
          </button>
        </div>

        {activeTab === 'register' ? <FaceRegister /> : <FaceAttendance />}
      </div>
    </div>
  );
}

export default App;
