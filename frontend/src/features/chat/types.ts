export interface ChatMessage {
  id: string;
  role: "user" | "agent" | "system";
  content: string;
  created_at: string;
  ambiguity_alerts?: string[]; // Liste des ambiguïtés détectées par l'agent
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

export interface SendMessagePayload {
  content: string;
}
