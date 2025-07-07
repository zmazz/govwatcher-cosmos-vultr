"""
Unit tests for WatcherAgent.
Tests proposal fetching, chain monitoring, and message forwarding.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

# Import the agent and models
from src.agents.watcher_agent import agent as watcher_agent
from src.models import NewProposal
from src.utils.cosmos_client import CosmosProposalFetcher


class TestWatcherAgent:
    """Test suite for WatcherAgent functionality."""

    @pytest.fixture
    def mock_cosmos_client(self):
        """Mock Cosmos client."""
        with patch('src.utils.cosmos_client.CosmosProposalFetcher') as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            yield mock_client

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
    def sample_proposals(self):
        """Sample proposal data from Cosmos chain."""
        return [
            {
                "proposal_id": "123",
                "content": {
                    "title": "Upgrade Network to v2.0",
                    "description": "This proposal upgrades the network to version 2.0 with improved security features."
                },
                "status": "PROPOSAL_STATUS_VOTING_PERIOD",
                "voting_start_time": "2024-01-15T10:00:00Z",
                "voting_end_time": "2024-01-22T10:00:00Z"
            },
            {
                "proposal_id": "124", 
                "content": {
                    "title": "Increase Block Size Limit",
                    "description": "Proposal to increase the maximum block size from 1MB to 2MB."
                },
                "status": "PROPOSAL_STATUS_VOTING_PERIOD",
                "voting_start_time": "2024-01-16T10:00:00Z",
                "voting_end_time": "2024-01-23T10:00:00Z"
            }
        ]

    @pytest.fixture
    def sample_new_proposal(self):
        """Sample NewProposal message."""
        return NewProposal(
            chain="cosmoshub-4",
            proposal_id=123,
            title="Upgrade Network to v2.0",
            description="This proposal upgrades the network to version 2.0 with improved security features."
        )

    def test_new_proposal_validation(self, sample_new_proposal):
        """Test NewProposal model validation."""
        # Valid proposal
        assert sample_new_proposal.chain == "cosmoshub-4"
        assert sample_new_proposal.proposal_id == 123
        assert sample_new_proposal.title == "Upgrade Network to v2.0"
        assert len(sample_new_proposal.description) > 0

        # Test required fields
        with pytest.raises(ValueError):
            NewProposal(
                chain="",
                proposal_id=123,
                title="Test",
                description="Test description"
            )

        with pytest.raises(ValueError):
            NewProposal(
                chain="cosmoshub-4",
                proposal_id=0,
                title="Test",
                description="Test description"
            )

        with pytest.raises(ValueError):
            NewProposal(
                chain="cosmoshub-4",
                proposal_id=123,
                title="",
                description="Test description"
            )

    @pytest.mark.asyncio
    async def test_fetch_proposals_success(self, mock_cosmos_client, sample_proposals):
        """Test successful proposal fetching."""
        from src.agents.watcher_agent import fetch_proposals
        
        # Mock successful API response
        mock_cosmos_client.get_proposals.return_value = sample_proposals
        
        chain_id = "cosmoshub-4"
        last_proposal_id = 122
        
        result = await fetch_proposals(chain_id, last_proposal_id)
        
        assert len(result) == 2
        assert result[0]['proposal_id'] == "123"
        assert result[1]['proposal_id'] == "124"
        
        mock_cosmos_client.get_proposals.assert_called_once_with(
            chain_id, 
            min_proposal_id=last_proposal_id + 1
        )

    @pytest.mark.asyncio
    async def test_fetch_proposals_no_new_proposals(self, mock_cosmos_client):
        """Test fetching when no new proposals exist."""
        from src.agents.watcher_agent import fetch_proposals
        
        # Mock empty response
        mock_cosmos_client.get_proposals.return_value = []
        
        chain_id = "cosmoshub-4"
        last_proposal_id = 125
        
        result = await fetch_proposals(chain_id, last_proposal_id)
        
        assert len(result) == 0
        mock_cosmos_client.get_proposals.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_proposals_api_error(self, mock_cosmos_client):
        """Test handling of API errors during proposal fetching."""
        from src.agents.watcher_agent import fetch_proposals
        
        # Mock API error
        mock_cosmos_client.get_proposals.side_effect = Exception("API Error")
        
        chain_id = "cosmoshub-4"
        last_proposal_id = 122
        
        result = await fetch_proposals(chain_id, last_proposal_id)
        
        # Should return empty list on error
        assert result == []

    @pytest.mark.asyncio
    async def test_filter_voting_proposals(self, sample_proposals):
        """Test filtering proposals in voting period."""
        from src.agents.watcher_agent import filter_voting_proposals
        
        # Add a proposal not in voting period
        all_proposals = sample_proposals + [{
            "proposal_id": "125",
            "content": {
                "title": "Rejected Proposal",
                "description": "This proposal was rejected."
            },
            "status": "PROPOSAL_STATUS_REJECTED",
            "voting_start_time": "2024-01-10T10:00:00Z",
            "voting_end_time": "2024-01-17T10:00:00Z"
        }]
        
        voting_proposals = filter_voting_proposals(all_proposals)
        
        # Should only return proposals in voting period
        assert len(voting_proposals) == 2
        assert all(p["status"] == "PROPOSAL_STATUS_VOTING_PERIOD" for p in voting_proposals)

    @pytest.mark.asyncio
    async def test_convert_to_new_proposal(self, sample_proposals):
        """Test converting chain proposal to NewProposal message."""
        from src.agents.watcher_agent import convert_to_new_proposal
        
        chain_id = "cosmoshub-4"
        proposal_data = sample_proposals[0]
        
        new_proposal = convert_to_new_proposal(proposal_data, chain_id)
        
        assert isinstance(new_proposal, NewProposal)
        assert new_proposal.chain == chain_id
        assert new_proposal.proposal_id == 123
        assert new_proposal.title == "Upgrade Network to v2.0"
        assert len(new_proposal.description) > 0

    @pytest.mark.asyncio
    async def test_get_last_proposal_id(self):
        """Test getting last processed proposal ID."""
        from src.agents.watcher_agent import get_last_proposal_id, set_last_proposal_id
        
        chain_id = "cosmoshub-4"
        
        # Test default value
        last_id = get_last_proposal_id(chain_id)
        assert last_id == 0
        
        # Test setting and getting
        set_last_proposal_id(chain_id, 123)
        last_id = get_last_proposal_id(chain_id)
        assert last_id == 123

    @pytest.mark.asyncio
    async def test_log_to_s3_success(self, mock_s3):
        """Test successful S3 logging."""
        from src.agents.watcher_agent import log_to_s3
        
        # Mock successful S3 put
        mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        log_data = {
            'event': 'proposals_fetched',
            'chain': 'cosmoshub-4',
            'count': 2,
            'timestamp': time.time()
        }
        
        result = await log_to_s3(log_data, 'watcher')
        assert result is True
        mock_s3.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_watcher_interval_handler_success(
        self, 
        mock_cosmos_client, 
        mock_s3,
        mock_context, 
        sample_proposals
    ):
        """Test successful watcher interval execution."""
        # Mock environment variables
        with patch.dict('os.environ', {
            'CHAIN_ID': 'cosmoshub-4',
            'ANALYSIS_AGENT_ADDRESS': 'analysis_agent_123'
        }):
            # Mock successful operations
            mock_cosmos_client.get_proposals.return_value = sample_proposals
            mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
            
            with patch('src.agents.watcher_agent.fetch_proposals') as mock_fetch:
                with patch('src.agents.watcher_agent.log_to_s3') as mock_log:
                    # Mock successful fetch
                    mock_fetch.return_value = sample_proposals
                    mock_log.return_value = True
                    
                    # Find the interval handler
                    handler = None
                    if hasattr(watcher_agent, '_interval_handlers'):
                        handler = watcher_agent._interval_handlers[0]
                    
                    assert handler is not None, "Interval handler not found"
                    
                    # Test the handler
                    await handler(mock_context)
                    
                    # Verify proposals were fetched
                    mock_fetch.assert_called_once()
                    
                    # Verify messages were sent to analysis agent
                    assert mock_context.send.call_count == 2  # Two proposals
                    
                    # Verify logging
                    mock_log.assert_called()

    @pytest.mark.asyncio
    async def test_watcher_interval_handler_no_new_proposals(
        self, 
        mock_context
    ):
        """Test watcher interval when no new proposals exist."""
        with patch.dict('os.environ', {
            'CHAIN_ID': 'cosmoshub-4',
            'ANALYSIS_AGENT_ADDRESS': 'analysis_agent_123'
        }):
            with patch('src.agents.watcher_agent.fetch_proposals') as mock_fetch:
                with patch('src.agents.watcher_agent.log_to_s3') as mock_log:
                    # Mock no new proposals
                    mock_fetch.return_value = []
                    mock_log.return_value = True
                    
                    # Find the interval handler
                    handler = None
                    if hasattr(watcher_agent, '_interval_handlers'):
                        handler = watcher_agent._interval_handlers[0]
                    
                    # Test the handler
                    await handler(mock_context)
                    
                    # Verify no messages were sent
                    mock_context.send.assert_not_called()
                    
                    # Verify logging still occurred
                    mock_log.assert_called()

    @pytest.mark.asyncio
    async def test_watcher_interval_handler_error_handling(
        self, 
        mock_context
    ):
        """Test error handling in watcher interval."""
        with patch.dict('os.environ', {
            'CHAIN_ID': 'cosmoshub-4',
            'ANALYSIS_AGENT_ADDRESS': 'analysis_agent_123'
        }):
            with patch('src.agents.watcher_agent.fetch_proposals') as mock_fetch:
                with patch('src.agents.watcher_agent.log_to_s3') as mock_log:
                    # Mock fetch error
                    mock_fetch.side_effect = Exception("Fetch error")
                    mock_log.return_value = True
                    
                    # Find the interval handler
                    handler = None
                    if hasattr(watcher_agent, '_interval_handlers'):
                        handler = watcher_agent._interval_handlers[0]
                    
                    # Test error handling
                    await handler(mock_context)
                    
                    # Should handle error gracefully
                    mock_context.send.assert_not_called()
                    
                    # Should log the error
                    mock_log.assert_called()

    def test_agent_configuration(self):
        """Test agent configuration and setup."""
        # Verify agent has required attributes
        assert hasattr(watcher_agent, 'address')
        assert hasattr(watcher_agent, 'name')
        
        # Verify interval handlers are registered
        assert hasattr(watcher_agent, '_interval_handlers')
        assert len(watcher_agent._interval_handlers) > 0
        
        # Verify interval handler is callable
        handler = watcher_agent._interval_handlers[0]
        assert callable(handler)

    @pytest.mark.asyncio
    async def test_proposal_deduplication(self, mock_context, sample_proposals):
        """Test that duplicate proposals are not sent multiple times."""
        with patch.dict('os.environ', {
            'CHAIN_ID': 'cosmoshub-4',
            'ANALYSIS_AGENT_ADDRESS': 'analysis_agent_123'
        }):
            with patch('src.agents.watcher_agent.fetch_proposals') as mock_fetch:
                with patch('src.agents.watcher_agent.log_to_s3') as mock_log:
                    with patch('src.agents.watcher_agent.get_last_proposal_id') as mock_get_last:
                        with patch('src.agents.watcher_agent.set_last_proposal_id') as mock_set_last:
                            # Mock returning same proposals twice
                            mock_fetch.return_value = sample_proposals
                            mock_log.return_value = True
                            mock_get_last.return_value = 120  # Lower than sample proposal IDs
                            
                            # Find the interval handler
                            handler = watcher_agent._interval_handlers[0]
                            
                            # Run handler twice
                            await handler(mock_context)
                            await handler(mock_context)
                            
                            # Should update last proposal ID to prevent duplicates
                            mock_set_last.assert_called()
                            
                            # Verify the last proposal ID was set correctly
                            last_call = mock_set_last.call_args_list[-1]
                            assert last_call[0][1] == 124  # Highest proposal ID

    @pytest.mark.asyncio
    async def test_multi_chain_support(self, mock_context, sample_proposals):
        """Test support for multiple chains."""
        chains = ['cosmoshub-4', 'osmosis-1', 'juno-1']
        
        for chain_id in chains:
            with patch.dict('os.environ', {
                'CHAIN_ID': chain_id,
                'ANALYSIS_AGENT_ADDRESS': 'analysis_agent_123'
            }):
                with patch('src.agents.watcher_agent.fetch_proposals') as mock_fetch:
                    with patch('src.agents.watcher_agent.log_to_s3') as mock_log:
                        # Mock proposals for this chain
                        chain_proposals = [
                            {**p, 'chain_id': chain_id} for p in sample_proposals
                        ]
                        mock_fetch.return_value = chain_proposals
                        mock_log.return_value = True
                        
                        # Find the interval handler
                        handler = watcher_agent._interval_handlers[0]
                        
                        # Test the handler
                        await handler(mock_context)
                        
                        # Verify proposals were processed for this chain
                        mock_fetch.assert_called_once_with(chain_id, 0)

    @pytest.mark.asyncio
    async def test_proposal_status_filtering(self):
        """Test filtering proposals by status."""
        from src.agents.watcher_agent import filter_voting_proposals
        
        proposals_mixed_status = [
            {
                "proposal_id": "1",
                "status": "PROPOSAL_STATUS_VOTING_PERIOD",
                "content": {"title": "Voting", "description": "In voting"}
            },
            {
                "proposal_id": "2", 
                "status": "PROPOSAL_STATUS_PASSED",
                "content": {"title": "Passed", "description": "Already passed"}
            },
            {
                "proposal_id": "3",
                "status": "PROPOSAL_STATUS_REJECTED",
                "content": {"title": "Rejected", "description": "Was rejected"}
            },
            {
                "proposal_id": "4",
                "status": "PROPOSAL_STATUS_VOTING_PERIOD",
                "content": {"title": "Voting 2", "description": "Also voting"}
            }
        ]
        
        voting_only = filter_voting_proposals(proposals_mixed_status)
        
        assert len(voting_only) == 2
        assert voting_only[0]["proposal_id"] == "1"
        assert voting_only[1]["proposal_id"] == "4"
        assert all(p["status"] == "PROPOSAL_STATUS_VOTING_PERIOD" for p in voting_only)

    @pytest.mark.asyncio
    async def test_cosmos_client_integration(self, mock_cosmos_client):
        """Test integration with CosmosClient."""
        from src.agents.watcher_agent import fetch_proposals
        
        # Test different chain configurations
        chain_configs = [
            ("cosmoshub-4", "https://cosmos-rpc.polkachu.com"),
            ("osmosis-1", "https://osmosis-rpc.polkachu.com"),
            ("juno-1", "https://juno-rpc.polkachu.com")
        ]
        
        for chain_id, expected_endpoint in chain_configs:
            mock_cosmos_client.get_proposals.return_value = []
            
            await fetch_proposals(chain_id, 0)
            
            # Verify client was called with correct parameters
            mock_cosmos_client.get_proposals.assert_called()

    def test_environment_variable_handling(self):
        """Test handling of environment variables."""
        from src.agents.watcher_agent import get_chain_config
        
        # Test with valid chain ID
        with patch.dict('os.environ', {'CHAIN_ID': 'cosmoshub-4'}):
            config = get_chain_config()
            assert config['chain_id'] == 'cosmoshub-4'
            assert 'rpc_endpoint' in config
        
        # Test with missing chain ID
        with patch.dict('os.environ', {}, clear=True):
            config = get_chain_config()
            assert config['chain_id'] == 'cosmoshub-4'  # Default fallback


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 