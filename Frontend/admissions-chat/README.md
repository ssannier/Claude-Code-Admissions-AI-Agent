# Admissions Chat Frontend

Next.js 15 frontend application for the AI Admissions Agent with real-time SSE streaming.

## Overview

This is the user-facing interface for prospective students to:
1. Submit inquiry forms to create Salesforce Leads
2. Chat with the AI admissions advisor in real-time
3. Receive streaming responses via Server-Sent Events

## Features

- **Inquiry Form**: Collects student information and creates Salesforce Lead
- **Real-time Chat**: SSE-based streaming for instant AI responses
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Session Management**: Tracks conversations with unique session IDs
- **Error Handling**: User-friendly error messages and retry logic

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React hooks
- **API Communication**: Fetch API with SSE support

## Project Structure

```
admissions-chat/
├── app/
│   ├── globals.css          # Global styles with Tailwind
│   ├── layout.tsx            # Root layout
│   └── page.tsx              # Home page (form + chat)
├── components/
│   ├── InquiryForm.tsx       # Form submission component
│   └── ChatInterface.tsx     # Chat UI with streaming
├── hooks/
│   └── useSSEChat.ts         # SSE client hook
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── README.md
```

## Components

### 1. InquiryForm

**Purpose**: Collect student information and submit to Form Submission Lambda

**Props**:
- `onSubmitSuccess: (data) => void` - Callback after successful form submission

**Features**:
- Form validation (required fields, email format, phone format)
- API integration with Form Submission Lambda
- Error handling with user feedback
- Loading states during submission

**Fields**:
- First Name (required)
- Last Name (required)
- Email (required)
- Cell Phone (required)
- Preferred Campus (required) - Manila, Makati, Cebu, Davao
- Program Type (required) - Undergraduate, Graduate, Doctorate
- Timing Preference - as soon as possible, 2 hours, 4 hours, tomorrow morning

### 2. ChatInterface

**Purpose**: Real-time chat with AI agent via SSE streaming

**Props**:
- `sessionData: { phoneNumber, studentName, sessionId }` - Session information
- `onBack: () => void` - Return to form callback

**Features**:
- Message list with user/assistant avatars
- Real-time streaming responses with typing indicator
- Auto-scroll to latest message
- Loading states (dots animation)
- Error display with retry option
- Session ID display for debugging

### 3. useSSEChat Hook

**Purpose**: Handle SSE communication with Agent Proxy Lambda

**Parameters**:
- `agentProxyUrl` - Agent Proxy Lambda Function URL
- `sessionId` - Unique session identifier
- `phoneNumber` - Student's phone (optional)
- `studentName` - Student's name (optional)

**Returns**:
- `messages: ChatMessage[]` - Array of chat messages
- `isStreaming: boolean` - Whether actively receiving response
- `error: string | null` - Error message if any
- `currentResponse: string` - Accumulated text from current stream
- `sendMessage: (prompt: string) => Promise<void>` - Send message function
- `cancelStream: () => void` - Cancel ongoing stream

**SSE Event Types**:
- `connected` - Connection established
- `chunk` - Text chunk from agent
- `complete` - Response completed
- `error` - Error occurred

## Environment Variables

Create `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=https://your-api-gateway-url.amazonaws.com/prod
NEXT_PUBLIC_AGENT_PROXY_URL=https://your-agent-proxy-function-url.amazonaws.com
```

For local development:
```bash
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_AGENT_PROXY_URL=http://localhost:3002
```

## Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Development

### Running Locally

1. Start the development server:
```bash
npm run dev
```

2. Open http://localhost:3000

3. Make sure backend services are running:
   - Form Submission Lambda (or mock at :3001)
   - Agent Proxy Lambda (or mock at :3002)

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## API Integration

### Form Submission API

**Endpoint**: `POST ${NEXT_PUBLIC_API_URL}/submit`

**Request**:
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com",
  "cellPhone": "+15551234567",
  "headquarters": "Manila",
  "programType": "Undergraduate",
  "timingPreference": "2 hours"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "message": "Form submitted successfully",
  "leadId": "00Q5e000001abcDEFG"
}
```

**Response (Error)**:
```json
{
  "success": false,
  "message": "Email address is required"
}
```

### Agent Proxy SSE API

**Endpoint**: `POST ${NEXT_PUBLIC_AGENT_PROXY_URL}`

**Request**:
```json
{
  "prompt": "What are the admission requirements?",
  "session_id": "session-123",
  "phone_number": "+15551234567",
  "student_name": "John Doe"
}
```

**Response (SSE Stream)**:
```
event: connection
data: {"type":"connected","sessionId":"session-123","timestamp":"2024-01-15T10:30:00.000Z"}

