import React, { useState, useRef, useEffect } from "react";
import { apiClient } from "@shared/api/client";
import { ApiError } from "@shared/api/types";
import type { ProblemDetails } from "@shared/api/types";
import { ApiErrorBanner } from "@shared/components/ApiErrorBanner";
import type { ChatMessage } from "../types";

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
    <div className="mx-auto flex h-[80vh] max-w-4xl flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center justify-between border-b border-slate-200 p-4 dark:border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Assistant AgentScope</h2>
          <p className="text-xs text-slate-500">Session : {sessionId}</p>
        </div>
      </div>

      <ApiErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] rounded-2xl p-4 text-sm ${
                msg.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-200"
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {msg.ambiguity_alerts && msg.ambiguity_alerts.length > 0 && (
                <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Précision requise
                  </div>
                  <ul className="mt-2 list-inside list-disc text-xs space-y-1">
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
            <div className="flex space-x-1 rounded-2xl bg-slate-100 p-4 dark:bg-slate-900">
              <div className="h-2 w-2 animate-bounce rounded-full bg-slate-400"></div>
              <div className="h-2 w-2 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: "0.2s" }}></div>
              <div className="h-2 w-2 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: "0.4s" }}></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-slate-200 p-4 dark:border-slate-800">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isSending}
            placeholder="Posez votre question à l'agent..."
            className="flex-1 rounded-lg border border-slate-300 bg-transparent px-4 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 dark:border-slate-700 dark:text-slate-100"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isSending}
            className="flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-700 disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-600"
          >
            Envoyer
          </button>
        </form>
      </div>
    </div>
  );
};
