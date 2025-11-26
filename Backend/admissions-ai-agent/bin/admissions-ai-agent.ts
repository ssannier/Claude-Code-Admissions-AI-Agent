#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { AdmissionsAgentStack } from '../lib/admissions-agent-stack';

const app = new cdk.App();

new AdmissionsAgentStack(app, 'AdmissionsAgentStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'AI-powered university admissions agent infrastructure',
  tags: {
    Project: 'AdmissionsAgent',
    Environment: 'Development',
  },
});

app.synth();
