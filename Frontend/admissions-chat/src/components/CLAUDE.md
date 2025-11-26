# Components - React Component Development Guidelines

## Overview

This directory contains all React components for the application, organized into base UI components, form components, landing page components, and chat interface components.

## Component Organization

```
src/components/
├── CLAUDE.md                          # This file
├── ui/                                # Base UI components (Radix-based)
│   ├── button.tsx                     # Button with variants
│   ├── input.tsx                      # Form input field
│   ├── card.tsx                       # Card container
│   ├── label.tsx                      # Form label
│   └── select.tsx                     # Dropdown select
├── inquiry-form.tsx                   # Inquiry form component
├── landing-page.tsx                   # Landing page component
└── nemo/                              # Chat interface components
    ├── nemo-chat-interface.tsx        # Main chat interface
    ├── chat-header.tsx                # Chat header with branding
    ├── chat-input.tsx                 # Message input field
    ├── chat-message.tsx               # Message bubble
    ├── markdown-renderer.tsx          # Markdown formatting
    ├── tool-card.tsx                  # Tool usage indicator
    ├── empty-state.tsx                # Empty chat state
    ├── loader.tsx                     # Loading animation
    └── scroll-button.tsx              # Scroll to bottom button
```

## Component Development Standards

### General Guidelines

1. **Use TypeScript**: All components must have explicit prop types
2. **Functional Components**: Use function declarations, not arrow functions for named exports
3. **Client vs Server Components**:
   - Default to Server Components (no 'use client')
   - Add 'use client' only when using hooks, event handlers, or browser APIs
4. **Prop Naming**: Use camelCase for prop names
5. **Event Handlers**: Prefix with `on` (e.g., `onClick`, `onSubmit`)
6. **CSS Classes**: Use Tailwind utilities with `cn()` helper for conditional classes

### Component Template

```typescript
// Component with props and proper typing
interface ComponentNameProps {
  prop1: string;
  prop2?: number;  // Optional props with ?
  onAction?: () => void;
  children?: React.ReactNode;
}

export function ComponentName({
  prop1,
  prop2 = 10,  // Default values
  onAction,
  children
}: ComponentNameProps) {
  return (
    <div className="...">
      {children}
    </div>
  );
}
```

## Base UI Components

### Button Component

```typescript
// src/components/ui/button.tsx
import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/90',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        outline: 'border border-input hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        sm: 'h-9 px-3',
        md: 'h-10 px-4 py-2',
        lg: 'h-11 px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : 'button';
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}
```

### Input Component

```typescript
// src/components/ui/input.tsx
import * as React from 'react';
import { cn } from '@/lib/utils';

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, label, error, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium mb-1">
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <input
          type={type}
          className={cn(
            'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-red-500 focus-visible:ring-red-500',
            className
          )}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-red-500">{error}</p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';
```

## Form Components

### Inquiry Form Component

```typescript
// src/components/inquiry-form.tsx
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { submitInquiryForm, type FormData } from '@/lib/form-api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

// Form validation schema (Property 1: Form validation rejects empty required fields)
const formSchema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  email: z.string().email('Invalid email address'),
  cellPhone: z.string().min(10, 'Valid phone number required'),
  homePhone: z.string().optional(),
  headquarters: z.string().min(1, 'Please select a campus'),
  programType: z.string().min(1, 'Please select a program type'),
});

interface InquiryFormProps {
  onSuccess: (formContext: string) => void;
}

export function InquiryForm({ onSuccess }: InquiryFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const result = await submitInquiryForm(data);

      if (result.success) {
        // Property 3: Successful Lead creation opens chat with context
        const formContext = `Student Information:
- Name: ${data.firstName} ${data.lastName}
- Email: ${data.email}
- Phone: ${data.cellPhone}
- Campus Interest: ${data.headquarters}
- Program Type: ${data.programType}`;

        onSuccess(formContext);
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="First Name"
          {...register('firstName')}
          error={errors.firstName?.message}
          required
        />
        <Input
          label="Last Name"
          {...register('lastName')}
          error={errors.lastName?.message}
          required
        />
      </div>

      <Input
        label="Email"
        type="email"
        {...register('email')}
        error={errors.email?.message}
        required
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Cell Phone"
          type="tel"
          placeholder="+1 (555) 123-4567"
          {...register('cellPhone')}
          error={errors.cellPhone?.message}
          required
        />
        <Input
          label="Home Phone (Optional)"
          type="tel"
          {...register('homePhone')}
        />
      </div>

      <select
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        {...register('headquarters')}
      >
        <option value="">Select Campus *</option>
        <option value="Manila">Manila Campus</option>
        <option value="Makati">Makati Campus</option>
        <option value="Cebu">Cebu Campus</option>
      </select>
      {errors.headquarters && (
        <p className="text-sm text-red-500">{errors.headquarters.message}</p>
      )}

      <select
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        {...register('programType')}
      >
        <option value="">Select Program Type *</option>
        <option value="Undergraduate">Undergraduate</option>
        <option value="Graduate">Graduate</option>
        <option value="Doctorate">Doctorate</option>
      </select>
      {errors.programType && (
        <p className="text-sm text-red-500">{errors.programType.message}</p>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      <Button
        type="submit"
        className="w-full"
        disabled={isSubmitting}
      >
        {isSubmitting ? 'Submitting...' : 'Start Chat with Nemo'}
      </Button>
    </form>
  );
}
```

