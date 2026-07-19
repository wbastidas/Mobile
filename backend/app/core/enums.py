"""Enumeraciones del dominio (roles, tipos y estados)."""
import enum


class Role(str, enum.Enum):
    """Roles de la plataforma web (sección 2.1 del documento)."""
    ADMIN = "ADMIN"                      # Administrador del Sistema (global)
    OPERATOR_MATRIZ = "OPERATOR_MATRIZ"  # Operador/Editor Matriz (global)
    OPERATOR_UN = "OPERATOR_UN"          # Operador/Editor UN (su UN)
    VIEWER_MATRIZ = "VIEWER_MATRIZ"      # Visualizador Matriz (global, solo lectura)
    VIEWER_UN = "VIEWER_UN"              # Visualizador UN (su UN, solo lectura)
    FIELD = "FIELD"                      # Funcionario de campo (app móvil)


# Conjuntos de roles por capacidad
MATRIZ_ROLES = {Role.ADMIN, Role.OPERATOR_MATRIZ, Role.VIEWER_MATRIZ}
OPERATOR_ROLES = {Role.ADMIN, Role.OPERATOR_MATRIZ, Role.OPERATOR_UN}
VIEWER_ROLES = {Role.VIEWER_MATRIZ, Role.VIEWER_UN}
GLOBAL_SCOPE_ROLES = {Role.ADMIN, Role.OPERATOR_MATRIZ, Role.VIEWER_MATRIZ}


class AuthType(str, enum.Enum):
    LOCAL = "LOCAL"          # Login local (usuario/clave gestionados en el sistema)
    CORPORATE = "CORPORATE"  # Login corporativo (AD/LDAP/SSO) — RF-WEB-01.1


class WorkType(str, enum.Enum):
    """Tipos de trabajo (RF-WEB-03)."""
    REVISION_RED = "REVISION_RED"        # Revisión en campo por sector geográfico
    ORDEN_PUNTUAL = "ORDEN_PUNTUAL"      # Orden de trabajo puntual (por GUID)
    MANTENIMIENTO = "MANTENIMIENTO"      # Actividad de mantenimiento / proyecto


class WorkStatus(str, enum.Enum):
    """Protocolo de estados por trabajo (RF-SYNC.6)."""
    CREATED = "CREATED"                  # Creado en la web, sin asignar
    ASSIGNED = "ASSIGNED"                # Asignado a un dispositivo
    DOWNLOADED = "DOWNLOADED"            # Descargado por el dispositivo
    IN_PROGRESS = "IN_PROGRESS"          # En ejecución en campo
    SYNCING = "SYNCING"                  # En sincronización
    SYNCED = "SYNCED"                    # Sincronizado/Verificado
    WITH_ISSUES = "WITH_ISSUES"          # Sincronizado con novedades de calidad
    COMPLETED = "COMPLETED"              # Terminado y consolidado
    SYNC_PENDING = "SYNC_PENDING"        # Sincronización parcial/fallida, reintentar


class RemoteDeleteStatus(str, enum.Enum):
    QUEUED = "QUEUED"          # En cola, esperando conexión del dispositivo
    CONFIRMED = "CONFIRMED"    # Ejecutado y confirmado por el dispositivo
    CANCELLED = "CANCELLED"


class ValidationResult(str, enum.Enum):
    APPROVED = "APPROVED"        # Aprobado sin novedades
    WITH_ISSUES = "WITH_ISSUES"  # Con novedades de calidad
    NOT_RUN = "NOT_RUN"


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    ASSIGN = "ASSIGN"
    REMOTE_DELETE_ORDER = "REMOTE_DELETE_ORDER"
    REMOTE_DELETE_CONFIRM = "REMOTE_DELETE_CONFIRM"
    SYNC_RECEIVE = "SYNC_RECEIVE"
    SYNC_VERIFY = "SYNC_VERIFY"
    CONSOLIDATE = "CONSOLIDATE"
    QUALITY_PARAMS_UPLOAD = "QUALITY_PARAMS_UPLOAD"
