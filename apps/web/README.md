# GIMO Web

Landing, autenticación y sistema de licencias/suscripciones de GIMO.

> **Parte del monorepo GIMO** — ubicado en `apps/web/`

## Stack

- **Next.js 16** (App Router + TypeScript + Tailwind)
- **Firebase Auth** (Google Sign-In)
- **Stripe** (suscripciones + webhooks)
- **Vercel** (deployment)

## Setup

```bash
# 1. Instalar dependencias
npm install

# 2. Configurar variables de entorno
cp .env.example .env.local
# Rellena los valores en .env.local

# 3. Arrancar en local
npm run dev
# → http://localhost:3000
```

## Variables de entorno

Copia `.env.example` a `.env.local` y completa:

| Variable | Descripción |
|---|---|
| `NEXT_PUBLIC_FIREBASE_*` | Credenciales Firebase |
| `FIREBASE_ADMIN_SERVICE_ACCOUNT` | Service account JSON (una línea) |
| `STRIPE_SECRET_KEY` | Clave secreta Stripe |
| `STRIPE_WEBHOOK_SECRET` | Secret del webhook |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Clave pública Stripe |
| `STRIPE_STANDARD_PRICE_ID` | ID del precio estándar |
| `LICENSE_SIGNING_PRIVATE_KEY` | Ed25519 PKCS8 PEM |
| `ADMIN_EMAILS` | Emails admin separados por coma |
| `GIMO_INTERNAL_KEY` | Secreto compartido con el orquestador |

## API Routes

| Endpoint | Descripción |
|---|---|
| `/api/license/validate` | Valida licencia y firma token |
| `/api/license/deactivate` | Desactiva una activación |
| `/api/license/regenerate` | Regenera clave de licencia |
| `/api/checkout` | Crea sesión de checkout Stripe |
| `/api/webhooks/stripe` | Webhooks de Stripe |
| `/api/admin/*` | Endpoints de administración |
| `/api/orchestrator/verify` | Verificación orquestador→web |

## Scripts

- `npm run dev` — desarrollo
- `npm run build` — build producción
- `npm run start` — arranque producción
- `npm run lint` — lint