event: chunk
data: {"type":"chunk","text":"Hello! ","chunkNumber":1,"sessionId":"session-123"}

event: chunk
data: {"type":"chunk","text":"The admission","chunkNumber":2,"sessionId":"session-123"}

event: complete
data: {"type":"complete","fullResponse":"Hello! The admission requirements...","totalChunks":10}
```

## Styling

Uses Tailwind CSS with custom configuration:

**Colors**:
- Primary: Blue (600/700) for CTAs and headers
- Success: Green (600) for user messages
- Background: Gray (50/100) for surfaces
- Error: Red (50/700) for errors

**Responsive Breakpoints**:
- `md:` - Tablet and up (768px)
- `lg:` - Desktop (1024px)

## User Flow

1. **Landing Page**:
   - User sees inquiry form
   - Fills out required information
   - Submits form

2. **Form Submission**:
   - Client validates input
   - Sends POST to Form Submission Lambda
   - Creates Salesforce Lead
   - Transitions to chat on success

3. **Chat Interface**:
   - Welcome message from AI
   - User types question
   - Click "Send" to submit
   - SSE stream opens
   - Chunks appear in real-time
   - Response completes
   - User can continue conversation

4. **Return to Form**:
   - User clicks "Back to Form"
   - Session data cleared
   - New form submission starts new session

## Error Handling

### Form Errors
- Validation errors shown inline
- API errors shown in banner
- Network errors with retry suggestion

### Chat Errors
- Connection errors: "Failed to communicate with agent"
- Stream errors: Displays partial response + error
- Timeout: Shows timeout message with retry

### Graceful Degradation
- If SSE not supported, shows fallback message
- If JavaScript disabled, shows contact information

## Accessibility

- **Keyboard Navigation**: All interactive elements focusable
- **ARIA Labels**: Proper labeling for screen readers
- **Color Contrast**: WCAG AA compliant
- **Focus Indicators**: Visible focus rings

## Performance

- **Code Splitting**: Automatic with Next.js
- **Lazy Loading**: Components loaded on demand
- **Image Optimization**: Next.js Image component (if images added)
- **Bundle Size**: < 200 KB gzipped

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile Safari: iOS 14+
- Chrome Mobile: Android 10+

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### AWS Amplify

1. Connect GitHub repository
2. Set build settings:
   - Build command: `npm run build`
   - Output directory: `.next`
3. Add environment variables
4. Deploy

### Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Monitoring

### Client-Side Errors

Errors are logged to console in development. In production, integrate with:
- **Sentry**: Error tracking
- **LogRocket**: Session replay
- **Google Analytics**: User behavior

### Performance Metrics

Track:
- Form submission success rate
- Chat message latency
- SSE connection success rate
- Time to first chunk

## Testing

### Manual Testing Checklist

- [ ] Form validation works for all fields
- [ ] Form submits successfully
- [ ] Chat interface loads after submission
- [ ] Messages stream in real-time
- [ ] Error messages display correctly
- [ ] Back button returns to form
- [ ] Responsive on mobile/tablet
- [ ] Works in all supported browsers

### Future: Automated Testing

Add tests with:
- **Unit Tests**: Jest + React Testing Library
- **E2E Tests**: Playwright
- **Visual Regression**: Percy or Chromatic

## Troubleshooting

### Form won't submit
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify API endpoint is accessible
- Check browser console for errors

### Chat not streaming
- Verify `NEXT_PUBLIC_AGENT_PROXY_URL` is set
- Check if SSE is supported in browser
- Inspect Network tab for SSE connection

### Styling issues
- Run `npm run build` to regenerate Tailwind
- Clear browser cache
- Check for conflicting CSS

## Future Enhancements

1. **Conversation History**: Store past conversations
2. **File Uploads**: Attach documents to inquiries
3. **Multi-language**: Support for Spanish, Chinese, etc.
4. **Voice Input**: Speech-to-text for accessibility
5. **Typing Indicators**: Show when agent is typing
6. **Read Receipts**: Show when messages are read
7. **Offline Support**: Queue messages when offline
8. **Push Notifications**: Alert for new messages

## Support

For issues or questions:
- Check browser console for errors
- Review this README
- Check CLAUDE.md in this directory

## License

Internal use only - University Admissions System
