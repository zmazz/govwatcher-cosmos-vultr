#!/usr/bin/env python3
"""
Enhanced Cosmos Governance Risk & Compliance Co-Pilot
Web application with comprehensive LLM-powered analysis and policy-driven recommendations
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import time
import hashlib

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import structlog

# Import our AI analysis system
from ai_adapters import HybridAIAnalyzer

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Cosmos GRC Co-Pilot",
    description="Governance Risk & Compliance Co-Pilot for Cosmos Ecosystem",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
templates = Jinja2Templates(directory="src/web/templates")

# Initialize AI analyzer
ai_analyzer = HybridAIAnalyzer()

# File paths for persistent storage
ANALYSIS_CACHE_FILE = "/tmp/proposal_analysis_cache.json"
POLICY_CACHE_FILE = "/tmp/organization_policy.json"

# In-memory cache for quick access
analysis_cache = {}
policy_cache = {}

# Default organization policy
DEFAULT_POLICY = {
    "name": "Conservative Strategy",
    "risk_tolerance": "MEDIUM",
    "security_weight": 0.4,
    "economic_weight": 0.3,
    "governance_weight": 0.2,
    "community_weight": 0.1,
    "auto_vote_threshold": 80,
    "voting_criteria": {
        "security_updates": "APPROVE",
        "parameter_changes": "REVIEW",
        "software_upgrades": "APPROVE",
        "community_pool": "REVIEW",
        "validator_changes": "ABSTAIN"
    }
}

def generate_proposal_hash(proposal: Dict[str, Any]) -> str:
    """Generate a unique hash for a proposal to track analysis state."""
    # Create a deterministic hash based on proposal content
    content = f"{proposal.get('chain_id', '')}_{proposal.get('proposal_id', '')}_{proposal.get('title', '')}_{proposal.get('status', '')}"
    return hashlib.md5(content.encode()).hexdigest()

def load_analysis_cache() -> Dict[str, Any]:
    """Load persistent analysis cache from disk."""
    try:
        if os.path.exists(ANALYSIS_CACHE_FILE):
            with open(ANALYSIS_CACHE_FILE, 'r') as f:
                cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached analyses from disk")
                return cache
        else:
            logger.info("No analysis cache file found, starting with empty cache")
            return {}
    except Exception as e:
        logger.error(f"Error loading analysis cache: {e}")
        return {}

def save_analysis_cache(cache: Dict[str, Any]) -> bool:
    """Save analysis cache to disk."""
    try:
        with open(ANALYSIS_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
        logger.info(f"Saved {len(cache)} analyses to cache file")
        return True
    except Exception as e:
        logger.error(f"Error saving analysis cache: {e}")
        return False

def load_governance_data() -> List[Dict[str, Any]]:
    """Load governance data from the updater service."""
    try:
        governance_file = "/tmp/governance_updates.json"
        if os.path.exists(governance_file):
            with open(governance_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} governance updates from file")
                return data
        else:
            logger.warning("Governance updates file not found, using demo data")
            return []
    except Exception as e:
        logger.error(f"Error loading governance data: {e}")
        return []

def get_organization_policy() -> Dict[str, Any]:
    """Get the current organization policy."""
    global policy_cache
    
    # Check if we have a cached policy
    if policy_cache and policy_cache.get("timestamp"):
        # Use cached policy if it's less than 5 minutes old
        cache_age = datetime.utcnow() - datetime.fromisoformat(policy_cache["timestamp"])
        if cache_age < timedelta(minutes=5):
            return policy_cache["policy"]
    
    # Load policy from file or use default
    try:
        if os.path.exists(POLICY_CACHE_FILE):
            with open(POLICY_CACHE_FILE, 'r') as f:
                policy = json.load(f)
                logger.info("Loaded organization policy from file")
        else:
            policy = DEFAULT_POLICY.copy()
            logger.info("Using default organization policy")
        
        # Cache the policy
        policy_cache = {
            "policy": policy,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return policy
        
    except Exception as e:
        logger.error(f"Error loading organization policy: {e}")
        return DEFAULT_POLICY.copy()

def save_organization_policy(policy: Dict[str, Any]) -> bool:
    """Save organization policy to file."""
    try:
        with open(POLICY_CACHE_FILE, 'w') as f:
            json.dump(policy, f, indent=2)
        
        # Update cache
        global policy_cache
        policy_cache = {
            "policy": policy,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("Organization policy saved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error saving organization policy: {e}")
        return False

async def analyze_new_proposals(proposals: List[Dict[str, Any]], policy: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze only new proposals that haven't been analyzed yet, using parallel processing."""
    global analysis_cache
    
    # Identify new proposals that need analysis
    new_proposals = []
    for proposal in proposals:
        proposal_hash = generate_proposal_hash(proposal)
        
        # Check if we already have a fresh analysis
        if proposal_hash in analysis_cache:
            cached_analysis = analysis_cache[proposal_hash]
            # Check if analysis is still valid (less than 24 hours old for active proposals)
            if cached_analysis.get("timestamp"):
                try:
                    analysis_age = datetime.utcnow() - datetime.fromisoformat(cached_analysis["timestamp"])
                    # Keep analysis for 24 hours, or 7 days if proposal is no longer in voting
                    max_age = timedelta(hours=24) if proposal.get("status") == "voting" else timedelta(days=7)
                    
                    if analysis_age < max_age:
                        logger.debug(f"Using cached analysis for proposal {proposal_hash}")
                        continue
                except ValueError:
                    # Invalid timestamp, re-analyze
                    pass
        
        # This proposal needs analysis
        new_proposals.append((proposal_hash, proposal))
        logger.info(f"Proposal {proposal_hash} ({proposal.get('title', 'Unknown')}) needs analysis")
    
    if not new_proposals:
        logger.info("No new proposals to analyze")
        return analysis_cache
    
    logger.info(f"Starting parallel analysis of {len(new_proposals)} new proposals")
    
    # Create analysis tasks for parallel execution
    analysis_tasks = []
    for proposal_hash, proposal in new_proposals:
        task = analyze_single_proposal_with_hash(proposal_hash, proposal, policy)
        analysis_tasks.append(task)
    
    # Execute all analyses in parallel with a reasonable concurrency limit
    semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent API calls
    
    async def limited_analysis(task):
        async with semaphore:
            return await task
    
    # Run analyses in parallel
    try:
        results = await asyncio.gather(*[limited_analysis(task) for task in analysis_tasks], return_exceptions=True)
        
        # Process results
        successful_analyses = 0
        for i, result in enumerate(results):
            proposal_hash, proposal = new_proposals[i]
            
            if isinstance(result, Exception):
                logger.error(f"Analysis failed for proposal {proposal_hash}: {result}")
                # Store a fallback analysis
                analysis_cache[proposal_hash] = {
                    "provider": "error",
                    "recommendation": "ABSTAIN",
                    "confidence": 30,
                    "reasoning": f"Analysis failed: {str(result)}",
                    "risk_assessment": "MEDIUM",
                    "policy_alignment": 50,
                    "economic_impact": "NEUTRAL",
                    "security_implications": "MINIMAL",
                    "timestamp": datetime.utcnow().isoformat(),
                    "analysis_hash": proposal_hash
                }
            else:
                analysis_cache[proposal_hash] = result
                successful_analyses += 1
        
        logger.info(f"Completed parallel analysis: {successful_analyses}/{len(new_proposals)} successful")
        
        # Save updated cache to disk
        save_analysis_cache(analysis_cache)
        
    except Exception as e:
        logger.error(f"Error in parallel analysis: {e}")
    
    return analysis_cache

