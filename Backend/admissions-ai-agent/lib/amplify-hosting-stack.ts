import * as cdk from 'aws-cdk-lib';
import * as amplify from 'aws-cdk-lib/aws-amplify';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

/**
 * AWS Amplify Hosting Stack for AI Admissions Agent Frontend
 *
 * Deploys the Next.js 15 frontend application to AWS Amplify Hosting
 * with CDN caching, environment management, and automatic deployments.
 */
export class AmplifyHostingStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // GitHub repository configuration
    const githubOwner = process.env.GITHUB_OWNER || 'your-org';
    const githubRepo = process.env.GITHUB_REPO || 'admissions-ai-agent';
    const githubBranch = process.env.GITHUB_BRANCH || 'main';
    const githubToken = cdk.SecretValue.secretsManager('github-token');

    // Create Amplify App
    const amplifyApp = new amplify.CfnApp(this, 'AdmissionsAgentApp', {
      name: 'AI Admissions Agent',
      repository: `https://github.com/${githubOwner}/${githubRepo}`,
      oauthToken: githubToken.unsafeUnwrap(),
      platform: 'WEB',

      // Build settings for Next.js 15
      buildSpec: `version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd Frontend/admissions-chat
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: .next
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
      - .next/cache/**/*`,

      // Environment variables
      environmentVariables: [
        {
          name: 'NEXT_PUBLIC_API_URL',
          value: process.env.API_GATEWAY_URL || 'https://your-api-url.amazonaws.com/prod'
        },
        {
          name: 'NEXT_PUBLIC_AGENT_PROXY_URL',
          value: process.env.AGENT_PROXY_URL || 'https://your-agent-proxy-url.lambda-url.us-east-1.on.aws'
        },
        {
          name: '_LIVE_UPDATES',
          value: '[{"pkg":"@aws-amplify/cli","type":"npm","version":"latest"}]'
        }
      ],

      // Custom rules for Next.js routing
      customRules: [
        {
          source: '/<*>',
          target: '/index.html',
          status: '404-200'
        }
      ]
    });

    // Create main branch
    const mainBranch = new amplify.CfnBranch(this, 'MainBranch', {
      appId: amplifyApp.attrAppId,
      branchName: githubBranch,
      enableAutoBuild: true,
      enablePerformanceMode: true,
      framework: 'Next.js - SSR',
      stage: 'PRODUCTION'
    });

    // Create IAM role for Amplify
    const amplifyRole = new iam.Role(this, 'AmplifyRole', {
      assumedBy: new iam.ServicePrincipal('amplify.amazonaws.com'),
      description: 'Service role for AWS Amplify'
    });

    amplifyRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('AdministratorAccess-Amplify')
    );

    // Outputs
    new cdk.CfnOutput(this, 'AmplifyAppId', {
      value: amplifyApp.attrAppId,
      description: 'Amplify App ID',
      exportName: 'AdmissionsAgentAmplifyAppId'
    });

    new cdk.CfnOutput(this, 'AmplifyAppUrl', {
      value: `https://${githubBranch}.${amplifyApp.attrDefaultDomain}`,
      description: 'Amplify App URL',
      exportName: 'AdmissionsAgentAmplifyUrl'
    });

    new cdk.CfnOutput(this, 'AmplifyConsoleUrl', {
      value: `https://console.aws.amazon.com/amplify/home?region=${this.region}#/${amplifyApp.attrAppId}`,
      description: 'Amplify Console URL'
    });
  }
}
