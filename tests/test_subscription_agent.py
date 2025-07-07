"""
Unit tests for SubscriptionAgent.
Tests payment validation, DynamoDB storage, and message handling.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal

# Import the agent and models
from src.agents.subscription_agent import agent as subscription_agent
from src.models import SubConfig, SubscriptionRecord
from src.utils.aws_clients import get_dynamodb_helper


class TestSubscriptionAgent:
    """Test suite for SubscriptionAgent functionality."""

    @pytest.fixture
    def mock_dynamodb(self):
        """Mock DynamoDB helper."""
        with patch('src.utils.aws_clients.get_dynamodb_helper') as mock:
            mock_helper = Mock()
            mock.return_value = mock_helper
            yield mock_helper

    @pytest.fixture
    def mock_s3(self):
        """Mock S3 client."""
        with patch('src.utils.aws_clients.get_s3_client') as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def mock_secrets(self):
        """Mock Secrets Manager client."""
        with patch('src.utils.aws_clients.get_secrets_client') as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def sample_sub_config(self):
        """Sample subscription configuration."""
        return SubConfig(
            email="test@example.com",
            chains=["cosmoshub-4", "osmosis-1"],
            policy_blurbs=[
                "Support proposals that improve network security",
                "Oppose proposals that increase inflation"
            ]
        )

    @pytest.fixture
    def mock_context(self):
        """Mock agent context."""
        context = Mock()
        context.send = AsyncMock()
        context.logger = Mock()
        return context

    def test_sub_config_validation(self, sample_sub_config):
        """Test SubConfig model validation."""
        # Valid configuration
        assert sample_sub_config.email == "test@example.com"
        assert len(sample_sub_config.chains) == 2
        assert len(sample_sub_config.policy_blurbs) == 2

        # Test email validation
        with pytest.raises(ValueError):
            SubConfig(
                email="invalid-email",
                chains=["cosmoshub-4"],
                policy_blurbs=["test policy"]
            )

        # Test empty chains
        with pytest.raises(ValueError):
            SubConfig(
                email="test@example.com",
                chains=[],
                policy_blurbs=["test policy"]
            )

        # Test empty policy blurbs
        with pytest.raises(ValueError):
            SubConfig(
                email="test@example.com",
                chains=["cosmoshub-4"],
                policy_blurbs=[]
            )

    def test_calculate_subscription_fee(self, sample_sub_config):
        """Test subscription fee calculation."""
        from src.agents.subscription_agent import calculate_subscription_fee
        
        # Base fee for 1 chain (should be 15 FET)
        single_chain_config = SubConfig(
            email="test@example.com",
            chains=["cosmoshub-4"],
            policy_blurbs=["test policy"]
        )
        fee = calculate_subscription_fee(single_chain_config)
        assert fee == Decimal('15')

        # Fee for 2 chains (should be 15 + 1 = 16 FET)
        fee = calculate_subscription_fee(sample_sub_config)
        assert fee == Decimal('16')

        # Fee for 5 chains (should be 15 + 4 = 19 FET)
        multi_chain_config = SubConfig(
            email="test@example.com",
            chains=["cosmoshub-4", "osmosis-1", "juno-1", "fetch-1", "akash-1"],
            policy_blurbs=["test policy"]
        )
        fee = calculate_subscription_fee(multi_chain_config)
        assert fee == Decimal('19')

    @pytest.mark.asyncio
    async def test_validate_payment_success(self, mock_secrets):
        """Test successful payment validation."""
        from src.agents.subscription_agent import validate_payment
        
        # Mock successful payment validation
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'mock_private_key'
        }
        
        with patch('src.agents.subscription_agent.check_blockchain_payment') as mock_check:
            mock_check.return_value = True
            
            result = await validate_payment(
                sender_address="fetch1234567890abcdef",
                amount=Decimal('15'),
                payment_reference="test_payment_123"
            )
            
            assert result is True
            mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_payment_failure(self, mock_secrets):
        """Test failed payment validation."""
        from src.agents.subscription_agent import validate_payment
        
        mock_secrets.get_secret_value.return_value = {
            'SecretString': 'mock_private_key'
        }
        
        with patch('src.agents.subscription_agent.check_blockchain_payment') as mock_check:
            mock_check.return_value = False
            
            result = await validate_payment(
                sender_address="fetch1234567890abcdef",
                amount=Decimal('15'),
                payment_reference="invalid_payment"
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_store_subscription_success(self, mock_dynamodb, sample_sub_config):
        """Test successful subscription storage."""
        from src.agents.subscription_agent import store_subscription
        
        # Mock successful DynamoDB put
        mock_dynamodb.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        sender = "fetch1234567890abcdef"
        result = await store_subscription(sender, sample_sub_config)
        
        assert result is True
        mock_dynamodb.put_item.assert_called_once()
        
        # Verify the item structure
        call_args = mock_dynamodb.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['wallet'] == sender
        assert item['email'] == sample_sub_config.email
        assert set(item['chains']) == set(sample_sub_config.chains)
        assert 'expires' in item
        assert 'last_notified' in item

    @pytest.mark.asyncio
    async def test_store_subscription_failure(self, mock_dynamodb, sample_sub_config):
        """Test failed subscription storage."""
        from src.agents.subscription_agent import store_subscription
        
        # Mock DynamoDB failure
        mock_dynamodb.put_item.side_effect = Exception("DynamoDB error")
        
        sender = "fetch1234567890abcdef"
        result = await store_subscription(sender, sample_sub_config)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_log_to_s3_success(self, mock_s3):
        """Test successful S3 logging."""
        from src.agents.subscription_agent import log_to_s3
        
        # Mock successful S3 put
        mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        log_data = {
            'event': 'subscription_created',
            'wallet': 'fetch1234567890abcdef',
            'timestamp': time.time()
        }
        
        result = await log_to_s3(log_data, 'subscription')
        assert result is True
        mock_s3.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscription_message_handler_success(
        self, 
        mock_dynamodb, 
        mock_s3, 
        mock_secrets,
        mock_context, 
        sample_sub_config
    ):
        """Test successful subscription message handling."""
        # Mock all dependencies for success
        mock_secrets.get_secret_value.return_value = {'SecretString': 'mock_key'}
        mock_dynamodb.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        with patch('src.agents.subscription_agent.validate_payment') as mock_validate:
            with patch('src.agents.subscription_agent.store_subscription') as mock_store:
                with patch('src.agents.subscription_agent.log_to_s3') as mock_log:
                    # Mock successful operations
                    mock_validate.return_value = True
                    mock_store.return_value = True
                    mock_log.return_value = True
                    
                    # Find the subscription handler
                    handler = None
                    if hasattr(subscription_agent, '_message_handlers'):
                        for h in subscription_agent._message_handlers:
                            if h.get('model') == SubConfig:
                                handler = h['handler']
                                break
                    
                    assert handler is not None, "Subscription handler not found"
                    
                    # Test the handler
                    sender = "fetch1234567890abcdef"
                    result = await handler(mock_context, sender, sample_sub_config)
                    
                    # Verify success response
                    mock_context.send.assert_called_once_with(sender, True)
                    
                    # Verify all operations were called
                    mock_validate.assert_called_once()
                    mock_store.assert_called_once()
                    mock_log.assert_called()

    @pytest.mark.asyncio
    async def test_subscription_message_handler_payment_failure(
        self, 
        mock_context, 
        sample_sub_config
    ):
        """Test subscription handling with payment failure."""
        with patch('src.agents.subscription_agent.validate_payment') as mock_validate:
            with patch('src.agents.subscription_agent.log_to_s3') as mock_log:
                # Mock payment failure
                mock_validate.return_value = False
                mock_log.return_value = True
                
                # Find the subscription handler
                handler = None
                if hasattr(subscription_agent, '_message_handlers'):
                    for h in subscription_agent._message_handlers:
                        if h.get('model') == SubConfig:
                            handler = h['handler']
                            break
                
                assert handler is not None, "Subscription handler not found"
                
                # Test the handler
                sender = "fetch1234567890abcdef"
                result = await handler(mock_context, sender, sample_sub_config)
                
                # Verify failure response
                mock_context.send.assert_called_once_with(sender, False)
                
                # Verify payment validation was attempted
                mock_validate.assert_called_once()

    def test_subscription_record_model(self):
        """Test SubscriptionRecord model."""
        record = SubscriptionRecord(
            wallet="fetch1234567890abcdef",
            email="test@example.com",
            expires=int(time.time()) + 31536000,  # 1 year
            chains={"cosmoshub-4", "osmosis-1"},
            policy=["Support security proposals"],
            last_notified={"cosmoshub-4": 123, "osmosis-1": 456}
        )
        
        assert record.wallet == "fetch1234567890abcdef"
        assert record.email == "test@example.com"
        assert len(record.chains) == 2
        assert len(record.policy) == 1
        assert len(record.last_notified) == 2

    @pytest.mark.asyncio
    async def test_get_existing_subscription(self, mock_dynamodb):
        """Test retrieving existing subscription."""
        from src.agents.subscription_agent import get_existing_subscription
        
        # Mock existing subscription
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'wallet': 'fetch1234567890abcdef',
                'email': 'test@example.com',
                'expires': int(time.time()) + 31536000,
                'chains': {'cosmoshub-4', 'osmosis-1'},
                'policy': ['test policy'],
                'last_notified': {}
            }
        }
        
        result = await get_existing_subscription("fetch1234567890abcdef")
        
        assert result is not None
        assert result['wallet'] == 'fetch1234567890abcdef'
        mock_dynamodb.get_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_nonexistent_subscription(self, mock_dynamodb):
        """Test retrieving non-existent subscription."""
        from src.agents.subscription_agent import get_existing_subscription
        
        # Mock no subscription found
        mock_dynamodb.get_item.return_value = {}
        
        result = await get_existing_subscription("fetch1234567890abcdef")
        
        assert result is None
        mock_dynamodb.get_item.assert_called_once()

    def test_agent_configuration(self):
        """Test agent configuration and setup."""
        # Verify agent has required attributes
        assert hasattr(subscription_agent, 'address')
        assert hasattr(subscription_agent, 'name')
        
        # Verify message handlers are registered
        assert hasattr(subscription_agent, '_message_handlers')
        
        # Find SubConfig handler
        subconfig_handler = None
        for handler in subscription_agent._message_handlers:
            if handler.get('model') == SubConfig:
                subconfig_handler = handler
                break
        
        assert subconfig_handler is not None
        assert subconfig_handler.get('payable') == 15  # Base fee
        assert callable(subconfig_handler.get('handler'))

    @pytest.mark.asyncio
    async def test_error_handling_and_logging(self, mock_context, sample_sub_config):
        """Test error handling and logging in subscription process."""
        with patch('src.agents.subscription_agent.validate_payment') as mock_validate:
            with patch('src.agents.subscription_agent.log_to_s3') as mock_log:
                # Mock validation error
                mock_validate.side_effect = Exception("Validation error")
                mock_log.return_value = True
                
                # Find the subscription handler
                handler = None
                if hasattr(subscription_agent, '_message_handlers'):
                    for h in subscription_agent._message_handlers:
                        if h.get('model') == SubConfig:
                            handler = h['handler']
                            break
                
                # Test error handling
                sender = "fetch1234567890abcdef"
                result = await handler(mock_context, sender, sample_sub_config)
                
                # Should handle error gracefully and send failure response
                mock_context.send.assert_called_once_with(sender, False)
                
                # Should log the error
                mock_log.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 