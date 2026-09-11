import React, { useState, useRef, useEffect } from "react";
import { apiClient } from "@shared/api/client";
import { ApiError } from "@shared/api/types";
import type { ProblemDetails } from "@shared/api/types";
import { ApiErrorBanner } from "@shared/components/ApiErrorBanner";
import type { ChatMessage } from "../types";
import { ChatBackdrop } from "./ChatBackdrop";
import { RobotAvatar } from "./RobotAvatar";

export const ChatScreen: React.FC<{ sessionId?: string }> = ({
  sessionId = "session-default"
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<ProblemDetails | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    setMessages([
      {
        id: "msg-001",
        role: "agent",
        content: "Bonjour ! Je suis l'agent AgentScope. Comment puis-je vous aider ?",
        created_at: new Date().toISOString()
      }
    ]);
  }, [sessionId]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isSending) return;

    const userText = inputText.trim();
    const newMsg: ChatMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: userText,
      created_at: new Date().toISOString(),
    };

    // Mise à jour optimiste de la liste de messages
    const updatedMessages = [...messages, newMsg];
    setMessages(updatedMessages);
    setInputText("");
    setIsSending(true);
    setError(null);

    try {
      // Structure conforme à ChatRequest (POST /chat)
      const payload = {
        conversation_id: sessionId,
        messages: updatedMessages.map((m) => ({
          role: m.role,
          text: m.content,
        })),
        current_proposal: {
          definition: "default_mapping",
          explanations: [],
          ambiguities: [],
          unmapped_fields: [],
        },
      };

      const response = await apiClient.post<{
        text: string;
        current_proposal?: { ambiguities?: string[] };
      }>("/chat", payload);

      const agentMsg: ChatMessage = {
        id: `agent-${Date.now()}`,
        role: "agent",
        content: response.text,
        created_at: new Date().toISOString(),
        ambiguity_alerts: response.current_proposal?.ambiguities || [],
      };

      setMessages((prev) => [...prev, agentMsg]);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem);
      } else {
        setError({
          title: "Erreur de communication",
          status: 500,
          detail: "Impossible de joindre l'agent sur POST /chat.",
        });
      }
      // Retirer le message optimiste si l'appel a échoué
      setMessages((prev) => prev.filter((m) => m.id !== newMsg.id));
    } finally {
      setIsSending(false); // Libère l'état de chargement
    }
  };

  return (
    <div className="relative flex h-full min-h-0 w-full flex-col border border-border bg-surface">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0 overflow-hidden"
      >
        <ChatBackdrop className="absolute left-1/2 top-1/2 h-[125%] w-[125%] -translate-x-1/2 -translate-y-1/2 opacity-[0.16]" />
      </div>
      <div className="relative z-10 flex items-center justify-between gap-3 border-b border-border bg-surface-raised px-4 py-3">
        <div className="flex min-w-0 items-center gap-3">
          <RobotAvatar className="h-9 w-9" />
          <div className="min-w-0">
            <h2 className="cyber-heading text-sm text-neon-cyan neon-text-cyan">
              Assistant AgentScope
            </h2>
            <p className="truncate text-[11px] text-foreground-muted">Session : {sessionId}</p>
          </div>
        </div>
        <span className="shrink-0 border border-neon-green/60 px-2 py-0.5 text-[10px] uppercase tracking-widest text-neon-green">
          online
        </span>
      </div>

      <ApiErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="relative z-10 flex-1 space-y-5 overflow-y-auto p-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] border p-3 text-sm ${
                msg.role === "user"
                  ? "border-neon-cyan/70 bg-neon-cyan/10 text-foreground"
                  : "border-border bg-surface-muted text-foreground"
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {msg.ambiguity_alerts && msg.ambiguity_alerts.length > 0 && (
                <div className="mt-3 border border-warning/60 bg-warning/10 p-3 text-foreground">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-warning">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Précision requise
                  </div>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-xs">
                    {msg.ambiguity_alerts.map((alert, idx) => (
                      <li key={idx}>{alert}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        {isSending && (
          <div className="flex justify-start">
            <div className="flex space-x-1 border border-border bg-surface-muted p-4">
              <div className="h-2 w-2 animate-bounce rounded-full bg-neon-cyan"></div>
              <div className="h-2 w-2 animate-bounce rounded-full bg-neon-cyan" style={{ animationDelay: "0.2s" }}></div>
              <div className="h-2 w-2 animate-bounce rounded-full bg-neon-cyan" style={{ animationDelay: "0.4s" }}></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="relative z-10 border-t border-border bg-surface/80 p-3 backdrop-blur-sm">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isSending}
            placeholder="Posez votre question à l'agent..."
            className="flex-1 border border-border bg-surface-muted px-3 py-2 text-sm text-foreground placeholder:text-foreground-muted focus:border-neon-cyan focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isSending}
            className="border border-neon-cyan bg-neon-cyan/10 px-4 py-2 text-sm font-semibold uppercase tracking-wider text-neon-cyan transition hover:bg-neon-cyan/20 disabled:opacity-40"
          >
            Envoyer
          </button>
        </form>
      </div>
    </div>
  );
};
