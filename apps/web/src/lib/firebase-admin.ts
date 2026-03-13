/**
 * Firebase Admin SDK — Server-side only
 * Usado en API routes para leer/escribir Firestore y verificar tokens.
 */
import { initializeApp, getApps, cert, App, ServiceAccount } from "firebase-admin/app";
import { getFirestore, Firestore } from "firebase-admin/firestore";
import { getAuth, Auth } from "firebase-admin/auth";

type ServiceAccountInput = {
  project_id?: string;
  private_key?: string;
  client_email?: string;
  projectId?: string;
  privateKey?: string;
  clientEmail?: string;
};

function initAdmin(): App {
  if (getApps().length > 0) return getApps()[0];

  const serviceAccountEnv = process.env.FIREBASE_SERVICE_ACCOUNT_KEY || process.env.FIREBASE_ADMIN_SERVICE_ACCOUNT;
  if (!serviceAccountEnv) {
    throw new Error("FIREBASE_SERVICE_ACCOUNT_KEY env var not set");
  }

  let parsed: ServiceAccountInput;
  try {
    // Soporta JSON directo o base64-encoded
    const decoded = Buffer.from(serviceAccountEnv, "base64").toString("utf-8");
    parsed = JSON.parse(decoded) as ServiceAccountInput;
  } catch {
    parsed = JSON.parse(serviceAccountEnv) as ServiceAccountInput;
  }

  const privateKeyRaw = parsed.privateKey ?? parsed.private_key;
  const projectIdRaw = parsed.projectId ?? parsed.project_id;
  const clientEmailRaw = parsed.clientEmail ?? parsed.client_email;

  const serviceAccount: ServiceAccount = {
    privateKey: privateKeyRaw,
    projectId: projectIdRaw,
    clientEmail: clientEmailRaw,
  };

  // Normaliza PEM por si viene serializado en una sola línea o con espacios dañados.
  if (typeof serviceAccount.privateKey === "string") {
    serviceAccount.privateKey = serviceAccount.privateKey
      .replace(/\\n/g, "\n")
      .replace("BEGINPRIVATEKEY", "BEGIN PRIVATE KEY")
      .replace("ENDPRIVATEKEY", "END PRIVATE KEY");
  }

  const expectedProjectId =
    (process.env.FIREBASE_PROJECT_ID || process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "").trim();
  if (
    expectedProjectId &&
    typeof serviceAccount.projectId === "string" &&
    serviceAccount.projectId.trim() !== expectedProjectId
  ) {
    throw new Error(
      `Firebase Admin project mismatch: service_account=${serviceAccount.projectId}, expected=${expectedProjectId}`
    );
  }

  return initializeApp({ credential: cert(serviceAccount) });
}

// Lazy initialization — no lanza error en build time si la variable no está configurada
let _adminApp: App | null = null;

function getAdminApp(): App {
  if (!_adminApp) _adminApp = initAdmin();
  return _adminApp;
}

export function getAdminDb(): Firestore {
  return getFirestore(getAdminApp());
}

export function getAdminAuth(): Auth {
  return getAuth(getAdminApp());
}

// Aliases para compatibilidad con código existente que importa adminDb/adminAuth directamente
export const adminDb: Firestore = new Proxy({} as Firestore, {
  get(_target, prop) {
    return (getAdminDb() as unknown as Record<string | symbol, unknown>)[prop];
  },
});
export const adminAuth: Auth = new Proxy({} as Auth, {
  get(_target, prop) {
    return (getAdminAuth() as unknown as Record<string | symbol, unknown>)[prop];
  },
});

/** Admin email list — estos usuarios tienen rol "admin" automáticamente */
export const ADMIN_EMAILS = (
  process.env.ADMIN_EMAILS ?? "admin@gimo.ai"
)
  .split(",")
  .map((e) => e.trim().toLowerCase());
