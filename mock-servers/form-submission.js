/**
 * Mock Form Submission API Server
 *
 * Simulates the Form Submission Lambda for local frontend testing.
 * Run: node mock-servers/form-submission.js
 */

const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 3001;

// Enable CORS for local development
app.use(cors());
app.use(express.json());

// Request logging middleware
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// Mock form submission endpoint
app.post('/submit', (req, res) => {
  console.log('📝 Form submission received:', req.body);

  const {
    firstName,
    lastName,
    email,
    cellPhone,
    headquarters,
    programType,
    timingPreference
  } = req.body;

  // Validation
  if (!firstName || !lastName || !email || !cellPhone || !headquarters || !programType) {
    console.log('❌ Validation failed - missing required fields');
    return res.status(400).json({
      success: false,
      message: 'Missing required fields'
    });
  }

  // Email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    console.log('❌ Validation failed - invalid email');
    return res.status(400).json({
      success: false,
      message: 'Invalid email address'
    });
  }

  // Simulate processing delay
  setTimeout(() => {
    const mockLeadId = 'MOCK-' + Date.now().toString(36).toUpperCase();

    console.log('✅ Form submission successful');
    console.log('   Lead ID:', mockLeadId);
    console.log('   Student:', `${firstName} ${lastName}`);
    console.log('   Email:', email);
    console.log('   Phone:', cellPhone);
    console.log('   Campus:', headquarters);
    console.log('   Program:', programType);
    console.log('   Timing:', timingPreference);

    res.json({
      success: true,
      message: 'Form submitted successfully',
      leadId: mockLeadId,
      data: {
        studentName: `${firstName} ${lastName}`,
        email,
        phone: cellPhone
      }
    });
  }, 1000);
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'Mock Form Submission API',
    timestamp: new Date().toISOString()
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('❌ Server error:', err);
  res.status(500).json({
    success: false,
    message: 'Internal server error'
  });
});

// Start server
app.listen(PORT, () => {
  console.log('🚀 Mock Form Submission API running');
  console.log(`   URL: http://localhost:${PORT}`);
  console.log(`   Endpoint: POST /submit`);
  console.log(`   Health: GET /health`);
  console.log('');
  console.log('📋 Test with curl:');
  console.log(`   curl -X POST http://localhost:${PORT}/submit \\`);
  console.log(`     -H "Content-Type: application/json" \\`);
  console.log(`     -d '{"firstName":"Test","lastName":"User","email":"test@example.com","cellPhone":"+15551234567","headquarters":"Manila","programType":"Undergraduate","timingPreference":"2 hours"}'`);
  console.log('');
  console.log('Press Ctrl+C to stop');
  console.log('---');
});
