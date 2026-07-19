// Tipos compartidos, alineados con los esquemas del backend.

export type Role =
  | "ADMIN"
  | "OPERATOR_MATRIZ"
  | "OPERATOR_UN"
  | "VIEWER_MATRIZ"
  | "VIEWER_UN"
  | "FIELD";

export type WorkType = "REVISION_RED" | "ORDEN_PUNTUAL" | "MANTENIMIENTO";

export type WorkStatus =
  | "CREATED"
  | "ASSIGNED"
  | "DOWNLOADED"
  | "IN_PROGRESS"
  | "SYNCING"
  | "SYNCED"
  | "WITH_ISSUES"
  | "COMPLETED"
  | "SYNC_PENDING";

export interface CurrentUser {
  id: string;
  username: string;
  full_name: string;
  role: Role;
  un_id: string | null;
  is_global_scope: boolean;
}

export interface BusinessUnit {
  id: string;
  code: string;
  name: string;
  is_headquarters: boolean;
  active: boolean;
}

export interface Device {
  id: string;
  device_uid: string;
  alias: string;
  un_id: string;
  assigned_user_id: string | null;
  active: boolean;
  quality_params_version: number | null;
}

export interface UserRow {
  id: string;
  username: string;
  full_name: string;
  email: string | null;
  role: Role;
  auth_type: string;
  un_id: string | null;
  active: boolean;
}

export interface Work {
  id: string;
  code: string;
  title: string;
  description: string | null;
  work_type: WorkType;
  status: WorkStatus;
  un_id: string;
  schema_version: number;
  sector_geojson: string | null;
  device_id: string | null;
  validation_result: string;
}

export interface DashboardSummary {
  total: number;
  active: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
}

export interface AuditRow {
  id: string;
  username: string | null;
  role: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  new_values: string | null;
  un_id: string | null;
  ip_address: string | null;
  created_at: string;
}

export interface QualityParam {
  id: string;
  version: number;
  description: string | null;
  is_active: boolean;
}

export interface QualityNovelty {
  id: string;
  work_id: string;
  element_guid: string | null;
  element_type: string | null;
  field: string | null;
  rule_type: string;
  message: string | null;
  expected: string | null;
  actual: string | null;
}

export interface TimelineEvent {
  at: string;
  action: string;
  detail: string | null;
  username: string | null;
}
