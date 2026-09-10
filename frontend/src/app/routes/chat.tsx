import { createFileRoute } from '@tanstack/react-router'
import { ChatScreen } from '@features/chat'

export const Route = createFileRoute('/chat')({
  component: ChatRouteComponent,
})

function ChatRouteComponent() {
  return (
    <div className="mx-auto h-[78vh] max-w-4xl">
      <ChatScreen sessionId="session-test" />
    </div>
  )
}
