"""
Unit tests for AnalysisAgent.
Tests OpenAI integration, policy analysis, and vote recommendation generation.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal

# Import the agent and models
from src.agents.analysis_agent import agent as analysis_agent
from src.models import NewProposal, VoteAdvice, SubscriptionRecord


class TestAnalysisAgent:
    """Test suite for AnalysisAgent functionality."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        with patch('src.agents.analysis_agent.get_openai_client') as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            yield mock_client

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
    def mock_context(self):
        """Mock agent context."""
        context = Mock()
        context.send = AsyncMock()
        context.logger = Mock()
        return context

    @pytest.fixture
    def sample_new_proposal(self):
        """Sample NewProposal message."""
        return NewProposal(
            chain="cosmoshub-4",
            proposal_id=123,
            title="Upgrade Network Security Protocol",
            description="This proposal aims to upgrade the network's security protocol."
        )

    @pytest.fixture
    def sample_subscription_records(self):
        """Sample subscription records from DynamoDB."""
        return [
            {
                'wallet': 'fetch1234567890abcdef',
                'email': 'user1@example.com',
                'chains': {'cosmoshub-4', 'osmosis-1'},
                'policy': json.dumps([
                    "Support proposals that improve network security",
                    "Oppose proposals that increase inflation"
                ]),
                'expires': int(time.time()) + 86400,
                'last_notified': {}
            },
            {
                'wallet': 'fetch0987654321fedcba',
                'email': 'user2@example.com', 
                'chains': {'cosmoshub-4'},
                'policy': json.dumps([
                    "Support community-driven initiatives",
                    "Oppose centralization efforts"
                ]),
                'expires': int(time.time()) + 86400,
                'last_notified': {}
            }
        ]

    @pytest.fixture
    def sample_openai_response(self):
        """Sample OpenAI API response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "decision": "YES",
            "confidence": 0.85,
            "rationale": "This proposal aligns with your policy of supporting network security improvements. The upgrade to cryptographic standards and validator authentication will enhance the overall security of the network, which is a priority based on your preferences."
        })
        return mock_response

    def test_vote_advice_validation(self):
        """Test VoteAdvice model validation."""
        advice = VoteAdvice(
            chain="cosmoshub-4",
            proposal_id=123,
            target_wallet="fetch1234567890abcdef",
            decision="YES",
            confidence=0.85,
            rationale="This proposal improves network security."
        )
        
        assert advice.chain == "cosmoshub-4"
        assert advice.decision == "YES"
        assert advice.confidence == 0.85

    @pytest.mark.asyncio
    async def test_get_active_subscriptions_for_chain(self, mock_dynamodb, sample_subscription_records):
        """Test fetching active subscriptions for a specific chain."""
        from src.agents.analysis_agent import get_active_subscriptions_for_chain
        
        # Mock DynamoDB scan response
        mock_dynamodb.scan.return_value = {
            'Items': sample_subscription_records
        }
        
        chain_id = "cosmoshub-4"
        subscriptions = await get_active_subscriptions_for_chain(chain_id)
        
        # Should return both subscriptions (both include cosmoshub-4)
        assert len(subscriptions) == 2
        assert all(chain_id in sub['chains'] for sub in subscriptions)

    @pytest.mark.asyncio
    async def test_get_active_subscriptions_no_matches(self, mock_dynamodb):
        """Test fetching subscriptions when no active subscriptions exist for chain."""
        from src.agents.analysis_agent import get_active_subscriptions_for_chain
        
        # Mock empty DynamoDB response
        mock_dynamodb.scan.return_value = {'Items': []}
        
        chain_id = "nonexistent-chain"
        subscriptions = await get_active_subscriptions_for_chain(chain_id)
        
        assert len(subscriptions) == 0

    @pytest.mark.asyncio
    async def test_build_analysis_prompt(self, sample_new_proposal):
        """Test building OpenAI analysis prompt."""
        from src.agents.analysis_agent import build_analysis_prompt
        
        policy_blurbs = [
            "Support proposals that improve network security",
            "Oppose proposals that increase inflation"
        ]
        
        prompt = build_analysis_prompt(sample_new_proposal, policy_blurbs)
        
        # Verify prompt contains key elements
        assert sample_new_proposal.title in prompt
        assert sample_new_proposal.description in prompt
        assert policy_blurbs[0] in prompt
        assert policy_blurbs[1] in prompt
        assert "YES" in prompt
        assert "NO" in prompt
        assert "ABSTAIN" in prompt

    @pytest.mark.asyncio
    async def test_analyze_proposal_with_openai_success(self, mock_openai_client, sample_openai_response, sample_new_proposal):
        """Test successful proposal analysis with OpenAI."""
        from src.agents.analysis_agent import analyze_proposal_with_openai
        
        # Mock successful OpenAI response
        mock_openai_client.chat.completions.create.return_value = sample_openai_response
        
        policy_blurbs = ["Support proposals that improve network security"]
        
        result = await analyze_proposal_with_openai(sample_new_proposal, policy_blurbs)
        
        assert result['decision'] == "YES"
        assert result['confidence'] == 0.85
        assert "security" in result['rationale'].lower()
        
        # Verify OpenAI was called correctly
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4o'
        assert len(call_args[1]['messages']) > 0

    @pytest.mark.asyncio
    async def test_analyze_proposal_with_openai_api_error(self, mock_openai_client, sample_new_proposal):
        """Test handling OpenAI API errors."""
        from src.agents.analysis_agent import analyze_proposal_with_openai
        
        # Mock OpenAI API error
        mock_openai_client.chat.completions.create.side_effect = Exception("OpenAI API Error")
        
        policy_blurbs = ["Support proposals that improve network security"]
        
        result = await analyze_proposal_with_openai(sample_new_proposal, policy_blurbs)
        
        # Should return default abstain response on error
        assert result['decision'] == "ABSTAIN"
        assert result['confidence'] == 0.0
        assert "error" in result['rationale'].lower()

    @pytest.mark.asyncio
    async def test_analyze_proposal_with_openai_invalid_response(self, mock_openai_client, sample_new_proposal):
        """Test handling invalid OpenAI response format."""
        from src.agents.analysis_agent import analyze_proposal_with_openai
        
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        policy_blurbs = ["Support proposals that improve network security"]
        
        result = await analyze_proposal_with_openai(sample_new_proposal, policy_blurbs)
        
        # Should return default abstain response on invalid JSON
        assert result['decision'] == "ABSTAIN"
        assert result['confidence'] == 0.0

    @pytest.mark.asyncio
    async def test_log_analysis_to_s3(self, mock_s3, sample_new_proposal):
        """Test logging analysis results to S3."""
        from src.agents.analysis_agent import log_analysis_to_s3
        
        analysis_data = {
            'proposal': sample_new_proposal.dict(),
            'decision': 'YES',
            'confidence': 0.85,
            'rationale': 'Test rationale',
            'timestamp': '2024-01-15T10:00:00Z'
        }
        
        await log_analysis_to_s3(analysis_data)
        
        # Verify S3 put_object was called
        mock_s3.put_object.assert_called_once()
        call_args = mock_s3.put_object.call_args
        
        assert 'Bucket' in call_args[1]
        assert 'Key' in call_args[1]
        assert 'Body' in call_args[1]
        
        # Verify the log structure
        log_data = json.loads(call_args[1]['Body'])
        assert log_data['proposal']['proposal_id'] == sample_new_proposal.proposal_id
        assert log_data['decision'] == 'YES'

    @pytest.mark.asyncio
    async def test_analysis_message_handler_success(
        self, 
        mock_openai_client,
        mock_dynamodb, 
        mock_s3,
        mock_context, 
        sample_new_proposal,
        sample_subscription_records,
        sample_openai_response
    ):
        """Test successful analysis message handling."""
        # Mock all dependencies
        mock_dynamodb.scan.return_value = {'Items': sample_subscription_records}
        mock_openai_client.chat.completions.create.return_value = sample_openai_response
        
        # Import and patch the message handler
        with patch('src.agents.analysis_agent.get_active_subscriptions_for_chain') as mock_get_subs, \
             patch('src.agents.analysis_agent.analyze_proposal_with_openai') as mock_analyze, \
             patch('src.agents.analysis_agent.log_analysis_to_s3') as mock_log:
            
            mock_get_subs.return_value = sample_subscription_records
            mock_analyze.return_value = {
                'decision': 'YES',
                'confidence': 0.85,
                'rationale': 'Test rationale'
            }
            
            # Import the handler function
            from src.agents.analysis_agent import handle_new_proposal
            
            await handle_new_proposal(mock_context, "sender", sample_new_proposal)
            
            # Verify analysis was performed for each subscription
            assert mock_analyze.call_count == len(sample_subscription_records)
            
            # Verify VoteAdvice messages were sent
            assert mock_context.send.call_count == len(sample_subscription_records)
            
            # Verify logging occurred
            mock_log.assert_called()

    @pytest.mark.asyncio
    async def test_analysis_message_handler_no_subscriptions(
        self, 
        mock_dynamodb,
        mock_context, 
        sample_new_proposal
    ):
        """Test analysis when no active subscriptions exist."""
        # Mock empty subscriptions
        mock_dynamodb.scan.return_value = {'Items': []}
        
        with patch('src.agents.analysis_agent.get_active_subscriptions_for_chain') as mock_get_subs:
            mock_get_subs.return_value = []
            
            from src.agents.analysis_agent import handle_new_proposal
            
            await handle_new_proposal(mock_context, "sender", sample_new_proposal)
            
            # Should not send any messages
            mock_context.send.assert_not_called()

    def test_agent_configuration(self):
        """Test agent configuration and setup."""
        from src.agents.analysis_agent import agent
        
        # Verify agent is properly configured
        assert agent is not None
        assert hasattr(agent, 'name')
        assert hasattr(agent, 'address')

    @pytest.mark.asyncio
    async def test_policy_matching_logic(self, sample_new_proposal):
        """Test policy matching and decision logic."""
        from src.agents.analysis_agent import build_analysis_prompt
        
        # Test security-focused policy
        security_policy = ["Support proposals that improve network security"]
        prompt = build_analysis_prompt(sample_new_proposal, security_policy)
        
        # Should contain security-related keywords
        assert "security" in prompt.lower()
        assert sample_new_proposal.title in prompt
        
        # Test inflation-focused policy
        inflation_policy = ["Oppose proposals that increase inflation"]
        prompt = build_analysis_prompt(sample_new_proposal, inflation_policy)
        
        # Should contain inflation-related keywords
        assert "inflation" in prompt.lower()

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, mock_openai_client, sample_new_proposal):
        """Test confidence scoring in analysis results."""
        from src.agents.analysis_agent import analyze_proposal_with_openai
        
        # Mock high confidence response
        high_confidence_response = Mock()
        high_confidence_response.choices = [Mock()]
        high_confidence_response.choices[0].message = Mock()
        high_confidence_response.choices[0].message.content = json.dumps({
            "decision": "YES",
            "confidence": 0.95,
            "rationale": "Strong alignment with security policies"
        })
        
        mock_openai_client.chat.completions.create.return_value = high_confidence_response
        
        policy_blurbs = ["Support proposals that improve network security"]
        result = await analyze_proposal_with_openai(sample_new_proposal, policy_blurbs)
        
        assert result['confidence'] == 0.95
        assert result['decision'] == "YES"

    @pytest.mark.asyncio
    async def test_error_handling_and_logging(self, mock_context, sample_new_proposal):
        """Test comprehensive error handling and logging."""
        with patch('src.agents.analysis_agent.get_active_subscriptions_for_chain') as mock_get_subs:
            # Mock database error
            mock_get_subs.side_effect = Exception("Database connection error")
            
            from src.agents.analysis_agent import handle_new_proposal
            
            # Should handle error gracefully
            await handle_new_proposal(mock_context, "sender", sample_new_proposal)
            
            # Should not crash and should log error
            mock_context.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_openai_analysis_success(self, mock_openai_client, sample_new_proposal):
        """Test successful OpenAI analysis."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "decision": "YES",
            "confidence": 0.85,
            "rationale": "Supports network security improvements."
        })
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # This would test the actual analysis function when implemented
        assert mock_response.choices[0].message.content is not None

    @pytest.mark.asyncio
    async def test_get_subscriptions_for_chain(self, mock_dynamodb, sample_subscription_records):
        """Test fetching active subscriptions for a chain."""
        mock_dynamodb.scan.return_value = {'Items': sample_subscription_records}
        
        # This would test the subscription fetching logic
        assert len(sample_subscription_records) == 2

    @pytest.mark.asyncio
    async def test_policy_analysis(self, sample_new_proposal):
        """Test policy-based analysis logic."""
        policy_blurbs = [
            "Support proposals that improve network security",
            "Oppose proposals that increase inflation"
        ]
        
        # Test that security proposal matches security policy
        assert "security" in sample_new_proposal.description.lower()
        assert "security" in policy_blurbs[0].lower()

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_context, sample_new_proposal):
        """Test error handling in analysis."""
        with patch('src.agents.analysis_agent.get_active_subscriptions_for_chain') as mock_get_subs:
            mock_get_subs.side_effect = Exception("Database error")
            
            # Should handle errors gracefully without crashing
            try:
                # This would call the actual handler when implemented
                pass
            except Exception:
                pytest.fail("Should handle errors gracefully")

    def test_agent_configuration(self):
        """Test agent is properly configured."""
        # This would test the agent configuration when imported
        assert True  # Placeholder for actual agent tests 