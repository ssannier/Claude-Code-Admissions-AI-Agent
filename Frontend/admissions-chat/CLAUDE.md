# Frontend - Next.js Application Development Guidelines

## Overview

This is a Next.js 15 application providing a modern landing page with inquiry form and real-time chat interface powered by SSE (Server-Sent Events) streaming from the AI agent.

**Framework**: Next.js 15 (App Router)
**UI Library**: React 19
**Language**: TypeScript 5
**Styling**: Tailwind CSS 4
**Component Library**: Radix UI

## Directory Structure

```
Frontend/admissions-chat/
├── CLAUDE.md                          # This file
├── package.json                       # Dependencies
├── tsconfig.json                      # TypeScript strict mode
├── next.config.js                     # Next.js configuration
├── tailwind.config.ts                 # Tailwind CSS customization
├── postcss.config.js                  # PostCSS configuration
├── .env.local.example                 # Environment variables template
├── .gitignore
├── public/                            # Static assets
│   ├── logos/
│   │   ├── university-logo.png
│   │   └── nemo-logo.png
│   ├── images/
│   │   └── hero-image.jpg
│   └── favicon.ico
└── src/
    ├── app/                           # Next.js App Router
    │   ├── layout.tsx                 # Root layout
    │   ├── page.tsx                   # Landing page
    │   ├── globals.css                # Global styles with CSS variables
    │   └── error.tsx                  # Error boundary
    ├── components/                    # See components/CLAUDE.md
    │   ├── CLAUDE.md
    │   ├── ui/                        # Base UI components
    │   ├── inquiry-form.tsx
    │   ├── landing-page.tsx
    │   └── nemo/                      # Chat interface components
    ├── lib/                           # Utilities and API clients
    │   ├── utils.ts                   # General utilities
    │   ├── config.ts                  # Environment configuration
    │   ├── agent-client.ts            # SSE streaming client
    │   ├── form-api.ts                # Form submission API
    │   └── types.ts                   # TypeScript types
    └── hooks/                         # Custom React hooks
        ├── use-stick-to-bottom.ts     # Auto-scroll hook
        └── use-chat.ts                # Chat state management
```

## Tech Stack

### Core Framework
```json
{
  "next": "^15.0.0",
  "react": "^19.0.0",
  "react-dom": "^19.0.0",
  "typescript": "^5.0.0"
}
```

### Styling
```json
{
  "tailwindcss": "^4.0.0",
  "autoprefixer": "^10.4.0",
  "postcss": "^8.4.0",
  "@radix-ui/react-slot": "^1.0.0",
  "class-variance-authority": "^0.7.0",
  "clsx": "^2.0.0",
  "tailwind-merge": "^2.0.0"
}
```

### UI Components
```json
{
  "@radix-ui/react-dialog": "^1.0.0",
  "@radix-ui/react-label": "^2.0.0",
  "@radix-ui/react-select": "^2.0.0",
  "react-markdown": "^9.0.0",
  "remark-gfm": "^4.0.0",
  "rehype-highlight": "^7.0.0"
}
```

### Form & Validation
```json
{
  "react-hook-form": "^7.50.0",
  "zod": "^3.22.0",
  "@hookform/resolvers": "^3.3.0"
}
```

## Configuration

### Environment Variables

```bash
# .env.local.example

# API Endpoints
NEXT_PUBLIC_AGENT_PROXY_URL=https://your-lambda-function-url.lambda-url.us-east-1.on.aws
NEXT_PUBLIC_FORM_SUBMISSION_API=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/submit

# University Branding
NEXT_PUBLIC_UNIVERSITY_NAME=Your University Name
NEXT_PUBLIC_UNIVERSITY_SHORT_NAME=YUN

# Optional: Analytics
NEXT_PUBLIC_GA_TRACKING_ID=G-XXXXXXXXXX
```

### Config File

```typescript
// src/lib/config.ts
export const config = {
  agentProxyUrl: process.env.NEXT_PUBLIC_AGENT_PROXY_URL || '',
  formSubmissionApi: process.env.NEXT_PUBLIC_FORM_SUBMISSION_API || '',
  universityName: process.env.NEXT_PUBLIC_UNIVERSITY_NAME || 'University',
  universityShortName: process.env.NEXT_PUBLIC_UNIVERSITY_SHORT_NAME || 'UNI',
} as const;

// Validate required env vars
if (!config.agentProxyUrl) {
  throw new Error('NEXT_PUBLIC_AGENT_PROXY_URL is required');
}

if (!config.formSubmissionApi) {
  throw new Error('NEXT_PUBLIC_FORM_SUBMISSION_API is required');
}
```

