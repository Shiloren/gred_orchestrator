import { initializeApp, getApps, getApp, type FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, type Auth } from 'firebase/auth';

const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const requiredFirebaseEnvKeys: Array<keyof typeof firebaseConfig> = [
    'apiKey',
    'authDomain',
    'projectId',
    'appId',
];

export function getMissingFirebaseEnvKeys(): string[] {
    return requiredFirebaseEnvKeys
        .filter((key) => !firebaseConfig[key])
        .map((key) => {
            if (key === 'apiKey') return 'VITE_FIREBASE_API_KEY';
            if (key === 'authDomain') return 'VITE_FIREBASE_AUTH_DOMAIN';
            if (key === 'projectId') return 'VITE_FIREBASE_PROJECT_ID';
            if (key === 'appId') return 'VITE_FIREBASE_APP_ID';
            return String(key);
        });
}

export function isFirebaseConfigured(): boolean {
    return getMissingFirebaseEnvKeys().length === 0;
}

let _app: FirebaseApp | null = null;
let _auth: Auth | null = null;
let _googleProvider: GoogleAuthProvider | null = null;

if (isFirebaseConfigured()) {
    _app = getApps().length ? getApp() : initializeApp(firebaseConfig);
    _auth = getAuth(_app);
    _googleProvider = new GoogleAuthProvider();
}

export const auth = _auth;
export const googleProvider = _googleProvider;