async def analyze_single_proposal_with_hash(proposal_hash: str, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a single proposal and return the result with hash."""
    try:
        logger.info(f"Analyzing proposal {proposal_hash}: {proposal.get('title', 'Unknown')}")
        
        # Perform AI analysis
        analysis = await ai_analyzer.analyze_proposal(proposal, policy)
        
        # Add metadata
        analysis["timestamp"] = datetime.utcnow().isoformat()
        analysis["analysis_hash"] = proposal_hash
        analysis["proposal_title"] = proposal.get("title", "Unknown")
        analysis["chain_id"] = proposal.get("chain_id", "unknown")
        analysis["chain_name"] = proposal.get("chain_name", "Unknown Chain")
        
        logger.info(f"Analysis completed for {proposal_hash}: {analysis.get('recommendation')} with {analysis.get('confidence')}% confidence")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing proposal {proposal_hash}: {e}")
        raise

async def process_governance_proposals() -> List[Dict[str, Any]]:
    """Process governance proposals with efficient AI analysis."""
    try:
        # Load governance data
        governance_data = load_governance_data()
        if not governance_data:
            logger.warning("No governance data available")
            return []
        
        # Get organization policy
        policy = get_organization_policy()
        
        # Load existing analysis cache
        global analysis_cache
        if not analysis_cache:
            analysis_cache = load_analysis_cache()
        
        # Extract proposals from governance data
        proposals = []
        for update in governance_data:
            proposal = update.get("proposal", {})
            if proposal:
                # Create proposal data structure
                proposal_data = {
                    "id": proposal.get("proposal_id", "unknown"),
                    "chain_id": proposal.get("chain_id", update.get("chain_id", "unknown")),
                    "chain_name": proposal.get("chain_name", update.get("chain_name", "Unknown Chain")),
                    "title": proposal.get("title", "Unknown Proposal"),
                    "description": proposal.get("description", "No description available"),
                    "status": proposal.get("status", "unknown"),
                    "type": proposal.get("type", "unknown"),
                    "voting_end_time": proposal.get("voting_end_time", "Unknown"),
                    "submit_time": proposal.get("submit_time", "Unknown"),
                    "total_deposit": proposal.get("total_deposit", [])
                }
                proposals.append(proposal_data)
        
        # Analyze new proposals efficiently
        await analyze_new_proposals(proposals, policy)
        
        # Build final processed proposals with cached analyses
        processed_proposals = []
        for proposal in proposals:
            proposal_hash = generate_proposal_hash(proposal)
            
            # Get analysis from cache
            analysis = analysis_cache.get(proposal_hash, {
                "provider": "fallback",
                "recommendation": "ABSTAIN",
                "confidence": 30,
                "reasoning": "No analysis available",
                "risk_assessment": "MEDIUM",
                "policy_alignment": 50,
                "economic_impact": "NEUTRAL",
                "security_implications": "MINIMAL",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Create processed proposal
            processed_proposal = {
                **proposal,
                "recommendation": analysis.get("recommendation", "ABSTAIN"),
                "confidence": analysis.get("confidence", 50),
                "reasoning": analysis.get("reasoning", "No analysis available"),
                "risk_assessment": analysis.get("risk_assessment", "MEDIUM"),
                "policy_alignment": analysis.get("policy_alignment", 50),
                "economic_impact": analysis.get("economic_impact", "NEUTRAL"),
                "security_implications": analysis.get("security_implications", "MINIMAL"),
                "analysis_provider": analysis.get("provider", "unknown"),
                "analysis_method": analysis.get("analysis_method", "unknown"),
                "last_analyzed": analysis.get("timestamp", datetime.utcnow().isoformat()),
                "analysis_hash": proposal_hash
            }
            
            processed_proposals.append(processed_proposal)
        
        logger.info(f"Processed {len(processed_proposals)} proposals with cached analyses")
        return processed_proposals
        
    except Exception as e:
        logger.error(f"Error processing governance proposals: {e}")
        return []

# Background task to refresh analyses periodically (but not re-analyze existing ones)
async def refresh_proposal_analyses():
    """Background task to refresh proposal analyses periodically."""
    while True:
        try:
            logger.info("Checking for new proposals to analyze...")
            await process_governance_proposals()
            
            # Clean up old analyses (remove analyses older than 30 days)
            global analysis_cache
            if analysis_cache:
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                old_hashes = []
                
                for proposal_hash, analysis in analysis_cache.items():
                    if analysis.get("timestamp"):
                        try:
                            analysis_date = datetime.fromisoformat(analysis["timestamp"])
                            if analysis_date < cutoff_date:
                                old_hashes.append(proposal_hash)
                        except ValueError:
                            old_hashes.append(proposal_hash)  # Invalid timestamp
                
                if old_hashes:
                    for hash_to_remove in old_hashes:
                        del analysis_cache[hash_to_remove]
                    save_analysis_cache(analysis_cache)
                    logger.info(f"Cleaned up {len(old_hashes)} old analyses")
            
            # Wait 10 minutes before next check
            await asyncio.sleep(600)  # 10 minutes
            
        except Exception as e:
            logger.error(f"Error in background refresh: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with overview."""
    try:
        # Get basic stats
        proposals = await process_governance_proposals()
        policy = get_organization_policy()
        
        # Calculate stats
        total_proposals = len(proposals)
        pending_votes = len([p for p in proposals if p["status"] == "voting"])
        high_confidence = len([p for p in proposals if p["confidence"] >= 80])
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "total_proposals": total_proposals,
            "pending_votes": pending_votes,
            "high_confidence": high_confidence,
            "policy_name": policy.get("name", "Default Policy")
        })
        
    except Exception as e:
        logger.error(f"Error in home route: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Enhanced dashboard with AI-powered analysis."""
    try:
        # Process proposals with AI analysis
        proposals = await process_governance_proposals()
        policy = get_organization_policy()
        
        # Calculate comprehensive stats
        total_proposals = len(proposals)
        pending_votes = len([p for p in proposals if p["status"] == "voting"])
        high_confidence = len([p for p in proposals if p["confidence"] >= 80])
        approve_recommendations = len([p for p in proposals if p["recommendation"] == "APPROVE"])
        reject_recommendations = len([p for p in proposals if p["recommendation"] == "REJECT"])
        abstain_recommendations = len([p for p in proposals if p["recommendation"] == "ABSTAIN"])
        
        # Risk assessment distribution
        high_risk = len([p for p in proposals if p["risk_assessment"] == "HIGH"])
        medium_risk = len([p for p in proposals if p["risk_assessment"] == "MEDIUM"])
        low_risk = len([p for p in proposals if p["risk_assessment"] == "LOW"])
        
        # Provider distribution
        openai_analyses = len([p for p in proposals if p["analysis_provider"] == "openai"])
        groq_analyses = len([p for p in proposals if p["analysis_provider"] == "groq"])
        fallback_analyses = len([p for p in proposals if p["analysis_provider"] in ["rule_based", "fallback"]])
        
        # Mock user data (replace with actual user management)
        mock_user = {
            "name": "GRC Administrator",
            "email": "admin@organization.com",
            "role": "Governance Manager"
        }
        
        # Organization data
        org = {
            "name": "Cosmos Treasury Management",
            "policy": policy.get("name", "Default Policy"),
            "risk_tolerance": policy.get("risk_tolerance", "MEDIUM"),
            "total_assets": "$2.5M",
            "active_chains": len(set([p["chain_id"] for p in proposals]))
        }
        
        logger.info(f"Dashboard loaded with {total_proposals} proposals, {high_confidence} high confidence analyses")
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": mock_user,
            "organization": org,
            "proposals": proposals,
            "proposals_json": json.dumps(proposals, ensure_ascii=True, default=str, separators=(',', ':')),
            "total_proposals": total_proposals,
            "pending_votes": pending_votes,
            "high_confidence": high_confidence,
            "approve_recommendations": approve_recommendations,
            "reject_recommendations": reject_recommendations,
            "abstain_recommendations": abstain_recommendations,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "openai_analyses": openai_analyses,
            "groq_analyses": groq_analyses,
            "fallback_analyses": fallback_analyses,
            "policy": policy
        })
        
    except Exception as e:
        logger.error(f"Error in dashboard route: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings page for policy configuration."""
    try:
        policy = get_organization_policy()
        
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "policy": policy
        })
        
    except Exception as e:
        logger.error(f"Error in settings route: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/settings/update")
