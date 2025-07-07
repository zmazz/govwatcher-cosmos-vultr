"""
Pytest configuration and common fixtures for Cosmos Gov-Watcher tests.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for all tests."""
    env_vars = {
        'AWS_REGION': 'us-east-1',
        'DYNAMODB_TABLE_NAME': 'test-govwatcher-subscriptions',
        'S3_BUCKET_NAME': 'test-govwatcher-logs',
        'FROM_EMAIL': 'test@govwatcher.com',
        'OPENAI_SECRET_NAME': 'test/openai',
        'PRIVATE_KEY_SECRET_NAME': 'test/private-key',
        'LLM_MODEL': 'gpt-4o',
        'LOG_LEVEL': 'DEBUG',
        'STAGE': 'test'
    }
    
    with patch.dict(os.environ, env_vars):
        yield

@pytest.fixture
def mock_aws_clients():
    """Mock all AWS clients."""
    with patch('src.utils.aws_clients.get_dynamodb_client') as mock_dynamo, \
         patch('src.utils.aws_clients.get_s3_client') as mock_s3, \
         patch('src.utils.aws_clients.get_ses_client') as mock_ses, \
         patch('src.utils.aws_clients.get_secrets_client') as mock_secrets:
        
        # Configure mock clients
        mock_dynamo.return_value = Mock()
        mock_s3.return_value = Mock()
        mock_ses.return_value = Mock()
        mock_secrets.return_value = Mock()
        
        yield {
            'dynamodb': mock_dynamo.return_value,
            's3': mock_s3.return_value,
            'ses': mock_ses.return_value,
            'secrets': mock_secrets.return_value
        } 