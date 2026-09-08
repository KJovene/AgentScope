export interface ImportReport {
  id: string;
  source_id?: string;
  mapping_id: string;
  status: "completed" | "failed" | "partial";
  imported_count: number;
  duplicate_count: number;
  rejected_count: number;
  missing_info_count: number;
  imported_at: string;
}
