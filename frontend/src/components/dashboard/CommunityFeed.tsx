import React from 'react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Heart, MessageCircle } from 'lucide-react'
import type { CommunityPost } from '@/lib/mock-data'

interface CommunityFeedProps {
  posts: CommunityPost[]
}

export function CommunityFeed({ posts }: CommunityFeedProps) {
  return (
    <div className="space-y-3">
      {posts.map((post) => (
        <Card key={post.id}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-semibold text-sm">{post.author}</p>
                <p className="text-xs text-muted-foreground">{post.timestamp}</p>
              </div>
            </div>

            <p className="text-sm text-foreground mb-3">{post.content}</p>

            <div className="flex gap-1 mb-3 flex-wrap">
              {post.tags.map((tag) => (
                <Badge key={tag} variant="info" className="text-xs">
                  #{tag}
                </Badge>
              ))}
            </div>

            <div className="flex gap-4 text-xs text-muted-foreground">
              <button className="flex items-center gap-1 hover:text-success transition-colors">
                <Heart size={14} />
                {post.likes}
              </button>
              <button className="flex items-center gap-1 hover:text-primary transition-colors">
                <MessageCircle size={14} />
                {post.replies}
              </button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
