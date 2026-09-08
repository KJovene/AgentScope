import { createFileRoute } from '@tanstack/react-router'
import { ChatScreen } from '@features/chat'

export const Route = createFileRoute('/chat')({
  component: ChatRouteComponent,
})

function ChatRouteComponent() {
  return <ChatScreen sessionId="session-test" />
}
