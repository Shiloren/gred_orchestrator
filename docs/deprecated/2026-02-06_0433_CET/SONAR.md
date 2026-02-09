# Sonar (SonarCloud) Continuous Analysis

Este repositorio está configurado para ejecutar análisis continuo de código con SonarCloud en cada `push` y `pull_request` mediante GitHub Actions.

> **Nota:** Si el repositorio es privado y no se usa SonarCloud, puedes sustituir el workflow para SonarQube Server. En ese caso necesitarás `SONAR_HOST_URL` además de `SONAR_TOKEN`.

## 1) Crear proyecto en SonarCloud
1. Entra a https://sonarcloud.io y crea un proyecto nuevo.
2. Selecciona la organización (Organization) y conecta el repositorio de GitHub.
3. Copia el `Project Key` y el `Organization Key`.

## 2) Actualizar `sonar-project.properties`
Edita el archivo en la raíz del repo y reemplaza los placeholders:
- `sonar.projectKey=CHANGE_ME_PROJECT_KEY`
- `sonar.organization=CHANGE_ME_ORG`

## 3) GitHub Secrets requeridos
En el repositorio de GitHub, ve a **Settings → Secrets and variables → Actions** y crea:
- `SONAR_TOKEN`: Token de acceso de SonarCloud con permisos para analizar el proyecto.
- *(Solo SonarQube self-hosted)* `SONAR_HOST_URL`: URL del servidor, por ejemplo `https://sonarqube.mi-dominio.com`.

## 4) Verificar el workflow
1. Abre una Pull Request o haz un `push` a una rama.
2. Ve a **Actions → Sonar** y confirma que el job termina en verde.
3. En SonarCloud, abre el proyecto y valida que el análisis aparece en **Activity**.

## Troubleshooting
- **Project Key incorrecto**: confirma que `sonar.projectKey` coincide exactamente con el Project Key de SonarCloud.
- **Falta de token**: asegura que `SONAR_TOKEN` existe y tiene permisos para el proyecto.
- **fetch-depth insuficiente**: el checkout debe usar `fetch-depth: 0` para que el análisis de PR funcione correctamente.
- **Exclusions mal puestas**: revisa `sonar.exclusions` si faltan archivos esperados o se analizan artefactos generados.
- **Cobertura no encontrada**: confirma que `pytest --cov` genere `coverage.xml` en la raíz antes del scan.

## Checklist de remediación Quality Gate
### 1) Fixes de código (Reliability/Maintainability)
1. **Re-lanzar `asyncio.CancelledError` en `lifespan`**
   - Archivo: `tools/repo_orchestrator/main.py`
   - Acción: tras cancelar el task de limpieza, se re-lanza el error para respetar la semántica de cancelación.
2. **Reducir complejidad cognitiva de `verify_llm_config`**
   - Archivo: `scripts/verify_llm_config.py`
   - Acción: se dividió la lógica en helpers (`build_payload`, `log_speed`, `handle_success`, etc.).
3. **Excepciones específicas en `probe_ports`**
   - Archivo: `scripts/probe_ports.py`
   - Acción: `except (socket.timeout, OSError)` para evitar captura genérica.
4. **Constante para mensaje duplicado**
   - Archivo: `tools/repo_orchestrator/security/auth.py`
   - Acción: `INVALID_TOKEN_ERROR = "Invalid token"` reutilizada en validaciones.

### 2) Cobertura de tests (target ≥ 80%)
1. Ejecuta tests unitarios:
   ```bash
   pytest -q
   ```
2. Genera cobertura:
   ```bash
   pytest --cov=tools --cov=scripts --cov-report=term-missing --cov-report=xml
   ```
3. Revisa líneas sin cubrir en el reporte y ajusta tests.
4. Tests añadidos para este esfuerzo:
   - `tests/unit/test_main.py`: validación del re-lanzado de `CancelledError`.
   - `tests/unit/test_probe_ports.py`: casos de puerto abierto y timeout.
   - `tests/unit/test_verify_llm_config.py`: helpers de configuración y logging.

### 3) Revisión de Security Hotspot (manual)
1. Entra al dashboard de SonarCloud/SonarQube y abre la pestaña **Security Hotspots**.
2. Filtra por “New Code” y abre el hotspot pendiente.
3. Revisa el contexto y marca como:
   - **Reviewed** si es aceptable con justificación.
   - **To Fix** si requiere cambios de código.
4. Añade comentario de justificación (si aplica) y guarda.
