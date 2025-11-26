# TODO List - AI Admissions Agent

**Last Updated**: November 25, 2024

---

## 🔴 High Priority (Before Production)

### Security & Secrets Management

- [ ] **Set Up AWS Secrets Manager**
  - [ ] Create secret for Salesforce credentials (`admissions-agent/salesforce`)
  - [ ] Create secret for Twilio credentials (`admissions-agent/twilio`)
  - [ ] Create secret for GitHub token (`github-token`)
  - [ ] Update Lambda functions to read from Secrets Manager instead of environment variables
  - [ ] Document secret rotation procedure
  - **Location**: See [SECURITY.md](SECURITY.md) for commands
  - **Priority**: CRITICAL before production deployment

- [ ] **Configure Environment Variables**
  - [ ] Create `.env` from `.env.example` for local development (root)
  - [ ] Create `.env.local` from `.env.example` (Frontend)
  - [ ] Create `.env` from `.env.example` (AgentCore)
  - [ ] Add all actual credentials (NEVER commit these files!)
  - [ ] Test that all services can read environment variables correctly

- [ ] **Set Up Bedrock Memory**
  - [ ] Create Bedrock Memory ID in AWS Console
  - [ ] Add Memory ID to `.env` and Lambda environment variables
  - [ ] Test conversation history persistence
  - [ ] Verify actor ID sanitization works correctly

- [ ] **Create Bedrock Knowledge Base**
  - [ ] Create S3 bucket for knowledge documents
  - [ ] Upload university admissions documentation
  - [ ] Create Bedrock Knowledge Base
  - [ ] Configure vector embeddings
  - [ ] Add Knowledge Base ID to environment variables
  - [ ] Test retrieval with sample queries

### Testing

- [ ] **Run All Unit Tests**
  - [ ] Form Submission Lambda tests (fix 2 remaining failures)
  - [ ] WhatsApp Sender Lambda tests (fix 1 remaining failure)
  - [ ] Agent Proxy Lambda tests (all passing ✅)
  - [ ] Document any acceptable failures

- [ ] **Local Testing with Mock Servers**
  - [ ] Run `./start-local-testing.sh`
  - [ ] Test form submission
  - [ ] Test chat interface
  - [ ] Test all mock response types
  - [ ] Test regenerate button
  - [ ] Test tool status indicators
  - [ ] Test error handling

---

## 🟡 Medium Priority (Before First Deployment)

### Dependency Updates

- [ ] **Update Deprecated Dependencies**
  - [ ] Update ESLint to v9 (currently v8.57.1)
    ```bash
    cd Frontend/admissions-chat
    npm install eslint@latest --save-dev
    ```
  - [ ] Update glob to v9+ (currently v7.2.3)
  - [ ] Update rimraf to v4+ (currently v3.0.2)
  - [ ] Test that everything still works after updates
  - **Note**: Low priority, won't affect functionality

- [ ] **Review and Update Package Versions**
  - [ ] Run `npm outdated` in all directories
  - [ ] Update packages with security vulnerabilities
  - [ ] Test thoroughly after updates

### AWS Infrastructure

- [ ] **Deploy CDK Stacks**
  - [ ] Bootstrap CDK in target AWS account
    ```bash
    cd Backend/admissions-ai-agent
    cdk bootstrap
    ```
  - [ ] Deploy main stack (`AdmissionsAgentStack`)
  - [ ] Deploy Amplify stack (`AmplifyHostingStack`)
  - [ ] Save all stack outputs (API URLs, Lambda ARNs, etc.)
  - [ ] Update environment variables with actual URLs

- [ ] **Upload Lambda Layers**
  - [ ] Build Salesforce layer (already built ✅)
  - [ ] Build Twilio layer (already built ✅)
  - [ ] Upload both layers to AWS
  - [ ] Attach layers to Lambda functions
  - [ ] Verify layers work in Lambda console

- [ ] **Configure Lambda Functions**
  - [ ] Set environment variables for all 3 Lambda functions
  - [ ] Attach Lambda layers
  - [ ] Configure VPC settings (if needed)
  - [ ] Set appropriate memory and timeout values
  - [ ] Test each Lambda function individually

### AgentCore Deployment

- [ ] **Configure Agent with Strands CLI**
  - [ ] Install Strands SDK: `pip install strands-sdk`
  - [ ] Run `agentcore configure` in AgentCore directory
  - [ ] Provide execution role ARN (from CDK outputs)
  - [ ] Provide ECR repository URI (from CDK outputs)
  - [ ] Provide Bedrock Memory ID
  - [ ] Verify `.agentcore/config.json` created

