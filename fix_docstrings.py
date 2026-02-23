import os
import re

replacements = {
    "CommsService": '"""Gestiona la comunicacion en tiempo real (SSE) o WebSockets."""',
    "PlanNodePosition": '"""Define las coordenadas de un nodo en el plano 2D visual."""',
    "CreatePlanRequest": '"""Esquema para crear un plan de ejecucion (CustomPlan)."""',
    "UpdatePlanRequest": '"""Esquema para actualizar metadatos de un CustomPlan."""',
    "RoutingDecision": '"""Encapsula la seleccion de proveedor y modelo (heuristica o NPU)."""',
    "PlanService": '"""Orquesta la planificacion cognitiva y preparacion de sub-tareas."""',
    "ProviderRegistry": '"""Registro en memoria de todos los proveedores AI detectados."""',
    "RegistryService": '"""Centraliza el patron registry para delegar configuraciones."""',
    "SkillCreateRequest": '"""Esquema para registrar un nuevo Skill re-utilizable."""',
    "SkillUpdateRequest": '"""Esquema para modificar parametros de un Skill existente."""',
    "TrustThresholds": '"""Limites estaticos de fallos para control continuo (CircuitBreaker)."""',
    "CircuitBreakerConfig": '"""Tiempos de cooldown y retry para proveedores inestables."""',
    "DetectedIntent": '"""Estructura las variables clave detectadas de un mensaje natural."""',
    "SecurityDecision": '"""Resultado del analisis de riesgo antes de iniciar una ejecucion."""',
    "ExecutionPlanDraft": '"""Borrador estructurado post-intencion, previo al GraphEngine."""',
    "CognitiveDecision": '"""Estado final cognitivo (Intencion + Seguridad + Plan)."""'
}

services_dir = r"c:\Users\shilo\Documents\Github\gred_in_multiagent_orchestrator\tools\gimo_server\services"
count = 0
for root, _, files in os.walk(services_dir):
    for filename in files:
        if filename.endswith(".py"):
            filepath = os.path.join(root, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            modified = False
            for class_name, correct_doc in replacements.items():
                generic_doc = f'"""Provee logica de negocio para {class_name}."""'
                if generic_doc in content:
                    content = content.replace(generic_doc, correct_doc)
                    modified = True

            if modified:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1
                print(f"Fixed {filename}")

print(f"Done. Fixed {count} files.")
