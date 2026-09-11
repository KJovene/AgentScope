import React, { useState } from "react";
import { ApiErrorBanner } from "../shared/components/ApiErrorBanner";
import type { ProblemDetails } from "../shared/api/types";

export type NavTab = "imports" | "mapping" | "dashboard" | "quality";

interface LayoutProps {
  children?: (props: {
    activeTab: NavTab;
    setError: (err: ProblemDetails | null) => void;
  }) => React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<NavTab>("dashboard");
  const [globalError, setGlobalError] = useState<ProblemDetails | null>(null);

  const navItems: { id: NavTab; label: string }[] = [
    { id: "imports", label: "Imports & Ingestion" },
    { id: "mapping", label: "Sources & Mapping" },
    { id: "dashboard", label: "Tableau de bord" },
    { id: "quality", label: "Qualité & Sessions" },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-900 dark:text-slate-100 flex flex-col">
      {/* Entête principal */}
      <header className="border-b border-slate-200 bg-white px-6 py-4 shadow-sm dark:border-slate-800 dark:bg-slate-950 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-xl font-bold tracking-tight text-indigo-600 dark:text-indigo-400">
            AgentScope
          </span>
          <span className="rounded bg-indigo-100 px-2 py-0,5 text-xs font-medium text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300">
            v0.1.0
          </span>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Navigation latérale */}
        <nav
          aria-label="Navigation principale"
          className="w-64 border-r border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950"
        >
          <ul className="space-y-1">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <li key={item.id}>
                  <button
                    onClick={() => {
                      setActiveTab(item.id);
                      setGlobalError(null);
                    }}
                    className={`w-full rounded-lg px-4 py-2,5 text-left text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                        : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-900"
                    }`}
                  >
                    {item.label}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Zone de contenu */}
        <main className="flex-1 p-6">
          <ApiErrorBanner error={globalError} onDismiss={() => setGlobalError(null)} />
          {children ? (
            children({ activeTab, setError: setGlobalError })
          ) : (
            <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-slate-500 dark:border-slate-700">
              Zone active : <strong className="capitalize">{activeTab}</strong>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
