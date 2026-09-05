// API client for Integration Control Tower

const API_BASE = "/api";

export interface Order {
  id: string;
  order_id: string;
  supplier_id: string;
  product_id: string;
  quantity: number;
  unit: string;
  is_urgent: boolean;
  delivery_date: string;
  source_system: string;
  status: string;
  correlation_id: string;
  created_at: string;
}

export interface Forecast {
  id: string;
  forecast_id: string;
  supplier_id: string;
  product_id: string;
  forecast_quantity: number;
  forecast_period: string;
  source_system: string;
  confidence_level: number;
  status: string;
  correlation_id: string;
  created_at: string;
}

export interface CanonicalEvent {
  id: string;
  event_id: string;
  event_type: string;
  event_version: string;
  source_system: string;
  order_id?: string;
  forecast_id?: string;
  supplier_id: string;
  product_id: string;
  quantity: number;
  unit: string;
  priority: string;
  delivery_date?: string;
  forecast_period?: string;
  business_rule_version: string;
  correlation_id: string;
  idempotency_key: string;
  status: string;
  raw_payload?: Record<string, any>;
  created_at: string;
}

export interface AdapterDelivery {
  id: string;
  delivery_id: string;
  event_id: string;
  supplier_id: string;
  adapter_name: string;
  transformed_payload: Record<string, any>;
  delivery_status: string;
  attempt_count: number;
  last_attempt: string;
  error_message?: string;
  latency_ms: number;
  retry_status?: string;
  created_at: string;
}

export interface SystemStatus {
  id: string;
  system_name: string;
  display_name: string;
  system_type: string;
  status: string;
  latency_ms: number;
  error_rate: number;
  last_heartbeat: string;
  details?: string;
}

export interface FailureCase {
  id: string;
  failure_id: string;
  failure_type: string;
  affected_system: string;
  severity: string;
  cause: string;
  impact: string;
  detection_method: string;
  recovery_action: string;
  status: string;
  retry_count: number;
  audit_reference?: string;
  created_at: string;
  resolved_at?: string;
}

export interface ChangeRequest {
  id: string;
  change_id: string;
  title: string;
  description: string;
  rule_key: string;
  current_rule_version: string;
  proposed_rule_version: string;
  previous_threshold: number;
  new_threshold: number;
  status: string;
  submitted_by: string;
  approved_by?: string;
  deployed_at?: string;
  rolled_back_at?: string;
  baseline_systems_changed: number;
  decoupled_systems_changed: number;
  notes?: string;
  created_at: string;
}

export interface AuditEntry {
  id: string;
  audit_id: string;
  timestamp: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string;
  old_value?: string;
  new_value?: string;
  status: string;
  correlation_id?: string;
}

export interface RollbackAction {
  id: string;
  rollback_id: string;
  change_id: string;
  from_version: string;
  to_version: string;
  initiated_by: string;
  reason: string;
  status: string;
  timestamp: string;
}

export interface ExperimentRun {
  id: string;
  run_id: string;
  timestamp: string;
  rule_change_name: string;
  baseline_systems_changed: number;
  decoupled_systems_changed: number;
  baseline_effort_hours: number;
  decoupled_effort_hours: number;
  tests_required_baseline: number;
  tests_required_decoupled: number;
  risk_score_baseline: string;
  risk_score_decoupled: string;
  improvement_pct: number;
  notes?: string;
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP Error ${res.status}`);
    }
    return await res.json();
  } catch (error: any) {
    console.error(`API Error on ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // Health
  getHealth: () => request<any>("/health"),

  // Orders
  getOrders: (supplier_id?: string) => request<Order[]>(`/orders${supplier_id ? `?supplier_id=${supplier_id}` : ""}`),
  createOrder: (data: any) => request<Order>("/orders", { method: "POST", body: JSON.stringify(data) }),

  // Forecasts
  getForecasts: () => request<Forecast[]>("/forecasts"),
  createForecast: (data: any) => request<Forecast>("/forecasts", { method: "POST", body: JSON.stringify(data) }),

  // Events
  getEvents: (supplier_id?: string, status?: string) => {
    const params = new URLSearchParams();
    if (supplier_id) params.append("supplier_id", supplier_id);
    if (status) params.append("status", status);
    return request<CanonicalEvent[]>(`/events?${params.toString()}`);
  },
  processEvents: () => request<any>("/events/process", { method: "POST" }),

  // Adapters
  getAdapterDeliveries: () => request<AdapterDelivery[]>("/adapters"),
  getAdapterTransformations: () => request<any>("/adapters/compare-transformations"),
  retryDelivery: (id: string) => request<AdapterDelivery>(`/adapters/retry/${id}`, { method: "POST" }),

  // Systems / Integration Monitor
  getSystems: () => request<SystemStatus[]>("/systems"),
  simulateSystemStatus: (data: { system_name: string; target_status: string }) =>
    request<SystemStatus>("/systems/simulate", { method: "POST", body: JSON.stringify(data) }),
  recoverAllSystems: () => request<SystemStatus[]>("/systems/recover-all", { method: "POST" }),

  // Failures
  getFailures: () => request<FailureCase[]>("/failures"),
  simulateFailure: (type: string, system?: string) =>
    request<FailureCase>("/failures/simulate", { method: "POST", body: JSON.stringify({ failure_type: type, target_system: system }) }),
  retryFailure: (id: string) => request<FailureCase>(`/failures/${id}/retry`, { method: "POST" }),
  resolveFailure: (id: string) => request<FailureCase>(`/failures/${id}/resolve`, { method: "POST" }),

  // Changes
  getChanges: () => request<ChangeRequest[]>("/changes"),
  createChange: (data: any) => request<ChangeRequest>("/changes", { method: "POST", body: JSON.stringify(data) }),
  submitChange: (id: string) => request<ChangeRequest>(`/changes/${id}/submit`, { method: "POST" }),
  approveChange: (id: string) => request<ChangeRequest>(`/changes/${id}/approve`, { method: "POST" }),
  rejectChange: (id: string) => request<ChangeRequest>(`/changes/${id}/reject`, { method: "POST" }),
  deployChange: (id: string) => request<ChangeRequest>(`/changes/${id}/deploy`, { method: "POST" }),
  rollbackChange: (id: string) => request<any>(`/changes/${id}/rollback`, { method: "POST" }),

  // Rollback Actions
  getRollbacks: () => request<RollbackAction[]>("/rollback"),

  // Experiments
  getExperiments: () => request<ExperimentRun[]>("/experiments"),
  getExperimentMetrics: () => request<any>("/experiments/metrics"),
  runExperiment: (threshold = 200) => request<ExperimentRun>(`/experiments/run?threshold=${threshold}`, { method: "POST" }),

  // Audit
  getAuditTrail: (action?: string, search?: string) => {
    const params = new URLSearchParams();
    if (action) params.append("action", action);
    if (search) params.append("search", search);
    return request<AuditEntry[]>(`/audit?${params.toString()}`);
  },

  // Stakeholder Validation
  getValidations: () => request<any[]>("/validation"),
  getValidationSummary: () => request<any>("/validation/summary"),
  submitValidation: (data: any) => request<any>("/validation", { method: "POST", body: JSON.stringify(data) }),
};
