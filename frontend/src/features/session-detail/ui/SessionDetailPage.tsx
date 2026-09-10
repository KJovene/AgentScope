import React from "react";
import type { SessionDetails, ModelCallEvent, ToolCallEvent, ErrorEvent } from "../types";

interface SessionTimelineProps {
  session: SessionDetails;
}

export const SessionTimeline: React.FC<SessionTimelineProps> = ({ session }) => {
  // Tri chronologique de sécurité
  const sortedEvents = [...session.events].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const renderModelCall = (event: ModelCallEvent) => (
    <div className="rounded-lg border border-indigo-200 bg-indigo-50/50 p-4 dark:border-indigo-900/50 dark:bg-indigo-950/20">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-semibold text-indigo-700 dark:text-indigo-400">🤖 Appel LLM ({event.model})</span>
        <div className="flex gap-3 text-xs text-slate-500">
          <span>Tokens: {event.tokens.total}</span>
          <span>Coût: ${event.cost.toFixed(4)}</span>
        </div>
      </div>
      <div className="space-y-2 text-sm text-slate-700 dark:text-slate-300">
        <p><span className="font-medium">Prompt:</span> {event.promptSummary}</p>
        <p><span className="font-medium">Réponse:</span> {event.responseSummary}</p>
      </div>
    </div>
  );

  const renderToolCall = (event: ToolCallEvent) => (
    <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-semibold text-emerald-700 dark:text-emerald-400">🛠️ Exécution Outil: {event.toolName}</span>
        {event.provenanceLink && (
          <a
            href={event.provenanceLink}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-medium text-emerald-600 hover:underline dark:text-emerald-400"
          >
            Lien provenance ↗
          </a>
        )}
      </div>
      <div className="space-y-2 text-sm text-slate-700 dark:text-slate-300">
        <div className="rounded bg-white p-2 shadow-sm dark:bg-slate-900">
          <span className="block text-xs font-medium text-slate-500">Arguments:</span>
          <pre className="mt-1 text-[10px] overflow-x-auto">{JSON.stringify(event.arguments, null, 2)}</pre>
        </div>
        <p className="mt-2"><span className="font-medium">Résultat:</span> {event.result}</p>
      </div>
    </div>
  );

  const renderError = (event: ErrorEvent) => (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/20">
      <div className="mb-1 flex items-center gap-2 font-semibold text-red-700 dark:text-red-400">
        <span>❌ Erreur</span>
        {event.step && <span className="text-xs font-normal opacity-75">(Étape: {event.step})</span>}
      </div>
      <p className="text-sm text-red-600 dark:text-red-300">{event.errorMessage}</p>
    </div>
  );

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
      {/* En-tête / Synthèse */}
      <div className="mb-8 flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Timeline de la session</h2>
          <p className="text-sm text-slate-500">Session ID: {session.id}</p>
        </div>
        <div className="flex gap-4 text-sm">
          <div className="rounded-lg bg-slate-100 px-4 py-2 text-center dark:bg-slate-900">
            <span className="block text-[10px] uppercase text-slate-500">Tokens totaux</span>
            <span className="font-bold text-slate-800 dark:text-slate-200">{session.totalTokens}</span>
          </div>
          <div className="rounded-lg bg-slate-100 px-4 py-2 text-center dark:bg-slate-900">
            <span className="block text-[10px] uppercase text-slate-500">Coût estimé</span>
            <span className="font-bold text-slate-800 dark:text-slate-200">${session.totalCost.toFixed(4)}</span>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="relative border-l-2 border-slate-200 ml-4 space-y-8 dark:border-slate-800">
        {sortedEvents.map((event) => (
          <div key={event.id} className="relative pl-6">
            {/* Point sur la timeline */}
            <div className={`absolute -left-[9px] top-1 h-4 w-4 rounded-full border-2 border-white dark:border-slate-950 ${
              event.type === 'model_call' ? 'bg-indigo-500' :
              event.type === 'tool_call' ? 'bg-emerald-500' : 'bg-red-500'
            }`} />

            {/* Heure */}
            <div className="mb-2 text-xs font-medium text-slate-400">
              {formatTime(event.timestamp)}
            </div>

            {/* Contenu de l'événement */}
            {event.type === "model_call" && renderModelCall(event)}
            {event.type === "tool_call" && renderToolCall(event)}
            {event.type === "error" && renderError(event)}
          </div>
        ))}

        {sortedEvents.length === 0 && (
          <p className="pl-6 text-sm text-slate-500">Aucun événement enregistré pour cette session.</p>
        )}
      </div>
    </div>
  );
}