### Next.js Configuration

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Enable experimental features for React 19
  experimental: {
    reactCompiler: true,
  },

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    domains: [], // Add your CDN domains if using external images
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
```

### Tailwind Configuration

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // University brand colors (customize per institution)
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        // Chat UI colors
        user: {
          DEFAULT: 'hsl(var(--user-message))',
          foreground: 'hsl(var(--user-message-foreground))',
        },
        ai: {
          DEFAULT: 'hsl(var(--ai-message))',
          foreground: 'hsl(var(--ai-message-foreground))',
        },
      },
      animation: {
        'typing': 'typing 1.5s infinite',
        'fade-in': 'fadeIn 0.3s ease-in',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        typing: {
          '0%, 100%': { opacity: '0.2' },
          '50%': { opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
```

### Global Styles

```css
/* src/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* University brand colors - customize per institution */
    --primary: 210 100% 50%;
    --primary-foreground: 0 0% 100%;
    --secondary: 30 100% 50%;
    --secondary-foreground: 0 0% 100%;

    /* Chat UI colors */
    --user-message: 220 70% 50%;
    --user-message-foreground: 0 0% 100%;
    --ai-message: 0 0% 95%;
    --ai-message-foreground: 0 0% 10%;

    /* Background and foreground */
    --background: 0 0% 100%;
    --foreground: 0 0% 10%;

    /* Border and input */
    --border: 214 32% 91%;
    --input: 214 32% 91%;
    --ring: 210 100% 50%;

    /* Glass-morphism effect */
    --glass-bg: rgba(255, 255, 255, 0.7);
    --glass-border: rgba(255, 255, 255, 0.3);
  }

  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}

@layer utilities {
  .glass-morphism {
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border);
  }
}
```

## API Client Development

### SSE Streaming Client

```typescript
// src/lib/agent-client.ts
import { config } from './config';

export type AgentStreamEvent =
  | { type: 'response'; content: string }
  | { type: 'tool_status'; icon: string; message: string }
  | { type: 'tool_result'; content: string }
  | { type: 'final'; content: string }
  | { type: 'error'; message: string };

/**
 * Stream chat responses from the agent via SSE.
 *
 * Property 35: Message send establishes SSE connection
 * Property 36: Chunks forwarded as SSE events
 * Property 37: SSE events normalized to standard type
 */
export async function* streamChatResponse(params: {
  message: string;
  sessionId: string;
  phoneNumber: string;
  systemMessage?: string;
}): AsyncGenerator<AgentStreamEvent> {
  const { message, sessionId, phoneNumber, systemMessage } = params;

  try {
    const response = await fetch(config.agentProxyUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: message,
        session_id: sessionId,
        phone_number: phoneNumber,
        system_message: systemMessage,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events (format: "data: {json}\n\n")
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.trim() || !line.startsWith('data: ')) continue;

        const jsonStr = line.slice(6); // Remove "data: " prefix

        try {
          const raw = JSON.parse(jsonStr);
          const event = normalizeRawEvent(raw);
          if (event) yield event;
        } catch (e) {
          console.error('Failed to parse SSE event:', jsonStr, e);
        }
      }
    }
  } catch (error) {
    console.error('SSE streaming error:', error);
    yield {
      type: 'error',
      message: 'Connection error. Please try again.',
    };
  }
}

/**
 * Normalize various backend event formats to standard AgentStreamEvent.
 *
 * Property 37: SSE events normalized to standard type
 */
function normalizeRawEvent(raw: any): AgentStreamEvent | null {
  // Response chunk
  if ('response' in raw) {
    return { type: 'response', content: raw.response };
  }

  // Tool usage indicator
  if ('thinking' in raw) {
    const thinking = raw.thinking;
    // Parse "🔍 Searching knowledge base" format
    const icon = thinking.charAt(0);
    const message = thinking.slice(1).trim();
    return { type: 'tool_status', icon, message };
  }

  // Tool result
  if ('tool_result' in raw) {
    return { type: 'tool_result', content: raw.tool_result };
  }

  // Final result
  if ('final_result' in raw) {
    return { type: 'final', content: raw.final_result };
  }

  // Error
  if ('error' in raw) {
    return { type: 'error', message: raw.error };
  }

  return null;
}
```

### Form Submission Client

