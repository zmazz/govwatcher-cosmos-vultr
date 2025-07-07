"""
Unit tests for data models.
Tests validation, serialization, and model behavior.
"""

import pytest
import time
from decimal import Decimal

from src.models import SubConfig, NewProposal, VoteAdvice, SubscriptionRecord, LogEntry


class TestModels:
    """Test suite for data models."""

    def test_sub_config_valid(self):
        """Test valid SubConfig creation."""
        config = SubConfig(
            email="test@example.com",
            chains=["cosmoshub-4", "osmosis-1"],
            policy_blurbs=["Support security proposals", "Oppose inflation increases"]
        )
        
        assert config.email == "test@example.com"
        assert len(config.chains) == 2
        assert len(config.policy_blurbs) == 2
        assert "cosmoshub-4" in config.chains
        assert "osmosis-1" in config.chains

    def test_new_proposal_valid(self):
        """Test valid NewProposal creation."""
        proposal = NewProposal(
            chain="cosmoshub-4",
            proposal_id=123,
            title="Network Upgrade Proposal",
            description="This proposal upgrades the network to improve security and performance."
        )
        
        assert proposal.chain == "cosmoshub-4"
        assert proposal.proposal_id == 123
        assert proposal.title == "Network Upgrade Proposal"
        assert len(proposal.description) > 0

    def test_vote_advice_valid(self):
        """Test valid VoteAdvice creation."""
        advice = VoteAdvice(
            chain="cosmoshub-4",
            proposal_id=123,
            decision="YES",
            rationale="This proposal improves network security and aligns with user policies.",
            confidence=0.85,
            target_wallet="fetch1234567890abcdef",
            target_email="user@example.com"
        )
        
        assert advice.chain == "cosmoshub-4"
        assert advice.proposal_id == 123
        assert advice.decision == "YES"
        assert advice.confidence == 0.85
        assert advice.target_wallet == "fetch1234567890abcdef"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])