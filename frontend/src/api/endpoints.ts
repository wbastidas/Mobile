// Funciones tipadas por recurso, sobre el cliente axios.
import { api } from "./client";
import type {
  AuditRow,
  BusinessUnit,
  CurrentUser,
  DashboardSummary,
  Device,
  QualityNovelty,
  QualityParam,
  TimelineEvent,
  UserRow,
  Work,
  WorkType,
} from "@/types";

export const authApi = {
  login: (username: string, password: string) =>
    api.post("/auth/login", { username, password }).then((r) => r.data),
  me: () => api.get<CurrentUser>("/auth/me").then((r) => r.data),
};

export const buApi = {
  list: () => api.get<BusinessUnit[]>("/business-units").then((r) => r.data),
  create: (payload: { code: string; name: string; is_headquarters?: boolean }) =>
    api.post<BusinessUnit>("/business-units", payload).then((r) => r.data),
};

export const usersApi = {
  list: () => api.get<UserRow[]>("/users").then((r) => r.data),
  create: (payload: Record<string, unknown>) =>
    api.post<UserRow>("/users", payload).then((r) => r.data),
};

export const devicesApi = {
  list: () => api.get<Device[]>("/devices").then((r) => r.data),
  create: (payload: { device_uid: string; alias: string; un_id: string }) =>
    api.post<Device>("/devices", payload).then((r) => r.data),
};

export const worksApi = {
  list: (params?: Record<string, string>) =>
    api.get<Work[]>("/works", { params }).then((r) => r.data),
  create: (payload: {
    code: string;
    title: string;
    work_type: WorkType;
    un_id: string;
    description?: string;
    sector_geojson?: string;
  }) => api.post<Work>("/works", payload).then((r) => r.data),
  assign: (device_id: string, work_ids: string[]) =>
    api.post<Work[]>("/works/assign", { device_id, work_ids }).then((r) => r.data),
  remoteDelete: (device_id: string, work_ids: string[]) =>
    api.post("/works/remote-delete", { device_id, work_ids }).then((r) => r.data),
};

export const dashboardApi = {
  summary: () => api.get<DashboardSummary>("/dashboard/summary").then((r) => r.data),
  map: (history = false) =>
    api.get<Work[]>("/dashboard/map", { params: { history } }).then((r) => r.data),
  timeline: (workId: string) =>
    api.get<TimelineEvent[]>(`/dashboard/works/${workId}/timeline`).then((r) => r.data),
};

export const noveltiesApi = {
  byWork: (workId: string) =>
    api
      .get<QualityNovelty[]>("/quality/novelties", { params: { work_id: workId } })
      .then((r) => r.data),
};

export const auditApi = {
  list: (params?: Record<string, string>) =>
    api.get<AuditRow[]>("/audit", { params }).then((r) => r.data),
};

export interface ReportInfo {
  key: string;
  name: string;
}
export interface ReportData {
  key: string;
  name: string;
  rows: Record<string, string | number>[];
  count: number;
}

export const reportsApi = {
  catalog: () => api.get<ReportInfo[]>("/reports").then((r) => r.data),
  data: (key: string, params?: Record<string, string>) =>
    api.get<ReportData>(`/reports/${key}`, { params }).then((r) => r.data),
  exportUrl: (key: string, fmt: string) => `/api/v1/reports/${key}/export?fmt=${fmt}`,
  download: async (key: string, fmt: string) => {
    const res = await api.get(`/reports/${key}/export`, {
      params: { fmt },
      responseType: "blob",
    });
    return res.data as Blob;
  },
};

export const qualityApi = {
  list: () => api.get<QualityParam[]>("/quality/params").then((r) => r.data),
  upload: (payload: { description?: string; rules_json: unknown; activate?: boolean }) =>
    api.post<QualityParam>("/quality/params", payload).then((r) => r.data),
};