- [ ] **Deploy Nemo Agent**
  - [ ] Run `./scripts/launch_agent.sh`
  - [ ] Save Agent ID and Agent ARN
  - [ ] Create Agent Alias in Bedrock console
  - [ ] Test agent with `agentcore test`
  - [ ] Update Agent Proxy Lambda with Agent ID and Alias ID

### Integration Testing

- [ ] **Test Form → Salesforce**
  - [ ] Submit test form
  - [ ] Verify Lead created in Salesforce
  - [ ] Check all fields mapped correctly
  - [ ] Verify timing preference stored

- [ ] **Test Chat → Knowledge Base**
  - [ ] Ask about admission requirements
  - [ ] Verify retrieval from Knowledge Base
  - [ ] Check relevance scores (≥ 0.5)
  - [ ] Verify source attribution displayed

- [ ] **Test Advisor Handoff Workflow**
  - [ ] Request advisor handoff
  - [ ] Verify Lead status changes to "Working - Connected"
  - [ ] Check Task created with title "AI Chat Summary - Advisor Handoff"
  - [ ] Verify Task includes conversation transcript
  - [ ] Confirm WhatsApp message sent
  - [ ] Test with different timing preferences

---

## 🟢 Low Priority (Nice to Have)

### Documentation

- [ ] **Update README files with actual deployment URLs**
  - [ ] Root README
  - [ ] Backend README
  - [ ] Frontend README
  - [ ] AgentCore README

- [ ] **Create Deployment Runbook**
  - [ ] Step-by-step deployment checklist
  - [ ] Rollback procedures
  - [ ] Troubleshooting common issues
  - [ ] Contact information

- [ ] **Add Architecture Diagrams**
  - [ ] Update with actual AWS resource names
  - [ ] Include security boundaries
  - [ ] Document data flows

### Testing Improvements

- [ ] **Property-Based Testing**
  - [ ] Install Hypothesis (Python) and fast-check (TypeScript)
  - [ ] Write property tests for all 44 properties
  - [ ] Integrate into CI/CD pipeline
  - **Reference**: See [design.md](docs/kiro docs/design.md) for properties

- [ ] **End-to-End Testing Automation**
  - [ ] Set up Playwright or Cypress
  - [ ] Automate full user flow
  - [ ] Test on multiple browsers
  - [ ] Add to CI/CD pipeline

- [ ] **Load Testing**
  - [ ] Set up Artillery or k6
  - [ ] Test with 100 concurrent users
  - [ ] Identify bottlenecks
  - [ ] Optimize based on results

### Monitoring & Observability

- [ ] **Set Up CloudWatch Dashboards**
  - [ ] Lambda invocation metrics
  - [ ] API Gateway metrics
  - [ ] Bedrock AgentCore metrics
  - [ ] SQS queue depth
  - [ ] Error rates and latency

- [ ] **Configure CloudWatch Alarms**
  - [ ] Lambda errors > threshold
  - [ ] API Gateway 5xx errors
  - [ ] SQS DLQ messages
  - [ ] Agent invocation failures
  - [ ] Set up SNS notifications

- [ ] **Enable X-Ray Tracing**
  - [ ] Enable for all Lambda functions
  - [ ] Enable for API Gateway
  - [ ] Create service map
  - [ ] Analyze trace data

### Security Enhancements

- [ ] **Install git-secrets**
  ```bash
  brew install git-secrets  # macOS
  git secrets --install
  git secrets --register-aws
  ```

- [ ] **Set Up Pre-commit Hooks**
  - [ ] Copy pre-commit hook from [PRE_COMMIT_CHECKLIST.md](PRE_COMMIT_CHECKLIST.md)
  - [ ] Make executable: `chmod +x .git/hooks/pre-commit`
  - [ ] Test with dummy secret

- [ ] **Enable AWS Config**
  - [ ] Record all resource changes
  - [ ] Set up compliance rules
  - [ ] Configure S3 bucket for logs

- [ ] **Enable AWS GuardDuty**
  - [ ] Turn on threat detection
  - [ ] Configure findings notifications
  - [ ] Review findings weekly

- [ ] **IAM Audit**
  - [ ] Review all IAM roles
  - [ ] Apply least-privilege principle
  - [ ] Remove unused permissions
  - [ ] Enable MFA for all users

### Feature Enhancements

- [ ] **Multi-language Support**
  - [ ] Integrate AWS Translate
  - [ ] Add language detection
  - [ ] Support 70+ languages
  - [ ] Test with non-English queries

- [ ] **Voice Input**
  - [ ] Add speech-to-text
  - [ ] Support in frontend
  - [ ] Test accessibility

