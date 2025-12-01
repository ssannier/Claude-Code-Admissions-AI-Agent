// Add this after the OpenSearch collection and KB role setup (around line 131)
// This creates the Bedrock Knowledge Base pointing to the manually-created index

import * as bedrock from 'aws-cdk-lib/aws-bedrock';

// Inside the stack constructor, after knowledgeBaseRole permissions:

// ==================== Bedrock Knowledge Base ====================
// PREREQUISITE: OpenSearch index "admissions-kb-index" must be created manually first
// See CREATE_INDEX_FIRST.md for instructions

const knowledgeBase = new bedrock.CfnKnowledgeBase(this, 'AdmissionsKnowledgeBase', {
  name: 'AdmissionsKnowledgeBase',
  description: 'Knowledge base for Mapua University admissions questions',
  roleArn: knowledgeBaseRole.roleArn,
  knowledgeBaseConfiguration: {
    type: 'VECTOR',
    vectorKnowledgeBaseConfiguration: {
      embeddingModelArn: `arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v1`,
    },
  },
  storageConfiguration: {
    type: 'OPENSEARCH_SERVERLESS',
    opensearchServerlessConfiguration: {
      collectionArn: kbCollection.attrArn,
      vectorIndexName: 'admissions-kb-index', // This must already exist!
      fieldMapping: {
        vectorField: 'vector',
        textField: 'text',
        metadataField: 'metadata',
      },
    },
  },
});
knowledgeBase.addDependency(kbCollection);

// Create S3 Data Source
const dataSource = new bedrock.CfnDataSource(this, 'KBDataSource', {
  name: 'AdmissionsDocuments',
  description: 'S3 bucket containing Mapua admissions documentation',
  knowledgeBaseId: knowledgeBase.attrKnowledgeBaseId,
  dataSourceConfiguration: {
    type: 'S3',
    s3Configuration: {
      bucketArn: knowledgeBaseBucket.bucketArn,
    },
  },
});
dataSource.addDependency(knowledgeBase);

// ==================== Stack Outputs ====================

new cdk.CfnOutput(this, 'KnowledgeBaseId', {
  value: knowledgeBase.attrKnowledgeBaseId,
  description: 'Bedrock Knowledge Base ID',
  exportName: 'KnowledgeBaseId',
});

new cdk.CfnOutput(this, 'DataSourceId', {
  value: dataSource.attrDataSourceId,
  description: 'Knowledge Base Data Source ID',
  exportName: 'DataSourceId',
});
