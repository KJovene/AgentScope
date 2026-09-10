import { createFileRoute } from '@tanstack/react-router'

import { AgentChat } from '@features/mapping-agent'

export const Route = createFileRoute('/chat')({
  component: ChatRouteComponent,
})

/** Full-page view of the same conversation the floating assistant hosts. */
function ChatRouteComponent() {
  return (
    <div className="mx-auto h-[78vh] max-w-4xl">
      <AgentChat className="h-full" />
    </div>
  )
}