async def update_settings(
    request: Request,
    policy_name: str = Form(...),
    risk_tolerance: str = Form(...),
    security_weight: float = Form(...),
    economic_weight: float = Form(...),
    governance_weight: float = Form(...),
    community_weight: float = Form(...),
    auto_vote_threshold: int = Form(...)
):
    """Update organization policy settings."""
    try:
        # Validate weights sum to 1.0
        total_weight = security_weight + economic_weight + governance_weight + community_weight
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(status_code=400, detail="Weights must sum to 1.0")
        
        # Create updated policy
        updated_policy = {
            "name": policy_name,
            "risk_tolerance": risk_tolerance,
            "security_weight": security_weight,
            "economic_weight": economic_weight,
            "governance_weight": governance_weight,
            "community_weight": community_weight,
            "auto_vote_threshold": auto_vote_threshold,
            "voting_criteria": {
                "security_updates": "APPROVE",
                "parameter_changes": "REVIEW",
                "software_upgrades": "APPROVE",
                "community_pool": "REVIEW",
                "validator_changes": "ABSTAIN"
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Save policy
        if save_organization_policy(updated_policy):
            # Clear analysis cache to force re-analysis with new policy
            global analysis_cache
            analysis_cache.clear()
            
            logger.info("Policy updated successfully, analysis cache cleared")
            return JSONResponse({"status": "success", "message": "Policy updated successfully"})
        else:
            raise HTTPException(status_code=500, detail="Failed to save policy")
            
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/proposals")
async def get_proposals():
    """API endpoint to get all proposals with AI analysis."""
    try:
        proposals = await process_governance_proposals()
        
        # Calculate chain statistics
        chain_stats = {}
        for proposal in proposals:
            chain_id = proposal.get("chain_id", "unknown")
            chain_name = proposal.get("chain_name", "Unknown Chain")
            
            if chain_id not in chain_stats:
                chain_stats[chain_id] = {
                    "chain_id": chain_id,
                    "chain_name": chain_name,
                    "proposal_count": 0,
                    "active_proposals": 0,
                    "high_confidence_analyses": 0
                }
            
            chain_stats[chain_id]["proposal_count"] += 1
            
            if proposal.get("status") == "voting" or proposal.get("status") == "2":
                chain_stats[chain_id]["active_proposals"] += 1
            
            if proposal.get("confidence", 0) >= 80:
                chain_stats[chain_id]["high_confidence_analyses"] += 1
        
        return JSONResponse({
            "proposals": proposals, 
            "count": len(proposals),
            "chain_stats": list(chain_stats.values()),
            "total_chains": len(chain_stats)
        })
        
    except Exception as e:
        logger.error(f"Error in proposals API: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/proposals")
async def proposals_redirect():
    """Redirect /proposals to /api/proposals for compatibility."""
    return await get_proposals()

@app.get("/api/proposal/{chain_id}/{proposal_id}/analyze")
async def analyze_specific_proposal(chain_id: str, proposal_id: str):
    """API endpoint to get detailed analysis for a specific proposal."""
    try:
        # Find the proposal
        governance_data = load_governance_data()
        proposal_data = None
        
        for update in governance_data:
            if (update.get("chain_id") == chain_id and 
                update.get("proposal", {}).get("proposal_id") == proposal_id):
                proposal_data = update.get("proposal", {})
                proposal_data["chain_id"] = update.get("chain_id")
                proposal_data["chain_name"] = update.get("chain_name", "Unknown Chain")
                break
        
        if not proposal_data:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Generate proposal hash for cache lookup
        proposal_hash = generate_proposal_hash(proposal_data)
        
        # Load analysis cache if not already loaded
        global analysis_cache
        if not analysis_cache:
            analysis_cache = load_analysis_cache()
        
        # Check if we have cached analysis
        if proposal_hash in analysis_cache:
            cached_analysis = analysis_cache[proposal_hash]
            logger.info(f"Using cached analysis for proposal {proposal_hash}")
            
            return JSONResponse({
                "proposal": proposal_data,
                "analysis": cached_analysis,
                "cache_hit": True,
                "last_analyzed": cached_analysis.get("timestamp", "Unknown")
            })
        
        # If not cached, perform analysis
        policy = get_organization_policy()
        logger.info(f"Performing fresh analysis for proposal {proposal_hash}")
        
        analysis = await analyze_single_proposal_with_hash(proposal_hash, proposal_data, policy)
        
        # Cache the result
        analysis_cache[proposal_hash] = analysis
        save_analysis_cache(analysis_cache)
        
        return JSONResponse({
            "proposal": proposal_data,
            "analysis": analysis,
            "cache_hit": False,
            "last_analyzed": analysis.get("timestamp", "Unknown")
        })
        
    except Exception as e:
        logger.error(f"Error analyzing specific proposal: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/status")
async def status():
    """API endpoint for health check and system status."""
    try:
        # Check AI service availability
        ai_status = {
            "openai": ai_analyzer.openai_adapter.is_available(),
            "groq": ai_analyzer.groq_adapter.is_available(),
            "llama": ai_analyzer.llama_adapter.is_available()
        }
        
        # Get proposal count
        proposals = await process_governance_proposals()
        
        # Calculate cache statistics
        cache_stats = {
            "total_analyses": len(analysis_cache),
            "fresh_analyses": 0,
            "stale_analyses": 0,
            "provider_distribution": {}
        }
        
        if analysis_cache:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            for analysis in analysis_cache.values():
                if analysis.get("timestamp"):
                    try:
                        analysis_time = datetime.fromisoformat(analysis["timestamp"])
                        if analysis_time > cutoff_time:
                            cache_stats["fresh_analyses"] += 1
                        else:
                            cache_stats["stale_analyses"] += 1
                    except ValueError:
                        cache_stats["stale_analyses"] += 1
                
                # Count provider distribution
                provider = analysis.get("provider", "unknown")
                cache_stats["provider_distribution"][provider] = cache_stats["provider_distribution"].get(provider, 0) + 1
        
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "ai_services": ai_status,
            "proposals_count": len(proposals),
            "cache_stats": cache_stats
        })
        
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/api/cache/debug")
async def cache_debug():
    """Debug endpoint to inspect cache contents."""
    try:
        global analysis_cache
        if not analysis_cache:
            analysis_cache = load_analysis_cache()
        
        cache_details = []
        for proposal_hash, analysis in analysis_cache.items():
            cache_details.append({
                "hash": proposal_hash,
                "title": analysis.get("proposal_title", "Unknown"),
                "chain_id": analysis.get("chain_id", "unknown"),
                "chain_name": analysis.get("chain_name", "Unknown Chain"),
                "provider": analysis.get("provider", "unknown"),
                "recommendation": analysis.get("recommendation", "ABSTAIN"),
                "confidence": analysis.get("confidence", 0),
                "timestamp": analysis.get("timestamp", "Unknown"),
                "age_hours": (datetime.utcnow() - datetime.fromisoformat(analysis["timestamp"])).total_seconds() / 3600 if analysis.get("timestamp") else None
            })
        
        # Sort by timestamp (newest first)
        cache_details.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return JSONResponse({
            "cache_size": len(analysis_cache),
            "cache_details": cache_details
        })
        
    except Exception as e:
        logger.error(f"Error in cache debug endpoint: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    try:
        logger.info("Starting Cosmos GRC Co-Pilot...")
        
        # Test AI services
        ai_status = {
            "openai": ai_analyzer.openai_adapter.is_available(),
            "groq": ai_analyzer.groq_adapter.is_available(),
            "llama": ai_analyzer.llama_adapter.is_available()
        }
        
        logger.info(f"AI Services Status: {ai_status}")
        
        # Load initial data
        proposals = await process_governance_proposals()
        logger.info(f"Loaded {len(proposals)} proposals on startup")
        
        # Start background refresh task
        asyncio.create_task(refresh_proposal_analyses())
        
        logger.info("Cosmos GRC Co-Pilot started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 