## Chat Interface Components

### Main Chat Interface

```typescript
// src/components/nemo/nemo-chat-interface.tsx
'use client';

import { useState, useEffect } from 'react';
import { useChat } from '@/hooks/use-chat';
import { useStickToBottom } from '@/hooks/use-stick-to-bottom';
import { ChatHeader } from './chat-header';
import { ChatMessage } from './chat-message';
import { ChatInput } from './chat-input';
import { EmptyState } from './empty-state';
import { ToolCard } from './tool-card';
import { Loader } from './loader';

interface NemoChatInterfaceProps {
  phoneNumber: string;
  formContext?: string;
  onClose?: () => void;
}

export function NemoChatInterface({
  phoneNumber,
  formContext,
  onClose,
}: NemoChatInterfaceProps) {
  const [sessionId] = useState(() => crypto.randomUUID()); // Property 12: Session IDs are unique

  const {
    messages,
    isStreaming,
    currentStreamingMessage,
    currentTool,
    sendMessage,
    regenerateLastMessage,
  } = useChat(sessionId, phoneNumber);

  const { containerRef, isAtBottom, scrollToBottom } = useStickToBottom<HTMLDivElement>();

  // Send initial message with form context
  useEffect(() => {
    if (formContext && messages.length === 0) {
      sendMessage('Hello!', formContext);
    }
  }, [formContext, messages.length, sendMessage]);

  const handleSendMessage = async (content: string) => {
    await sendMessage(content);
    scrollToBottom();
  };

  return (
    <div className="flex flex-col h-full bg-background" data-testid="chat-interface">
      <ChatHeader onClose={onClose} />

      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 && !isStreaming && (
          <EmptyState />
        )}

        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            onRegenerate={message.type === 'ai' ? regenerateLastMessage : undefined}
          />
        ))}

        {/* Show streaming message (Property 5: AI responses stream incrementally) */}
        {isStreaming && currentStreamingMessage && (
          <ChatMessage
            message={{
              id: 'streaming',
              type: 'ai',
              content: currentStreamingMessage,
              timestamp: Date.now(),
            }}
            isStreaming
          />
        )}

        {/* Show tool usage indicator (Property 11, 18, 40) */}
        {currentTool && (
          <ToolCard
            icon={currentTool.icon}
            message={currentTool.message}
            state={currentTool.state}
          />
        )}

        {/* Show loading dots when streaming starts */}
        {isStreaming && !currentStreamingMessage && !currentTool && (
          <Loader />
        )}
      </div>

      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={isStreaming}
      />
    </div>
  );
}
```

### Chat Message Component

```typescript
// src/components/nemo/chat-message.tsx
'use client';

import { Message } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { MarkdownRenderer } from './markdown-renderer';
import { cn } from '@/lib/utils';
import { RotateCcw } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  onRegenerate?: () => void;
}

export function ChatMessage({
  message,
  isStreaming = false,
  onRegenerate,
}: ChatMessageProps) {
  const isUser = message.type === 'user';

  return (
    <div
      className={cn(
        'flex w-full',
        isUser ? 'justify-end' : 'justify-start'
      )}
      data-testid={isUser ? 'user-message' : 'ai-message'}
    >
      <div
        className={cn(
          'max-w-[80%] rounded-lg p-4',
          isUser
            ? 'bg-user text-user-foreground'  // Property 4: User messages display with correct styling
            : 'bg-ai text-ai-foreground'
        )}
      >
        <div className="prose prose-sm max-w-none">
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <MarkdownRenderer content={message.content} />
          )}
        </div>

        {/* Timestamp */}
        <p className="text-xs opacity-60 mt-2">
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>

        {/* Regenerate button for AI messages (Property 6: Completed AI messages include regenerate button) */}
        {!isUser && !isStreaming && onRegenerate && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRegenerate}
            className="mt-2"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Regenerate
          </Button>
        )}
      </div>
    </div>
  );
}
```

### Markdown Renderer Component

```typescript
// src/components/nemo/markdown-renderer.tsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeHighlight]}
      components={{
        // Custom styling for markdown elements
        a: ({ node, ...props }) => (
          <a
            {...props}
            className="text-primary underline hover:no-underline"
            target="_blank"
            rel="noopener noreferrer"
          />
        ),
        code: ({ node, inline, ...props }) =>
          inline ? (
            <code
              {...props}
              className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono"
            />
          ) : (
            <code {...props} className="block p-4 rounded-lg overflow-x-auto" />
          ),
        ul: ({ node, ...props }) => (
          <ul {...props} className="list-disc list-inside space-y-1" />
        ),
        ol: ({ node, ...props }) => (
          <ol {...props} className="list-decimal list-inside space-y-1" />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
```

