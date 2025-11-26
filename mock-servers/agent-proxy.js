/**
 * Mock Agent Proxy Server with SSE Streaming
 *
 * Simulates the Agent Proxy Lambda for local frontend testing.
 * Includes mock responses with tool usage indicators and streaming text.
 * Run: node mock-servers/agent-proxy.js
 */

const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 3002;

// Enable CORS for local development
app.use(cors());
app.use(express.json());

// Request logging middleware
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// Mock responses database
const mockResponses = {
  'admission': 'Based on our admissions documentation, undergraduate applicants need a high school diploma with a minimum GPA of 3.0. You must also submit SAT or ACT scores, two letters of recommendation, and a personal statement.',
  'requirements': 'The admission requirements vary by program. For undergraduate programs, you need a high school diploma with at least a 3.0 GPA. Graduate programs require a bachelor\'s degree with a 3.5 GPA. All programs require English proficiency test scores (TOEFL or IELTS).',
  'deadline': 'Application deadlines for Fall 2025 admission are: Early Decision - November 15, Regular Decision - January 15, and Late Applications accepted until March 1 on a rolling basis.',
  'financial': 'We offer various financial aid options including merit scholarships, need-based grants, and student loans. International students may qualify for merit scholarships ranging from $5,000 to full tuition coverage.',
  'campus': 'We have four campuses: Manila (main campus), Makati (business programs), Cebu (engineering and technology), and Davao (agriculture and sciences). Each campus offers unique programs and facilities.',
  'default': 'Thank you for your question. Let me search our knowledge base for that information. Based on university policies, I recommend speaking with an admissions advisor who can provide detailed information specific to your situation.'
};

// Get mock response based on keywords
function getMockResponse(prompt) {
  const lowerPrompt = prompt.toLowerCase();

  if (lowerPrompt.includes('admission') || lowerPrompt.includes('require')) {
    return { response: mockResponses.admission, tool: 'retrieve_university_info' };
  } else if (lowerPrompt.includes('deadline') || lowerPrompt.includes('when')) {
    return { response: mockResponses.deadline, tool: 'retrieve_university_info' };
  } else if (lowerPrompt.includes('financial') || lowerPrompt.includes('scholarship') || lowerPrompt.includes('aid')) {
    return { response: mockResponses.financial, tool: 'retrieve_university_info' };
  } else if (lowerPrompt.includes('campus') || lowerPrompt.includes('location')) {
    return { response: mockResponses.campus, tool: 'retrieve_university_info' };
  } else if (lowerPrompt.includes('status') || lowerPrompt.includes('application')) {
    return { response: 'Let me check your application status in our system...', tool: 'query_salesforce_leads' };
  } else if (lowerPrompt.includes('advisor') || lowerPrompt.includes('human') || lowerPrompt.includes('speak')) {
    return { response: 'I\'ll connect you with a human advisor right away. They will reach out to you based on your preferred timing.', tool: 'complete_advisor_handoff' };
  }

  return { response: mockResponses.default, tool: 'retrieve_university_info' };
}

// SSE formatting helper
function formatSSE(data, event = 'message') {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

// Mock Agent Proxy endpoint with SSE streaming
app.post('/', (req, res) => {
  console.log('🤖 Agent request received:', req.body);

  const { prompt, session_id, phone_number, student_name } = req.body;

  if (!prompt) {
    res.status(400).json({ error: 'Missing prompt field' });
    return;
  }

  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');

  console.log('   Session:', session_id || 'none');
  console.log('   Phone:', phone_number || 'none');
  console.log('   Student:', student_name || 'none');
  console.log('   Prompt:', prompt);

  // Get mock response
  const { response, tool } = getMockResponse(prompt);

  let step = 0;

  // Step 1: Show tool thinking indicator (500ms delay)
  setTimeout(() => {
    step++;
    const thinkingMsg = `Using ${tool}...`;
    console.log(`   [${step}] 🔧 ${thinkingMsg}`);
    res.write(formatSSE({ thinking: thinkingMsg }));
  }, 500);

  // Step 2: Tool result received (1.5s delay)
  setTimeout(() => {
    step++;
    console.log(`   [${step}] 📊 Tool result received`);
    res.write(formatSSE({ tool_result: 'Retrieved information from knowledge base' }));
  }, 1500);

  // Step 3: Stream response word by word (starting at 2s)
  const words = response.split(' ');
  let accumulatedText = '';

  words.forEach((word, i) => {
    setTimeout(() => {
      step++;
      accumulatedText += word + ' ';
      console.log(`   [${step}] 💬 Chunk: "${word}"`);
      res.write(formatSSE({ response: word + ' ' }));
    }, 2000 + (i * 100));
  });

  // Step 4: Send final result (after all words)
  setTimeout(() => {
    step++;
    console.log(`   [${step}] ✅ Complete`);
    res.write(formatSSE({ final_result: response }));
    res.end();
    console.log('---');
  }, 2000 + (words.length * 100) + 300);
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'Mock Agent Proxy',
    timestamp: new Date().toISOString()
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('❌ Server error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
app.listen(PORT, () => {
  console.log('🚀 Mock Agent Proxy running');
  console.log(`   URL: http://localhost:${PORT}`);
  console.log(`   Endpoint: POST /`);
  console.log(`   Health: GET /health`);
  console.log('');
  console.log('📋 Supported keywords:');
  console.log('   - "admission" or "requirements" → Admission info');
  console.log('   - "deadline" or "when" → Application deadlines');
  console.log('   - "financial" or "scholarship" → Financial aid');
  console.log('   - "campus" or "location" → Campus information');
  console.log('   - "status" or "application" → Salesforce query');
  console.log('   - "advisor" or "human" → Advisor handoff');
  console.log('');
  console.log('📋 Test with curl:');
  console.log(`   curl -X POST http://localhost:${PORT}/ \\`);
  console.log(`     -H "Content-Type: application/json" \\`);
  console.log(`     -d '{"prompt":"What are the admission requirements?","session_id":"test-123"}'`);
  console.log('');
  console.log('Press Ctrl+C to stop');
  console.log('---');
});
