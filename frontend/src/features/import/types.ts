export interface ImportReport {
  id: string;
  source_id?: string;
  mapping_id: string;
  status: "completed" | "failed" | "partial" | string;
  imported_count: number;
  duplicate_count: number;
  rejected_count: number;
  missing_info_count: number | Record<string, number>;
  imported_at: string;
}

export interface RejectRecord {
  record_index: number;
  reason_code: string;
  reason_detail: string;
  payload?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
