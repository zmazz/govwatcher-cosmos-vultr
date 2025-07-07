"""
Unit tests for AWS helper classes.
Tests the actual helper classes that exist in the codebase.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws

from src.utils.aws_clients import DynamoDBHelper, S3Helper, SESHelper, SecretsHelper
from src.models import SubscriptionRecord, SubConfig


class TestDynamoDBHelper:
    """Test suite for DynamoDB helper functionality."""

    @mock_aws
    def test_put_subscription_success(self):
        """Test successful subscription storage."""
        # Create mock DynamoDB table
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='GovSubscriptions',
            KeySchema=[{'AttributeName': 'wallet', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'wallet', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()  # Wait for table to be ready
        
        # Test the helper
        with patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'GovSubscriptions'}):
            helper = DynamoDBHelper()
            
            subscription_data = {
                'wallet': 'fetch1234567890abcdef',
                'email': 'test@example.com',
                'chains': ['cosmoshub-4'],
                'policy': json.dumps(['Support security proposals']),
                'expires': int(time.time()) + 86400,
                'last_notified': {},
                'created_at': int(time.time())
            }
            
            result = helper.put_subscription(subscription_data)
            assert result is True

    @mock_aws
    def test_get_subscription_success(self):
        """Test successful subscription retrieval."""
        # Create and populate mock table
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='GovSubscriptions',
            KeySchema=[{'AttributeName': 'wallet', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'wallet', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()  # Wait for table to be ready
        
        # Add test data
        wallet = 'fetch1234567890abcdef'
        test_item = {
            'wallet': wallet,
            'email': 'test@example.com',
            'chains': ['cosmoshub-4'],
            'policy': json.dumps(['Support security proposals']),
            'expires': int(time.time()) + 86400,
            'last_notified': {},
            'created_at': int(time.time())
        }
        table.put_item(Item=test_item)
        
        # Test retrieval
        with patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'GovSubscriptions'}):
            helper = DynamoDBHelper()
            result = helper.get_subscription(wallet)
            
            assert result is not None
            assert result['wallet'] == wallet
            assert result['email'] == 'test@example.com'

    @mock_aws
    def test_get_subscription_not_found(self):
        """Test subscription retrieval when record doesn't exist."""
        # Create empty table
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='GovSubscriptions',
            KeySchema=[{'AttributeName': 'wallet', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'wallet', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()  # Wait for table to be ready
        
        with patch.dict('os.environ', {'DYNAMODB_TABLE_NAME': 'GovSubscriptions'}):
            helper = DynamoDBHelper()
            result = helper.get_subscription('nonexistent_wallet')
            
            assert result is None


class TestS3Helper:
    """Test suite for S3 helper functionality."""

    @mock_aws
    def test_put_log_success(self):
        """Test successful log storage in S3."""
        # Create mock S3 bucket
        import boto3
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'test-govwatcher-logs'
        s3.create_bucket(Bucket=bucket_name)
        
        with patch.dict('os.environ', {'S3_BUCKET_NAME': bucket_name}):
            helper = S3Helper()
            
            log_entry = {
                'timestamp': int(time.time()),
                'lambda_name': 'test-function',
                'event_type': 'test_event',
                'data': {'test': 'data'},
                'success': True
            }
            
            s3_key = 'logs/2024/01/15/test_log.json'
            result = helper.put_log(log_entry, s3_key)
            
            assert result is True
            
            # Verify the log was stored
            response = s3.get_object(Bucket=bucket_name, Key=s3_key)
            stored_data = json.loads(response['Body'].read())
            assert stored_data['event_type'] == 'test_event'


class TestSESHelper:
    """Test suite for SES helper functionality."""

    @mock_aws
    def test_send_vote_advice_email_success(self):
        """Test successful email sending via SES."""
        # Setup mock SES
        import boto3
        ses = boto3.client('ses', region_name='us-east-1')
        from_email = 'test@govwatcher.com'
        to_email = 'user@example.com'
        
        # Verify email addresses in SES (required for moto)
        ses.verify_email_identity(EmailAddress=from_email)
        ses.verify_email_identity(EmailAddress=to_email)
        
        # Verify the identities are verified
        identities = ses.list_verified_email_addresses()
        assert from_email in identities['VerifiedEmailAddresses']
        assert to_email in identities['VerifiedEmailAddresses']
        
        with patch.dict('os.environ', {'FROM_EMAIL': from_email}):
            helper = SESHelper()
            
            result = helper.send_vote_advice_email(
                to_email=to_email,
                subject='Test Vote Advice',
                body_text='Test email body',
                body_html='<p>Test email body</p>'
            )
            
            assert result is True


class TestSecretsHelper:
    """Test suite for Secrets Manager helper functionality."""

    def test_get_secret_success(self):
        """Test successful secret retrieval."""
        with patch('boto3.client') as mock_boto:
            mock_secrets_client = Mock()
            mock_boto.return_value = mock_secrets_client
            
            # Mock successful secret retrieval
            mock_secrets_client.get_secret_value.return_value = {
                'SecretString': 'test_secret_value'
            }
            
            helper = SecretsHelper()
            result = helper.get_secret('test_secret')
            
            assert result == 'test_secret_value'
            mock_secrets_client.get_secret_value.assert_called_once_with(SecretId='test_secret')

    def test_get_secret_caching(self):
        """Test that secrets are cached after first retrieval."""
        with patch('boto3.client') as mock_boto:
            mock_secrets_client = Mock()
            mock_boto.return_value = mock_secrets_client
            
            mock_secrets_client.get_secret_value.return_value = {
                'SecretString': 'cached_secret_value'
            }
            
            helper = SecretsHelper()
            
            # First call should hit the API
            result1 = helper.get_secret('cached_secret')
            assert result1 == 'cached_secret_value'
            
            # Second call should use cache
            result2 = helper.get_secret('cached_secret')
            assert result2 == 'cached_secret_value'
            
            # Should only call the API once due to caching
            mock_secrets_client.get_secret_value.assert_called_once()


class TestSubscriptionRecordModel:
    """Test suite for SubscriptionRecord model functionality."""

    def test_subscription_record_creation(self):
        """Test creating subscription record from SubConfig."""
        config = SubConfig(
            email='test@example.com',
            chains=['cosmoshub-4', 'osmosis-1'],
            policy_blurbs=['Support security proposals', 'Oppose inflation increases']
        )
        
        wallet = 'fetch1234567890abcdef'
        expires = int(time.time()) + 86400
        created_at = int(time.time())
        
        record = SubscriptionRecord.from_sub_config(wallet, config, expires, created_at)
        
        assert record.wallet == wallet
        assert record.email == config.email
        assert record.chains == config.chains
        assert record.expires == expires
        assert record.created_at == created_at
        
        # Test policy parsing
        policy_blurbs = record.get_policy_blurbs()
        assert len(policy_blurbs) == 2
        assert 'Support security proposals' in policy_blurbs

    def test_subscription_record_validation(self):
        """Test subscription record validation."""
        current_time = int(time.time())
        
        record = SubscriptionRecord(
            wallet='fetch1234567890abcdef',
            email='test@example.com',
            expires=current_time + 86400,  # Active
            chains=['cosmoshub-4'],
            policy=json.dumps(['Test policy']),
            created_at=current_time,
            last_notified={}
        )
        
        # Test active status
        assert record.is_active(current_time) is True
        assert record.is_active(current_time + 90000) is False  # Expired
        
        # Test notification logic
        assert record.should_notify('cosmoshub-4', 123) is True  # New proposal
        assert record.should_notify('osmosis-1', 123) is False  # Not subscribed to chain
        
        # Update last notified and test again
        record.last_notified['cosmoshub-4'] = 123
        assert record.should_notify('cosmoshub-4', 123) is False  # Already notified
        assert record.should_notify('cosmoshub-4', 124) is True   # Newer proposal 