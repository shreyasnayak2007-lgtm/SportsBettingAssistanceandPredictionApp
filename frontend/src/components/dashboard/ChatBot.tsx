'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Send } from 'lucide-react'

interface Message {
  id: string
  sender: 'user' | 'assistant'
  content: string
}

export function ChatBot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'assistant',
      content:
        "Hi! I'm your sports betting assistant. Ask me anything about odds, player props, or betting strategies.",
    },
  ])
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      content: input,
    }

    setMessages((prev) => [...prev, userMessage])

    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        content:
          "That's a great question! Based on current trends and analysis, I'd recommend checking the latest stats and consensus picks.",
      }
      setMessages((prev) => [...prev, assistantMessage])
    }, 500)

    setInput('')
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="text-base">Betting Assistant</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-2">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.sender === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                  msg.sender === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask a question..."
            className="text-sm"
          />
          <Button size="sm" onClick={handleSend} variant="primary">
            <Send size={16} />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
