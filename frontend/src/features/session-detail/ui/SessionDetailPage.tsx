import React from "react";
import { useParams } from "@tanstack/react-router";
import { SessionTimeline } from "./SessionTimeline";

export const SessionDetailPage: React.FC = () => {
  const { sessionId } = useParams({ strict: false });

  const mockSession = {
    id: sessionId || "sess-demo",
    status: "completed" as const,
    createdAt: new Date().toISOString(),
    totalTokens: 1250,
    totalCost: 0.025,
    events: [],
  };

  return (
    <div className="p-6">
      <SessionTimeline session={mockSession} />
    </div>
  );
};