### Tool Card Component

```typescript
// src/components/nemo/tool-card.tsx
import { cn } from '@/lib/utils';

interface ToolCardProps {
  icon: string;
  message: string;
  state: 'running' | 'completed';
}

export function ToolCard({ icon, message, state }: ToolCardProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 p-4 rounded-lg border',
        state === 'running'
          ? 'bg-blue-50 border-blue-200'
          : 'bg-green-50 border-green-200'
      )}
      data-testid="tool-indicator"
    >
      <span className="text-2xl">{icon}</span>
      <div className="flex-1">
        <p className="text-sm font-medium">{message}</p>
        {state === 'running' && (
          <div className="flex gap-1 mt-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        )}
      </div>
    </div>
  );
}
```

### Chat Input Component

```typescript
// src/components/nemo/chat-input.tsx
'use client';

import { useState, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t p-4">
      <div className="flex gap-2">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          className="flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          rows={1}
          disabled={disabled}
          data-testid="chat-input"
        />
        <Button
          onClick={handleSubmit}
          disabled={disabled || !message.trim()}
          size="icon"
          data-testid="send-button"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
```

### Empty State Component

```typescript
// src/components/nemo/empty-state.tsx
import { MessageSquare } from 'lucide-react';

const suggestedQuestions = [
  'What programs does the university offer?',
  'What are the admissions requirements?',
  'Tell me about campus life',
  'What scholarships are available?',
];

interface EmptyStateProps {
  onSelectQuestion?: (question: string) => void;
}

export function EmptyState({ onSelectQuestion }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <MessageSquare className="w-16 h-16 text-muted-foreground mb-4" />
      <h3 className="text-xl font-semibold mb-2">Chat with Nemo</h3>
      <p className="text-muted-foreground mb-6">
        Ask me anything about our university programs, admissions, and campus life!
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
        {suggestedQuestions.map((question) => (
          <button
            key={question}
            onClick={() => onSelectQuestion?.(question)}
            className="p-3 text-sm text-left border rounded-lg hover:bg-accent transition-colors"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
}
```

## Component Testing

### Unit Test Example

```typescript
// __tests__/unit/components/chat-message.test.tsx
import { render, screen } from '@testing-library/react';
import { ChatMessage } from '@/components/nemo/chat-message';

describe('ChatMessage', () => {
  it('renders user message with correct styling', () => {
    const message = {
      id: '1',
      type: 'user' as const,
      content: 'Hello',
      timestamp: Date.now(),
    };

    render(<ChatMessage message={message} />);

    const messageEl = screen.getByTestId('user-message');
    expect(messageEl).toHaveClass('justify-end');
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('renders AI message with regenerate button', () => {
    const message = {
      id: '2',
      type: 'ai' as const,
      content: 'Hi there!',
      timestamp: Date.now(),
    };

    const onRegenerate = jest.fn();

    render(<ChatMessage message={message} onRegenerate={onRegenerate} />);

    const regenerateBtn = screen.getByText('Regenerate');
    expect(regenerateBtn).toBeInTheDocument();
  });
});
```

## Accessibility Guidelines

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Logical tab order throughout the interface
- Visible focus indicators

### ARIA Labels
```typescript
<button aria-label="Close chat" onClick={onClose}>
  <X className="w-4 h-4" />
</button>

<input
  aria-label="Type your message"
  aria-describedby="input-help"
  placeholder="Type here..."
/>
```

### Color Contrast
- Text: 4.5:1 minimum contrast ratio (WCAG AA)
- Large text (18px+): 3:1 minimum
- Interactive elements: 3:1 minimum

### Screen Reader Support
- Use semantic HTML (`<nav>`, `<main>`, `<article>`)
- Provide alt text for all images
- Use `aria-live` for dynamic content updates

```typescript
<div aria-live="polite" aria-atomic="true">
  {isStreaming && <p>AI is typing...</p>}
</div>
```

## Performance Best Practices

1. **Memoization**: Use `React.memo` for expensive renders
```typescript
export const ChatMessage = React.memo(ChatMessageComponent);
```

2. **Lazy Loading**: Dynamic imports for heavy components
```typescript
const HeavyComponent = dynamic(() => import('./heavy-component'), {
  loading: () => <Loader />,
});
```

3. **Virtual Scrolling**: For long message lists (use `react-window`)

4. **Debouncing**: For search and input validation

## Related Documentation

- **Frontend Guide**: See `../CLAUDE.md` for overall frontend architecture
- **Hooks**: See `src/hooks/` for custom React hooks
- **API Clients**: See `src/lib/` for API integration
- **Requirements**: See `docs/kiro docs/requirements.md` for component requirements
- **Design Specs**: See `docs/kiro docs/design.md` for detailed component interfaces
