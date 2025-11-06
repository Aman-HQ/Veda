// import React, { useEffect, useState } from 'react';
// import { auth } from '../firebase';
// import { applyActionCode } from 'firebase/auth';
// import { useNavigate, useSearchParams } from 'react-router-dom';
// import axios from 'axios';
// import authStore from '../stores/authStore';

// const VerifyEmail = () => {
//   const [searchParams] = useSearchParams();
//   const navigate = useNavigate();
  
//   const [verifying, setVerifying] = useState(true);
//   const [error, setError] = useState('');
//   const [success, setSuccess] = useState(false);

//   const oobCode = searchParams.get('oobCode');

//   useEffect(() => {
//     if (!oobCode) {
//       setError('Invalid verification link');
//       setVerifying(false);
//       return;
//     }

//     // Apply the email verification code
//     applyActionCode(auth, oobCode)
//       .then(async () => {
//         setSuccess(true);
        
//         // Auto-login: Get user email from Firebase
//         const user = auth.currentUser;
//         if (user) {
//           try {
//             // Get Firebase ID token
//             const idToken = await user.getIdToken();
            
//             // Call backend to auto-login
//             const response = await axios.post(
//               `${import.meta.env.VITE_API_BASE_URL}/auth/verify-and-login`,
//               { firebase_id_token: idToken }
//             );
            
//             // Store tokens using auth store
//             // Access token: Stored in memory (via authStore)
//             // Refresh token: Stored in localStorage (via authStore)
//             const { access_token, refresh_token } = response.data;
            
//             if (access_token && refresh_token) {
//               authStore.setTokens({
//                 accessToken: access_token,
//                 refreshToken: refresh_token
//               });
              
//               // Navigate to chat page
//               navigate('/chat', { 
//                 replace: true,
//                 state: { 
//                   autoLogin: true,
//                   message: 'Email verified successfully!'
//                 }
//               });
//             } else {
//               throw new Error('Invalid response from server');
//             }
            
//           } catch (error) {
//             console.error('Auto-login failed:', error);
//             setError('Verification successful, but auto-login failed. Please login manually.');
//             setVerifying(false);
//             setTimeout(() => navigate('/login'), 3000);
//           }
//         } else {
//           setError('Verification successful! Please login to continue.');
//           setVerifying(false);
//           setTimeout(() => navigate('/login'), 2000);
//         }
//       })
//       .catch((error) => {
//         console.error('Verification error:', error);
        
//         // Provide user-friendly error messages
//         if (error.code === 'auth/invalid-action-code') {
//           setError('Verification link is invalid or has already been used.');
//         } else if (error.code === 'auth/expired-action-code') {
//           setError('Verification link has expired. Please request a new one.');
//         } else {
//           setError('Verification failed. Link may be expired or invalid.');
//         }
        
//         setVerifying(false);
//       });
//   }, [oobCode, navigate]);

//   if (verifying) {
//     return (
//       <div className="verify-email-container" style={styles.container}>
//         <div style={styles.card}>
//           <div style={styles.spinner}></div>
//           <h2 style={styles.title}>Verifying your email...</h2>
//           <p style={styles.subtitle}>Please wait while we confirm your email address.</p>
//         </div>
//       </div>
//     );
//   }

//   if (success) {
//     return (
//       <div className="verify-email-container" style={styles.container}>
//         <div style={styles.card}>
//           <div style={styles.successIcon}>✅</div>
//           <h2 style={styles.title}>Email Verified!</h2>
//           <p style={styles.subtitle}>Your email has been successfully verified.</p>
//           <p style={styles.message}>Logging you in automatically...</p>
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div className="verify-email-container" style={styles.container}>
//       <div style={styles.card}>
//         <div style={styles.errorIcon}>❌</div>
//         <h2 style={styles.title}>Verification Failed</h2>
//         <p style={styles.errorMessage}>{error}</p>
//         <button 
//           onClick={() => navigate('/login')}
//           style={styles.button}
//         >
//           Go to Login
//         </button>
//       </div>
//     </div>
//   );
// };

// // Basic inline styles (you can replace with your CSS classes)
// const styles = {
//   container: {
//     display: 'flex',
//     justifyContent: 'center',
//     alignItems: 'center',
//     minHeight: '100vh',
//     backgroundColor: '#f5f5f5',
//     padding: '20px'
//   },
//   card: {
//     backgroundColor: 'white',
//     borderRadius: '8px',
//     padding: '40px',
//     maxWidth: '400px',
//     width: '100%',
//     boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
//     textAlign: 'center'
//   },
//   spinner: {
//     border: '4px solid #f3f3f3',
//     borderTop: '4px solid #3498db',
//     borderRadius: '50%',
//     width: '40px',
//     height: '40px',
//     animation: 'spin 1s linear infinite',
//     margin: '0 auto 20px'
//   },
//   successIcon: {
//     fontSize: '48px',
//     marginBottom: '20px'
//   },
//   errorIcon: {
//     fontSize: '48px',
//     marginBottom: '20px'
//   },
//   title: {
//     fontSize: '24px',
//     fontWeight: 'bold',
//     marginBottom: '10px',
//     color: '#333'
//   },
//   subtitle: {
//     fontSize: '16px',
//     color: '#666',
//     marginBottom: '10px'
//   },
//   message: {
//     fontSize: '14px',
//     color: '#888'
//   },
//   errorMessage: {
//     fontSize: '16px',
//     color: '#e74c3c',
//     marginBottom: '20px'
//   },
//   button: {
//     backgroundColor: '#3498db',
//     color: 'white',
//     border: 'none',
//     borderRadius: '4px',
//     padding: '12px 24px',
//     fontSize: '16px',
//     cursor: 'pointer',
//     transition: 'background-color 0.3s'
//   }
// };

// export default VerifyEmail;
