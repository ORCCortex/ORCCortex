// Firebase configuration - PUBLIC SAFE VERSION
// This version uses placeholder values and should be safe for public repositories

const firebaseConfig = {
    // NOTE: This API key has been regenerated and restricted
    // The actual key is stored securely and not in this public repository
    apiKey: "",
    authDomain: "orccortex-543d1.firebaseapp.com",
    projectId: "orccortex-543d1",
    storageBucket: "orccortex-543d1.firebasestorage.app"
};

// For production, load the actual config from secure source
if (typeof window !== 'undefined') {
    window.FIREBASE_CONFIG = firebaseConfig;
}