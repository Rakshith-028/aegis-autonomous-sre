export const API_BASE =
  process.env.NEXT_PUBLIC_AEGIS_API_URL ??
  "http://localhost:8080";

export const WS_URL =
  process.env.NEXT_PUBLIC_AEGIS_WS_URL ??
  "ws://localhost:8080/ws/live";


export type MetricValue = {
  success: boolean;
  value: number | null;
  error: string | null;
};


export type Evidence = {
  service: string;
  timestamp: string;
  health: {
    reachable: boolean;
    status_code: number | null;
    latency_seconds?: number;
    error?: string;
  };
  container: {
    available: boolean;
    state?: {
      Status?: string;
      Running?: boolean;
      Restarting?: boolean;
      OOMKilled?: boolean;
      ExitCode?: number;
    };
    error?: string;
  };
  metrics: {
    request_rate: MetricValue;
    error_rate: MetricValue;
    latency: MetricValue;
  };
  logs: string[];
};


export type RCA = {
  root_cause: string;
  confidence: number;
  severity: string;
  reasoning: string[];
  recommended_action: string;
};


export type Incident = {
  id: string;
  incident_key: string;
  service: string;
  status: string;
  severity: string;
  source: string;
  failure_type: string;
  reason: string;
  started_at: string;
  updated_at: string;
  resolved_at: string | null;
  remediation: string | null;
  metadata: Record<string, unknown>;
};


export type SystemStatus = {
  system: string;
  service: string;
  evidence: Evidence;
  rca: RCA;
  active_incidents: Incident[];
};


export type Postmortem = {
  incident_id: string;
  service: string;
  created_at: string;
  incident: Incident;
  root_cause_analysis: RCA;
  policy_decision: {
    allowed: boolean;
    risk_level: string;
    requires_approval: boolean;
    reason: string;
  };
  remediation: {
    success: boolean;
    action: string;
    detail: string;
  };
  verification: Array<{
    attempt: number;
    status_code: number | null;
    latency_seconds: number | null;
    healthy: boolean;
  }>;
  summary: string;
};


async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();

    throw new Error(
      text || `Request failed with HTTP ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}


export function getSystemStatus() {
  return request<SystemStatus>("/api/status");
}


export async function getIncidents() {
  const data = await request<{
    count: number;
    incidents: Incident[];
  }>("/api/incidents");

  return data.incidents;
}


export async function getPostmortems() {
  const data = await request<{
    count: number;
    postmortems: Postmortem[];
  }>("/api/postmortems");

  return data.postmortems;
}


export function runAutonomousCycle() {
  return request<Record<string, unknown>>(
    "/api/cycle/run",
    {
      method: "POST",
    },
  );
}


export function injectChaos(mode: string) {
  return request<Record<string, unknown>>(
    `/api/chaos/${mode}`,
    {
      method: "POST",
    },
  );
}