```typescript
// src/lib/form-api.ts
import { config } from './config';

export interface FormData {
  firstName: string;
  lastName: string;
  email: string;
  cellPhone: string;
  homePhone?: string;
  headquarters: string;
  programType: string;
}

export interface FormSubmissionResponse {
  success: boolean;
  message: string;
  leadId?: string;
}

/**
 * Submit inquiry form to create Salesforce Lead.
 *
 * Property 2: Valid form submission creates Salesforce Lead
 */
export async function submitInquiryForm(
  data: FormData
): Promise<FormSubmissionResponse> {
  try {
    const response = await fetch(config.formSubmissionApi, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.message || 'Form submission failed');
    }

    return result;
  } catch (error) {
    console.error('Form submission error:', error);
    return {
      success: false,
      message: 'Failed to submit form. Please try again.',
    };
  }
}
```

## TypeScript Type Definitions

```typescript
// src/lib/types.ts

/** Chat message in the interface */
export interface Message {
  id: string;                    // UUID
  type: 'user' | 'ai';           // Message sender
  content: string;               // Message text (markdown for AI)
  timestamp: number;             // Unix timestamp
  toolStatus?: ToolStatus;       // Optional tool usage indicator
}

/** Tool usage indicator */
export interface ToolStatus {
  icon: string;                  // Emoji icon (🔍, 🤝)
  message: string;               // Status message
  state: 'running' | 'completed'; // Tool execution state
}

/** Form data structure */
export interface FormData {
  firstName: string;
  lastName: string;
  email: string;
  cellPhone: string;
  homePhone?: string;            // Optional
  headquarters: string;          // Campus location
  programType: string;           // undergraduate, graduate, etc.
}

/** Chat state management */
export interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  currentStreamingMessage: string;
  currentTool: ToolStatus | null;
  sessionId: string;
}
```

## Custom Hooks

### Auto-Scroll Hook

```typescript
// src/hooks/use-stick-to-bottom.ts
import { useEffect, useRef, useState } from 'react';

/**
 * Hook to manage automatic scrolling to bottom of a container.
 * Returns a ref to attach to the container and a function to manually scroll.
 */
export function useStickToBottom<T extends HTMLElement>() {
  const containerRef = useRef<T>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);

  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const atBottom = scrollHeight - scrollTop - clientHeight < 50;
      setIsAtBottom(atBottom);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  // Auto-scroll when new messages arrive if user is at bottom
  useEffect(() => {
    if (isAtBottom) {
      scrollToBottom();
    }
  }, [isAtBottom]);

  return { containerRef, isAtBottom, scrollToBottom };
}
```

### Chat State Hook

```typescript
// src/hooks/use-chat.ts
import { useState, useCallback } from 'react';
import { streamChatResponse } from '@/lib/agent-client';
import type { Message, ToolStatus } from '@/lib/types';

export function useChat(sessionId: string, phoneNumber: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');
  const [currentTool, setCurrentTool] = useState<ToolStatus | null>(null);

  const sendMessage = useCallback(
    async (content: string, systemMessage?: string) => {
      // Add user message
      const userMessage: Message = {
        id: crypto.randomUUID(),
        type: 'user',
        content,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Start streaming AI response
      setIsStreaming(true);
      setCurrentStreamingMessage('');
      setCurrentTool(null);

      try {
        for await (const event of streamChatResponse({
          message: content,
          sessionId,
          phoneNumber,
          systemMessage,
        })) {
          if (event.type === 'response') {
            setCurrentStreamingMessage((prev) => prev + event.content);
          } else if (event.type === 'tool_status') {
            setCurrentTool({
              icon: event.icon,
              message: event.message,
              state: 'running',
            });
          } else if (event.type === 'tool_result') {
            if (currentTool) {
              setCurrentTool({ ...currentTool, state: 'completed' });
            }
          } else if (event.type === 'final') {
            const aiMessage: Message = {
              id: crypto.randomUUID(),
              type: 'ai',
              content: event.content,
              timestamp: Date.now(),
              toolStatus: currentTool || undefined,
            };
            setMessages((prev) => [...prev, aiMessage]);
            setCurrentStreamingMessage('');
            setCurrentTool(null);
          } else if (event.type === 'error') {
            // Property 41: Error events hide technical details
            const errorMessage: Message = {
              id: crypto.randomUUID(),
              type: 'ai',
              content: event.message,
              timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, errorMessage]);
            setCurrentStreamingMessage('');
          }
        }
      } finally {
        setIsStreaming(false);
      }
    },
    [sessionId, phoneNumber, currentTool]
  );

  const regenerateLastMessage = useCallback(() => {
    if (messages.length < 2) return;

    // Remove last AI message
    const updatedMessages = messages.slice(0, -1);
    const lastUserMessage = updatedMessages[updatedMessages.length - 1];

    setMessages(updatedMessages);
    sendMessage(lastUserMessage.content);
  }, [messages, sendMessage]);

  return {
    messages,
    isStreaming,
    currentStreamingMessage,
    currentTool,
    sendMessage,
    regenerateLastMessage,
  };
}
```