- [ ] **Conversation History UI**
  - [ ] Add "View History" button
  - [ ] Display past conversations
  - [ ] Allow searching history
  - [ ] Export transcript feature

- [ ] **Analytics Dashboard**
  - [ ] Track user engagement
  - [ ] Monitor conversion rates
  - [ ] Identify common questions
  - [ ] Generate reports

### Performance Optimization

- [ ] **Lambda Performance**
  - [ ] Analyze cold start times
  - [ ] Implement Lambda warming
  - [ ] Optimize package sizes
  - [ ] Consider provisioned concurrency

- [ ] **Frontend Optimization**
  - [ ] Analyze bundle size
  - [ ] Implement code splitting
  - [ ] Add service worker for offline support
  - [ ] Optimize images and assets

- [ ] **Database Optimization**
  - [ ] Review DynamoDB indexes
  - [ ] Optimize query patterns
  - [ ] Consider caching layer (ElastiCache)
  - [ ] Monitor read/write capacity

---

## 📋 Completed Items

### ✅ Implementation (Nov 25, 2024)
- [x] Complete backend infrastructure with CDK
- [x] Implement all 3 Lambda functions with tests
- [x] Create AgentCore with proper Strands SDK integration
- [x] Implement all 5 custom tools
- [x] Build frontend with Next.js 15
- [x] Implement SSE streaming
- [x] Add regenerate functionality
- [x] Add tool status indicators
- [x] Fix all critical architecture compliance issues
- [x] Create deployment scripts
- [x] Create testing infrastructure (mock servers)
- [x] Write comprehensive documentation

### ✅ Critical Fixes (Nov 25, 2024)
- [x] Rename tool to `retrieve_university_info`
- [x] Fix Salesforce Lead status to "Working - Connected"
- [x] Fix Task title to "AI Chat Summary - Advisor Handoff"
- [x] Set explicit agent name to "Nemo"
- [x] Create Amplify hosting stack
- [x] Create deployment scripts

### ✅ Documentation (Nov 25, 2024)
- [x] QUICKSTART.md
- [x] TESTING_GUIDE.md
- [x] PROJECT_STATUS.md
- [x] IMPLEMENTATION_AUDIT_REPORT.md
- [x] ARCHITECTURE_COMPLIANCE_AUDIT.md
- [x] SECURITY.md
- [x] PRE_COMMIT_CHECKLIST.md
- [x] .gitignore and .env.example files

---

## 🎯 Current Focus

**Immediate Next Steps** (This Week):

1. ✅ Set up local `.env` files with your credentials
2. ✅ Test locally with mock servers (`./start-local-testing.sh`)
3. ✅ Run all unit tests
4. ⏳ Create Bedrock Memory ID
5. ⏳ Create Bedrock Knowledge Base
6. ⏳ Deploy CDK stacks to AWS
7. ⏳ Deploy Nemo agent to Bedrock AgentCore

---

## 📊 Progress Tracking

| Category | Items | Completed | Remaining | Progress |
|----------|-------|-----------|-----------|----------|
| **High Priority** | 15 | 0 | 15 | ░░░░░░░░░░ 0% |
| **Medium Priority** | 18 | 0 | 18 | ░░░░░░░░░░ 0% |
| **Low Priority** | 35 | 0 | 35 | ░░░░░░░░░░ 0% |
| **Implementation** | 44 | 44 | 0 | ██████████ 100% ✅ |
| **TOTAL** | 112 | 44 | 68 | ████░░░░░░ 39% |

---

## 🔄 Update History

- **Nov 25, 2024**: Initial TODO list created
  - All implementation items completed
  - All critical fixes completed
  - 68 items remaining across 3 priority levels

---

## 📝 Notes

- **Before Production**: Must complete all High Priority items
- **For MVP**: Complete High + most Medium Priority items
- **Ongoing**: Low Priority items can be tackled incrementally

- **Estimated Time**:
  - High Priority: 2-3 days
  - Medium Priority: 1-2 weeks
  - Low Priority: 1-3 months

---

## 🆘 If You Need Help

1. Check the relevant documentation:
   - [QUICKSTART.md](QUICKSTART.md) - Getting started
   - [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing procedures
   - [SECURITY.md](SECURITY.md) - Security guidelines

2. Review AWS documentation:
   - [Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/)
   - [CDK Documentation](https://docs.aws.amazon.com/cdk/)

3. Common issues documented in:
   - [TESTING_GUIDE.md - Troubleshooting](TESTING_GUIDE.md#troubleshooting)

---

**Keep this file updated as you complete items! Check off completed tasks and add new ones as needed.**
