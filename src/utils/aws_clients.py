"""
AWS client utilities for the Cosmos Gov-Watcher system.
Provides singleton clients for DynamoDB, S3, SES, and Secrets Manager.
"""

import os
import boto3
from typing import Optional, Dict, Any
import json
from botocore.exceptions import ClientError
import structlog

logger = structlog.get_logger(__name__)


class AWSClients:
    """Singleton class for AWS service clients."""
    
    _instance = None
    _clients = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_dynamodb_client(self):
        """Get DynamoDB client."""
        if 'dynamodb' not in self._clients:
            self._clients['dynamodb'] = boto3.client('dynamodb')
        return self._clients['dynamodb']
    
    def get_dynamodb_resource(self):
        """Get DynamoDB resource for higher-level operations."""
        if 'dynamodb_resource' not in self._clients:
            self._clients['dynamodb_resource'] = boto3.resource('dynamodb')
        return self._clients['dynamodb_resource']
    
    def get_s3_client(self):
        """Get S3 client."""
        if 's3' not in self._clients:
            self._clients['s3'] = boto3.client('s3')
        return self._clients['s3']
    
    def get_ses_client(self):
        """Get SES client."""
        if 'ses' not in self._clients:
            self._clients['ses'] = boto3.client('ses')
        return self._clients['ses']
    
    def get_secrets_client(self):
        """Get Secrets Manager client."""
        if 'secrets' not in self._clients:
            self._clients['secrets'] = boto3.client('secretsmanager')
        return self._clients['secrets']


class DynamoDBHelper:
    """Helper class for DynamoDB operations."""
    
    def __init__(self):
        self.clients = AWSClients()
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'GovSubscriptions')
    
    def get_table(self):
        """Get DynamoDB table resource."""
        dynamodb = self.clients.get_dynamodb_resource()
        return dynamodb.Table(self.table_name)
    
    def put_subscription(self, subscription_data: Dict[str, Any]) -> bool:
        """Store subscription record in DynamoDB."""
        try:
            table = self.get_table()
            table.put_item(Item=subscription_data)
            logger.info("Subscription stored successfully", wallet=subscription_data.get('wallet'))
            return True
        except ClientError as e:
            logger.error("Failed to store subscription", error=str(e), wallet=subscription_data.get('wallet'))
            return False
    
    def get_subscription(self, wallet: str) -> Optional[Dict[str, Any]]:
        """Retrieve subscription by wallet address."""
        try:
            table = self.get_table()
            response = table.get_item(Key={'wallet': wallet})
            return response.get('Item')
        except ClientError as e:
            logger.error("Failed to retrieve subscription", error=str(e), wallet=wallet)
            return None
    
    def get_active_subscriptions_for_chain(self, chain: str, current_time: int) -> list:
        """Get all active subscriptions for a specific chain."""
        try:
            table = self.get_table()
            # Use scan for now - in production, consider GSI for chain-based queries
            response = table.scan(
                FilterExpression="contains(chains, :chain) AND expires > :current_time",
                ExpressionAttributeValues={
                    ':chain': chain,
                    ':current_time': current_time
                }
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error("Failed to retrieve active subscriptions", error=str(e), chain=chain)
            return []
    
    def update_last_notified(self, wallet: str, chain: str, proposal_id: int) -> bool:
        """Update the last notified proposal ID for a user and chain."""
        try:
            table = self.get_table()
            table.update_item(
                Key={'wallet': wallet},
                UpdateExpression="SET last_notified.#chain = :proposal_id",
                ExpressionAttributeNames={'#chain': chain},
                ExpressionAttributeValues={':proposal_id': proposal_id}
            )
            logger.info("Last notified updated", wallet=wallet, chain=chain, proposal_id=proposal_id)
            return True
        except ClientError as e:
            logger.error("Failed to update last notified", error=str(e), wallet=wallet)
            return False


class S3Helper:
    """Helper class for S3 logging operations."""
    
    def __init__(self):
        self.clients = AWSClients()
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'govwatcher-logs')
    
    def put_log(self, log_entry: Dict[str, Any], s3_key: str) -> bool:
        """Store log entry in S3."""
        try:
            s3 = self.clients.get_s3_client()
            s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(log_entry, indent=2),
                ContentType='application/json'
            )
            logger.debug("Log entry stored in S3", s3_key=s3_key)
            return True
        except ClientError as e:
            logger.error("Failed to store log in S3", error=str(e), s3_key=s3_key)
            return False


class SESHelper:
    """Helper class for SES email operations."""
    
    def __init__(self):
        self.clients = AWSClients()
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@govwatcher.com')
    
    def send_vote_advice_email(self, to_email: str, subject: str, body_text: str, body_html: str) -> bool:
        """Send voting advice email via SES."""
        try:
            ses = self.clients.get_ses_client()
            response = ses.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                        'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                    }
                }
            )
            logger.info("Email sent successfully", to=to_email, message_id=response['MessageId'])
            return True
        except ClientError as e:
            logger.error("Failed to send email", error=str(e), to=to_email)
            return False


class SecretsHelper:
    """Helper class for AWS Secrets Manager operations."""
    
    def __init__(self):
        self.clients = AWSClients()
        self._secrets_cache = {}
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Retrieve secret value from Secrets Manager with caching."""
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]
        
        try:
            secrets = self.clients.get_secrets_client()
            response = secrets.get_secret_value(SecretId=secret_name)
            secret_value = response['SecretString']
            self._secrets_cache[secret_name] = secret_value
            logger.debug("Secret retrieved successfully", secret_name=secret_name)
            return secret_value
        except ClientError as e:
            logger.error("Failed to retrieve secret", error=str(e), secret_name=secret_name)
            return None
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from secrets."""
        return self.get_secret(os.getenv('OPENAI_SECRET_NAME', 'GovWatcher/OpenAI'))
    
    def get_private_key(self) -> Optional[str]:
        """Get uAgents private key from secrets."""
        return self.get_secret(os.getenv('PRIVATE_KEY_SECRET_NAME', 'GovWatcher/PrivateKey'))


# Convenience functions for easy access
def get_dynamodb_helper() -> DynamoDBHelper:
    """Get DynamoDB helper instance."""
    return DynamoDBHelper()

def get_s3_helper() -> S3Helper:
    """Get S3 helper instance."""
    return S3Helper()

def get_ses_helper() -> SESHelper:
    """Get SES helper instance."""
    return SESHelper()

def get_secrets_helper() -> SecretsHelper:
    """Get Secrets helper instance."""
    return SecretsHelper() 