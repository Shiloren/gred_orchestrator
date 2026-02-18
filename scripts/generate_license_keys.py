#!/usr/bin/env python3
"""
GIMO License Key Generator — Ed25519
=====================================
Genera el par de claves Ed25519 para el sistema de licenciamiento GIMO.

Uso:
    python scripts/generate_license_keys.py

Salida:
    - private_key.pem  → Cargar en Vercel como LICENSE_SIGNING_PRIVATE_KEY
    - public_key.pem   → Embebida en GIMO Server + env ORCH_LICENSE_PUBLIC_KEY
"""

import sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        PublicFormat,
    )
except ImportError:
    print("ERROR: cryptography no instalado. Ejecuta: pip install cryptography>=43.0.0")
    sys.exit(1)


def generate_keys(output_dir: Path = Path(".")) -> tuple[str, str]:
    """Genera par Ed25519. Retorna (private_pem, public_pem) como strings."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


def main():
    print("=" * 60)
    print("  GIMO License Key Generator — Ed25519")
    print("=" * 60)

    private_pem, public_pem = generate_keys()

    # Guardar archivos
    private_path = Path("private_key.pem")
    public_path = Path("public_key.pem")

    private_path.write_text(private_pem, encoding="utf-8")
    public_path.write_text(public_pem, encoding="utf-8")

    print(f"\n✅ Claves generadas correctamente:")
    print(f"   private_key.pem  → {private_path.resolve()}")
    print(f"   public_key.pem   → {public_path.resolve()}")

    # Mostrar instrucciones
    print("\n" + "=" * 60)
    print("  CONFIGURACIÓN REQUERIDA")
    print("=" * 60)

    print("\n📦 GIMO WEB (Vercel) — añadir estas env vars:")
    print(f"\n  LICENSE_SIGNING_PRIVATE_KEY=")
    # Mostrar la clave en formato inline (\\n)
    private_inline = private_pem.replace("\n", "\\n")
    print(f"  {private_inline}")

    print(f"\n  LICENSE_SIGNING_PUBLIC_KEY=")
    public_inline = public_pem.replace("\n", "\\n")
    print(f"  {public_inline}")

    print("\n🖥️  GIMO Server — añadir a .env o al sistema:")
    print(f"\n  ORCH_LICENSE_KEY=<tu-license-key-generada-en-el-dashboard>")
    print(f"  ORCH_LICENSE_URL=https://gimo-web.vercel.app/api/license/validate")
    print(f"  ORCH_LICENSE_PUBLIC_KEY=")
    print(f"  {public_inline}")

    print("\n" + "=" * 60)
    print("  ⚠️  SEGURIDAD")
    print("=" * 60)
    print("\n  • private_key.pem NUNCA debe subirse a git")
    print("  • Está añadido al .gitignore automáticamente")
    print("  • Solo la public_key.pem puede ser pública")
    print("  • public_key.pem también se embebe en el código del Server")
    print("    como fallback si ORCH_LICENSE_PUBLIC_KEY no está configurada")

    # Añadir al .gitignore si existe
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        entries_to_add = []
        if "private_key.pem" not in content:
            entries_to_add.append("private_key.pem")
        if entries_to_add:
            with gitignore.open("a", encoding="utf-8") as f:
                f.write("\n# License keys (NEVER commit private key)\n")
                for entry in entries_to_add:
                    f.write(f"{entry}\n")
            print(f"\n  ✅ Añadido 'private_key.pem' a .gitignore")

    # También mostrar el public key para embeber en el código
    print("\n" + "=" * 60)
    print("  PUBLIC KEY (para embeber en license_guard.py)")
    print("=" * 60)
    print("\n  Copia este valor y pégalo en EMBEDDED_PUBLIC_KEY en")
    print("  tools/gimo_server/security/license_guard.py:")
    print()
    print('  EMBEDDED_PUBLIC_KEY = """')
    print(public_pem.strip())
    print('  """')
    print()


if __name__ == "__main__":
    main()
