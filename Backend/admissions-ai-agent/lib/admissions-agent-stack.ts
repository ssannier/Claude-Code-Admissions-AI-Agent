import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as logs from 'aws-cdk-lib/aws-logs';
import { SqsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import { Construct } from 'constructs';
import * as path from 'path';

export class AdmissionsAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ==================== S3 Bucket for Knowledge Base ====================
    const knowledgeBaseBucket = new s3.Bucket(this, 'KnowledgeBaseBucket', {
      bucketName: `admissions-agent-kb-${this.account}-${this.region}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.RETAIN, // Retain bucket on stack deletion to preserve knowledge base documents
      autoDeleteObjects: false, // Don't auto-delete objects to prevent accidental data loss
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [
        {
          noncurrentVersionExpiration: cdk.Duration.days(30),
        },
      ],
    });

    // ==================== Bedrock Knowledge Base ====================
    // NOTE: Knowledge Base will be created via Bedrock Console
    // This approach avoids complex permission issues between CDK, Bedrock, and OpenSearch
    // See KNOWLEDGE_BASE_INSTRUCTIONS.md for step-by-step Console creation guide
    //
    // Configuration to use:
    // - Name: AdmissionsKnowledgeBase
    // - S3 Bucket: admissions-agent-kb-756493389182-us-west-2
    // - OpenSearch Collection: admissions-kb-collection (to be created)
    // - Index: admissions-kb-index
    // - Embeddings: Titan Embeddings G1 - Text

    // ==================== DynamoDB Tables ====================

    // WhatsappSessions table for session tracking
    const sessionsTable = new dynamodb.Table(this, 'WhatsappSessionsTable', {
      tableName: 'WhatsappSessions',
      partitionKey: {
        name: 'phone_number',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Can recreate - data is ephemeral during development
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
    });

    // WhatsAppMessageTracking table for delivery status
    const messageTrackingTable = new dynamodb.Table(this, 'MessageTrackingTable', {
      tableName: 'WhatsAppMessageTracking',
      partitionKey: {
        name: 'eum_msg_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Can recreate - data is ephemeral during development
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
    });

    // ==================== SQS Queue for WhatsApp Messages ====================

    // Dead-letter queue for failed messages
    const whatsappDLQ = new sqs.Queue(this, 'WhatsAppDLQ', {
      queueName: 'twilio-whatsapp-dlq',
      retentionPeriod: cdk.Duration.days(14),
    });

    // Main WhatsApp queue
    const whatsappQueue = new sqs.Queue(this, 'WhatsAppQueue', {
      queueName: 'twilio-whatsapp-queue',
      visibilityTimeout: cdk.Duration.seconds(300),
      retentionPeriod: cdk.Duration.days(14),
      deadLetterQueue: {
        queue: whatsappDLQ,
        maxReceiveCount: 3,
      },
    });

    // ==================== Lambda Layers ====================

    // Salesforce layer
    const salesforceLayer = new lambda.LayerVersion(this, 'SalesforceLayer', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../layers/salesforce')),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      description: 'Salesforce integration libraries (simple-salesforce, requests)',
    });

    // Twilio layer
    const twilioLayer = new lambda.LayerVersion(this, 'TwilioLayer', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../layers/twilio')),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      description: 'Twilio WhatsApp integration libraries',
    });

    // ==================== IAM Role for AgentCore ====================

    const agentExecutionRole = new iam.Role(this, 'AgentExecutionRole', {
      roleName: 'AdmissionsAgentExecutionRole',
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      description: 'Execution role for Bedrock AgentCore with access to required AWS services',
    });

    // Grant Bedrock permissions
    agentExecutionRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
        'bedrock:Retrieve',
        'bedrock:GetMemoryEvents',
        'bedrock:PutMemoryEvents',
        'bedrock:DeleteMemoryEvents',
      ],
      resources: ['*'],
    }));

    // Grant S3 read access to knowledge base bucket
    knowledgeBaseBucket.grantRead(agentExecutionRole);

    // Grant DynamoDB access
    sessionsTable.grantReadWriteData(agentExecutionRole);
    messageTrackingTable.grantReadWriteData(agentExecutionRole);

    // Grant SQS send message permission
    whatsappQueue.grantSendMessages(agentExecutionRole);

    // ==================== ECR Repository for AgentCore ====================

    const agentEcrRepo = new ecr.Repository(this, 'AgentEcrRepo', {
      repositoryName: 'admissions-agent',
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Can recreate - images can be rebuilt
      emptyOnDelete: true, // Automatically delete images on stack deletion
      lifecycleRules: [{
        maxImageCount: 5,
        description: 'Keep last 5 images',
      }],
    });

    // ==================== Lambda Functions ====================

    // Form Submission Lambda
    const formSubmissionLogGroup = new logs.LogGroup(this, 'FormSubmissionLogGroup', {
      logGroupName: '/aws/lambda/admissions-form-submission',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const formSubmissionLambda = new lambda.Function(this, 'FormSubmissionLambda', {
      functionName: 'admissions-form-submission',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'form_submission.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/form-submission')),
      timeout: cdk.Duration.seconds(15),
      memorySize: 256,
      layers: [salesforceLayer],
      environment: {
        SALESFORCE_SECRET_NAME: 'admissions-agent/salesforce',
        LOG_LEVEL: 'INFO',
      },
      logGroup: formSubmissionLogGroup,
    });

    // Grant Secrets Manager read permissions
    formSubmissionLambda.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['secretsmanager:GetSecretValue'],
      resources: [`arn:aws:secretsmanager:${this.region}:${this.account}:secret:admissions-agent/salesforce-*`],
    }));

    // WhatsApp Sender Lambda
    const whatsappSenderLogGroup = new logs.LogGroup(this, 'WhatsAppSenderLogGroup', {
      logGroupName: '/aws/lambda/admissions-whatsapp-sender',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const whatsappSenderLambda = new lambda.Function(this, 'WhatsAppSenderLambda', {
      functionName: 'admissions-whatsapp-sender',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'send_whatsapp_twilio.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/whatsapp-sender')),
      timeout: cdk.Duration.seconds(15),
      memorySize: 256,
      layers: [twilioLayer],
      environment: {
        TWILIO_SECRET_NAME: 'admissions-agent/twilio',
        MESSAGE_TRACKING_TABLE: messageTrackingTable.tableName,
        AWS_REGION: this.region,
        LOG_LEVEL: 'INFO',
      },
      logGroup: whatsappSenderLogGroup,
    });

    // Grant DynamoDB write access to WhatsApp Lambda
    messageTrackingTable.grantWriteData(whatsappSenderLambda);

    // Grant Secrets Manager read permissions
    whatsappSenderLambda.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['secretsmanager:GetSecretValue'],
      resources: [`arn:aws:secretsmanager:${this.region}:${this.account}:secret:admissions-agent/twilio-*`],
    }));

    // Add SQS as event source for WhatsApp Lambda
    whatsappSenderLambda.addEventSource(new SqsEventSource(whatsappQueue, {
      batchSize: 10,
      maxBatchingWindow: cdk.Duration.seconds(5),
    }));

    // Agent Proxy Lambda (placeholder - will be implemented)
    const agentProxyLogGroup = new logs.LogGroup(this, 'AgentProxyLogGroup', {
      logGroupName: '/aws/lambda/admissions-agent-proxy',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const agentProxyLambda = new lambda.Function(this, 'AgentProxyLambda', {
      functionName: 'admissions-agent-proxy',
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/agent-proxy')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        AGENT_RUNTIME_ARN: process.env.AGENT_RUNTIME_ARN || 'placeholder',
        LOG_LEVEL: 'INFO',
      },
      logGroup: agentProxyLogGroup,
    });

    // Grant agent proxy permission to invoke Bedrock AgentCore
    agentProxyLambda.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeAgent',
        'bedrock:InvokeAgentWithResponseStream',
      ],
      resources: ['*'],
    }));

    // Create Function URL for Agent Proxy (for SSE streaming)
    const agentProxyUrl = agentProxyLambda.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      cors: {
        allowedOrigins: ['*'], // TODO: Restrict to frontend domain in production
        allowedMethods: [lambda.HttpMethod.POST],
        allowedHeaders: ['Content-Type'],
        maxAge: cdk.Duration.hours(1),
      },
    });

    // ==================== API Gateway ====================

    const api = new apigateway.RestApi(this, 'AdmissionsApi', {
      restApiName: 'Admissions Form API',
      description: 'API for submitting inquiry forms',
      deployOptions: {
        stageName: 'prod',
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS, // TODO: Restrict in production
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization'],
      },
    });

    // Add /submit endpoint
    const submitResource = api.root.addResource('submit');
    const formSubmissionIntegration = new apigateway.LambdaIntegration(formSubmissionLambda);
    submitResource.addMethod('POST', formSubmissionIntegration);

    // ==================== Stack Outputs ====================

    new cdk.CfnOutput(this, 'KnowledgeBaseBucketName', {
      value: knowledgeBaseBucket.bucketName,
      description: 'S3 bucket for knowledge base documents',
      exportName: 'KnowledgeBaseBucketName',
    });

    new cdk.CfnOutput(this, 'SessionsTableName', {
      value: sessionsTable.tableName,
      description: 'DynamoDB table for session tracking',
      exportName: 'SessionsTableName',
    });

    new cdk.CfnOutput(this, 'MessageTrackingTableName', {
      value: messageTrackingTable.tableName,
      description: 'DynamoDB table for message tracking',
      exportName: 'MessageTrackingTableName',
    });

    new cdk.CfnOutput(this, 'WhatsAppQueueUrl', {
      value: whatsappQueue.queueUrl,
      description: 'SQS queue URL for WhatsApp messages',
      exportName: 'WhatsAppQueueUrl',
    });

    new cdk.CfnOutput(this, 'AgentExecutionRoleArn', {
      value: agentExecutionRole.roleArn,
      description: 'IAM role ARN for AgentCore execution',
      exportName: 'AgentExecutionRoleArn',
    });

    new cdk.CfnOutput(this, 'AgentEcrRepositoryUri', {
      value: agentEcrRepo.repositoryUri,
      description: 'ECR repository URI for AgentCore images',
      exportName: 'AgentEcrRepositoryUri',
    });

    new cdk.CfnOutput(this, 'AgentProxyFunctionUrl', {
      value: agentProxyUrl.url,
      description: 'Agent Proxy Lambda Function URL for SSE streaming',
      exportName: 'AgentProxyFunctionUrl',
    });

    new cdk.CfnOutput(this, 'FormSubmissionApiUrl', {
      value: api.url + 'submit',
      description: 'API Gateway URL for form submission',
      exportName: 'FormSubmissionApiUrl',
    });

    // NOTE: Knowledge Base ID, Data Source ID, and Role will be available after
    // creating the Knowledge Base via Bedrock Console. Update QUICK_REFERENCE.md
    // with these values after creation.
  }
}
