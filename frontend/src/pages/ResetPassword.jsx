// import { useState, useEffect } from 'react';
// import { useNavigate, useSearchParams } from 'react-router-dom';
// import { auth } from '../firebase';
// import { confirmPasswordReset, verifyPasswordResetCode, signInWithEmailAndPassword } from 'firebase/auth';
// import axios from 'axios';
// import AuthLayout from '../components/Layout/AuthLayout.jsx';

// export default function ResetPassword() {
//   const [searchParams] = useSearchParams();
//   const navigate = useNavigate();
  
//   const [newPassword, setNewPassword] = useState('');
//   const [confirmPassword, setConfirmPassword] = useState('');
//   const [loading, setLoading] = useState(false);
//   const [verifying, setVerifying] = useState(true);
//   const [error, setError] = useState('');
//   const [email, setEmail] = useState('');
//   const [codeVerified, setCodeVerified] = useState(false);

//   const oobCode = searchParams.get('oobCode'); // Firebase sends this in the URL
//   const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

//   useEffect(() => {
//     // Verify the reset code when component mounts  
//     if (!oobCode) {
//       setError('No reset code provided. Please request a new password reset link.');
//       setVerifying(false);
//       return;
//     }

//     verifyPasswordResetCode(auth, oobCode)
//       .then((emailAddress) => {
//         setEmail(emailAddress);
//         setCodeVerified(true);
//         setVerifying(false);
//       })
//       .catch((error) => {
//         console.error('Code verification error:', error);
        
//         // Handle specific Firebase errors
//         if (error.code === 'auth/invalid-action-code') {
//           setError('This password reset link is invalid or has already been used.');
//         } else if (error.code === 'auth/expired-action-code') {
//           setError('This password reset link has expired. Please request a new one.');
//         } else {
//           setError('Invalid or expired reset link. Please request a new password reset.');
//         }
//         setVerifying(false);
//       });
//   }, [oobCode]);

//   const handleResetPassword = async (e) => {
//     e.preventDefault();
//     setError('');
    
//     // Validation
//     if (newPassword !== confirmPassword) {
//       setError('Passwords do not match');
//       return;
//     }

//     if (newPassword.length < 8) {
//       setError('Password must be at least 8 characters');
//       return;
//     }

//     setLoading(true);

//     try {
//       // Step 1: Reset password in Firebase
//       await confirmPasswordReset(auth, oobCode, newPassword);
//       console.log('Password reset in Firebase successful');
      
//       // Step 2: Sign in to get Firebase ID token
//       const userCredential = await signInWithEmailAndPassword(auth, email, newPassword);
//       const idToken = await userCredential.user.getIdToken();
//       console.log('Got Firebase ID token');
      
//       // Step 3: Send to backend to sync with PostgreSQL
//       await axios.post(`${apiBase}/api/auth/sync-password`, {
//         firebase_id_token: idToken,
//         new_password: newPassword  // Backend will hash this
//       });
//       console.log('Password synced to PostgreSQL');

//       // Success! Navigate to login
//       setTimeout(() => {
//         navigate('/login', { 
//           state: { 
//             message: 'Password reset successful! You can now log in with your new password.',
//             type: 'success'
//           } 
//         });
//       }, 1500);
      
//     } catch (err) {
//       console.error('Error resetting password:', err);
      
//       // Handle specific errors
//       if (err.response?.status === 401) {
//         setError('Authentication failed. Please try resetting your password again.');
//       } else if (err.response?.status === 404) {
//         setError('User account not found. Please contact support.');
//       } else if (err.response?.data?.detail) {
//         setError(err.response.data.detail);
//       } else if (err.code === 'auth/weak-password') {
//         setError('Password is too weak. Please use a stronger password.');
//       } else if (err.code === 'auth/invalid-action-code') {
//         setError('This reset link has already been used. Please request a new one.');
//       } else {
//         setError('Failed to reset password. Please try again or request a new reset link.');
//       }
//     } finally {
//       setLoading(false);
//     }
//   };

//   // Loading state while verifying code
//   if (verifying) {
//     return (
//       <AuthLayout>
//         <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
//           <div className="text-center">
//             <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
//             <p className="text-slate-600 dark:text-slate-400">Verifying reset code...</p>
//           </div>
//         </div>
//       </AuthLayout>
//     );
//   }

//   // Error state - code verification failed
//   if (!codeVerified) {
//     return (
//       <AuthLayout>
//         <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
//           <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-9 text-center">
//             Reset Link Invalid
//           </h1>
//           <div className="rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 mb-6">
//             <p className="text-sm text-red-800 dark:text-red-200 text-center">{error}</p>
//           </div>
//           <div className="space-y-4">
//             <button
//               onClick={() => navigate('/forgot-password')}
//               className="w-full py-2 px-4 rounded-md bg-slate-900 dark:bg-slate-800 text-white font-semibold hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
//             >
//               Request New Reset Link
//             </button>
//             <button
//               onClick={() => navigate('/login')}
//               className="w-full py-2 px-4 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium border border-slate-300 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
//             >
//               Back to Login
//             </button>
//           </div>
//         </div>
//       </AuthLayout>
//     );
//   }

//   // Main reset password form
//   return (
//     <AuthLayout>
//       <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6 w-[500px] sm:w-[440px]">
//         <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-9 text-center">
//           Reset Password
//         </h1>
//         <p className="text-sm text-slate-600 dark:text-slate-400 mb-6 text-center">
//           Enter your new password for <span className="font-medium text-slate-900 dark:text-slate-100">{email}</span>
//         </p>

//         <form onSubmit={handleResetPassword} className="space-y-5">
//           <label className="block" htmlFor="new-password">
//             <span className="block text-sm text-slate-700 dark:text-slate-300">New Password</span>
//             <input
//               id="new-password"
//               type="password"
//               required
//               minLength={8}
//               className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
//               value={newPassword}
//               onChange={(e) => setNewPassword(e.target.value)}
//               disabled={loading}
//               placeholder="Enter new password (min 8 characters)"
//             />
//           </label>

//           <label className="block" htmlFor="confirm-password">
//             <span className="block text-sm text-slate-700 dark:text-slate-300">Confirm Password</span>
//             <input
//               id="confirm-password"
//               type="password"
//               required
//               minLength={8}
//               className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
//               value={confirmPassword}
//               onChange={(e) => setConfirmPassword(e.target.value)}
//               disabled={loading}
//               placeholder="Confirm your new password"
//             />
//           </label>

//           {error && (
//             <div className="rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3">
//               <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
//             </div>
//           )}

//           {loading && !error && (
//             <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4">
//               <p className="text-sm text-blue-800 dark:text-blue-200">
//                 Resetting your password...
//               </p>
//             </div>
//           )}

//           <button
//             type="submit"
//             className="mt-2 w-full py-2 px-4 rounded-md bg-slate-900 dark:bg-slate-800 text-white font-semibold hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
//             disabled={loading}
//           >
//             {loading ? 'Resetting Password...' : 'Reset Password'}
//           </button>
//         </form>

//         <div className="mt-5 text-center">
//           <button
//             onClick={() => navigate('/login')}
//             className="text-indigo-600 dark:text-indigo-400 hover:underline text-sm"
//             disabled={loading}
//           >
//             Back to Login
//           </button>
//         </div>

//         <div className="mt-4 text-center text-xs text-slate-500 dark:text-slate-400">
//           <p>Make sure your password is at least 8 characters long.</p>
//         </div>
//       </div>
//     </AuthLayout>
//   );
// }
