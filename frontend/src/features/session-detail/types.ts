
export type EventType = "model_call" | "tool_call" | "error";

export interface BaseEvent {
  id: string;
  timestamp: string; // ISO-8601
  type: EventType;
}

export interface ModelCallEvent extends BaseEvent {
  type: "model_call";
  model: string;
  promptSummary: string;
  responseSummary: string;
  tokens: { prompt: number; completion: number; total: number };
  cost: number;
}

export interface ToolCallEvent extends BaseEvent {
  type: "tool_call";
  toolName: string;
  arguments: Record<string, unknown>;
  result: string;
  provenanceLink?: string; // Lien vers le document ou la source
}

export interface ErrorEvent extends BaseEvent {
  type: "error";
  errorMessage: string;
  step?: string;
}

export type SessionEvent = ModelCallEvent | ToolCallEvent | ErrorEvent;

export interface SessionDetails {
  id: string;
  status: "running" | "completed" | "failed";
  createdAt: string;
  totalTokens: number;
  totalCost: number;
  events: SessionEvent[];
}