## Development Workflow

### Local Development

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your API endpoints

# Run development server
npm run dev

# Open http://localhost:3000
```

### Building for Production

```bash
# Build optimized production bundle
npm run build

# Test production build locally
npm start
```

### Linting and Formatting

```bash
# Run ESLint
npm run lint

# Format code with Prettier
npm run format
```

## Testing Strategy

### Unit Tests (Jest + React Testing Library)

```typescript
// __tests__/unit/lib/agent-client.test.ts
import { normalizeRawEvent } from '@/lib/agent-client';

describe('Agent Client', () => {
  it('normalizes response events', () => {
    const event = normalizeRawEvent({ response: 'Hello' });
    expect(event).toEqual({ type: 'response', content: 'Hello' });
  });

  it('normalizes tool status events', () => {
    const event = normalizeRawEvent({ thinking: '🔍 Searching' });
    expect(event).toEqual({
      type: 'tool_status',
      icon: '🔍',
      message: 'Searching',
    });
  });
});
```

### Integration Tests (Playwright)

```typescript
// __tests__/e2e/user-journey.spec.ts
import { test, expect } from '@playwright/test';

test('complete user journey', async ({ page }) => {
  // Visit landing page
  await page.goto('/');

  // Fill inquiry form
  await page.fill('[name="firstName"]', 'John');
  await page.fill('[name="lastName"]', 'Doe');
  await page.fill('[name="email"]', 'john@example.com');
  await page.fill('[name="cellPhone"]', '+15551234567');
  await page.selectOption('[name="headquarters"]', 'Manila');
  await page.selectOption('[name="programType"]', 'Undergraduate');

  // Submit form
  await page.click('button[type="submit"]');

  // Chat should open
  await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible();

  // Send a message
  await page.fill('[data-testid="chat-input"]', 'What programs do you offer?');
  await page.click('[data-testid="send-button"]');

  // Wait for AI response
  await expect(page.locator('[data-testid="ai-message"]')).toBeVisible({
    timeout: 10000,
  });
});
```

## Performance Optimization

### Code Splitting
- Use dynamic imports for heavy components
- Lazy load chat interface until form is submitted

```typescript
// src/app/page.tsx
import dynamic from 'next/dynamic';

const NemoChatInterface = dynamic(
  () => import('@/components/nemo/nemo-chat-interface'),
  { ssr: false }
);
```

### Image Optimization
- Use Next.js `<Image>` component
- Serve images in WebP/AVIF formats
- Lazy load images below the fold

### Bundle Analysis

```bash
# Analyze bundle size
npm run build
npx @next/bundle-analyzer
```

## Accessibility

- **Keyboard Navigation**: All interactive elements accessible via Tab
- **Screen Reader Support**: ARIA labels on all buttons and inputs
- **Color Contrast**: WCAG AA compliant (4.5:1 for normal text)
- **Focus Indicators**: Visible focus outlines on all focusable elements

## Security Best Practices

1. **Content Security Policy**: Configure CSP headers in `next.config.js`
2. **Input Sanitization**: Validate all form inputs before submission
3. **XSS Prevention**: Use React's built-in XSS protection, sanitize markdown
4. **HTTPS Only**: Enforce HTTPS in production
5. **Rate Limiting**: Implement client-side rate limiting for API calls

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### AWS Amplify

```bash
# Use deploy script from Backend/admissions-ai-agent/deploy-scripts/
./frontend-amplify-deploy.sh
```

### Docker

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

## Related Documentation

- **Components**: See `src/components/CLAUDE.md` for component development patterns
- **Backend Integration**: See `Backend/admissions-ai-agent/lambda/CLAUDE.md` for API contracts
- **Requirements**: See `docs/kiro docs/requirements.md` for frontend requirements
- **Design System**: See `docs/kiro docs/design.md` for UI component specifications
