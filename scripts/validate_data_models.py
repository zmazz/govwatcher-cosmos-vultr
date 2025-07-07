#!/usr/bin/env python3
"""
Data Model Validation Script
Validates that all documented models match the actual implementation
"""

import os
import sys
import json
import inspect
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def validate_pydantic_models():
    """Validate Pydantic models from src/models.py"""
    try:
        from models import SubConfig, NewProposal, VoteAdvice, SubscriptionRecord, LogEntry
        
        results = {}
        
        # Validate SubConfig
        try:
            test_config = SubConfig(
                email="test@example.com",
                chains=["cosmoshub-4"],
                policy_blurbs=["Test policy with more than 10 characters"]
            )
            results["SubConfig"] = "✅ VALID"
        except Exception as e:
            results["SubConfig"] = f"❌ ERROR: {str(e)}"
        
        # Validate NewProposal
        try:
            test_proposal = NewProposal(
                chain="cosmoshub-4",
                proposal_id=123,
                title="Test Proposal",
                description="Test description with more than 10 characters"
            )
            results["NewProposal"] = "✅ VALID"
        except Exception as e:
            results["NewProposal"] = f"❌ ERROR: {str(e)}"
        
        # Validate VoteAdvice
        try:
            test_advice = VoteAdvice(
                chain="cosmoshub-4",
                proposal_id=123,
                target_wallet="cosmos1abc123",
                target_email="test@example.com",
                decision="YES",
                rationale="Test rationale with sufficient length to meet requirements",
                confidence=0.85
            )
            results["VoteAdvice"] = "✅ VALID"
        except Exception as e:
            results["VoteAdvice"] = f"❌ ERROR: {str(e)}"
        
        return results
        
    except ImportError as e:
        return {"Models Import": f"❌ IMPORT ERROR: {str(e)}"}

def validate_sqlalchemy_models():
    """Validate SQLAlchemy models from src/web/main.py"""
    try:
        from web.main import Organization, User, Subscription, ProposalHistory, UserPreferences
        from web.main import PaymentMethod, WalletConnection, Base
        
        results = {}
        
        # Check table names
        expected_tables = {
            "Organization": "organizations",
            "User": "users", 
            "Subscription": "subscriptions",
            "ProposalHistory": "proposal_history",
            "UserPreferences": "user_preferences",
            "PaymentMethod": "payment_methods",
            "WalletConnection": "wallet_connections"
        }
        
        for model_name, expected_table in expected_tables.items():
            try:
                model_class = locals()[model_name]
                actual_table = model_class.__tablename__
                if actual_table == expected_table:
                    results[f"{model_name}.__tablename__"] = "✅ VALID"
                else:
                    results[f"{model_name}.__tablename__"] = f"❌ MISMATCH: expected {expected_table}, got {actual_table}"
            except KeyError:
                results[f"{model_name}"] = "❌ MODEL NOT FOUND"
        
        # Check required columns exist
        org_columns = [col.name for col in Organization.__table__.columns]
        required_org_columns = ["id", "name", "domain", "created_at", "policy_template", "is_active"]
        
        for col in required_org_columns:
            if col in org_columns:
                results[f"Organization.{col}"] = "✅ VALID"
            else:
                results[f"Organization.{col}"] = "❌ MISSING COLUMN"
        
        return results
        
    except ImportError as e:
        return {"SQLAlchemy Models Import": f"❌ IMPORT ERROR: {str(e)}"}

def validate_ai_adapters():
    """Validate AI adapter implementations"""
    try:
        from ai_adapters import GroqAdapter, LlamaAdapter, HybridAIAnalyzer
        
        results = {}
        
        # Test Groq adapter initialization
        try:
            groq_adapter = GroqAdapter()
            results["GroqAdapter.__init__"] = "✅ VALID"
            
            # Check required methods
            required_methods = ["analyze_proposal", "is_available"]
            for method in required_methods:
                if hasattr(groq_adapter, method):
                    results[f"GroqAdapter.{method}"] = "✅ VALID"
                else:
                    results[f"GroqAdapter.{method}"] = "❌ MISSING METHOD"
        except Exception as e:
            results["GroqAdapter.__init__"] = f"❌ ERROR: {str(e)}"
        
        # Test Llama adapter initialization
        try:
            llama_adapter = LlamaAdapter()
            results["LlamaAdapter.__init__"] = "✅ VALID"
        except Exception as e:
            results["LlamaAdapter.__init__"] = f"❌ ERROR: {str(e)}"
        
        # Test Hybrid analyzer
        try:
            hybrid_analyzer = HybridAIAnalyzer()
            results["HybridAIAnalyzer.__init__"] = "✅ VALID"
        except Exception as e:
            results["HybridAIAnalyzer.__init__"] = f"❌ ERROR: {str(e)}"
        
        return results
        
    except ImportError as e:
        return {"AI Adapters Import": f"❌ IMPORT ERROR: {str(e)}"}

def validate_agent_models():
    """Validate agent message models"""
    try:
        # Check if uAgents models are available
        from uagents import Model
        
        # Import agent files to check for model definitions
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'onchain'))
        
        try:
            from payment_agent import PaymentRequest, PaymentResponse
            results = {
                "PaymentRequest": "✅ VALID",
                "PaymentResponse": "✅ VALID"
            }
        except ImportError as e:
            results = {"Agent Models": f"❌ IMPORT ERROR: {str(e)}"}
        
        return results
        
    except ImportError as e:
        return {"uAgents Import": f"❌ IMPORT ERROR: {str(e)}"}

def validate_database_schema():
    """Validate database schema matches documentation"""
    try:
        import sqlite3
        from web.main import DATABASE_URL, engine
        
        results = {}
        
        # For SQLite, connect and check schema
        if "sqlite" in DATABASE_URL:
            db_path = DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ["organizations", "users", "subscriptions", "proposal_history", "user_preferences"]
                
                for table in expected_tables:
                    if table in tables:
                        results[f"Table.{table}"] = "✅ EXISTS"
                    else:
                        results[f"Table.{table}"] = "❌ MISSING"
                
                conn.close()
            else:
                results["Database File"] = "❌ NOT FOUND"
        else:
            results["Database Check"] = "⚠️ SKIPPED (PostgreSQL - requires connection)"
        
        return results
        
    except Exception as e:
        return {"Database Schema": f"❌ ERROR: {str(e)}"}

def validate_function_signatures():
    """Validate main function signatures match documentation"""
    try:
        from web.main import app
        
        results = {}
        
        # Check FastAPI routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append(f"{list(route.methods)[0]} {route.path}")
        
        expected_routes = [
            "GET /status",
            "GET /dashboard", 
            "GET /settings",
            "POST /api/auth/login"
        ]
        
        for expected_route in expected_routes:
            if any(expected_route in route for route in routes):
                results[f"Route.{expected_route}"] = "✅ VALID"
            else:
                results[f"Route.{expected_route}"] = "❌ MISSING"
        
        return results
        
    except Exception as e:
        return {"Function Signatures": f"❌ ERROR: {str(e)}"}

def generate_validation_report():
    """Generate comprehensive validation report"""
    
    print("🔍 Data Model Validation Report")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    validation_functions = [
        ("Pydantic Models", validate_pydantic_models),
        ("SQLAlchemy Models", validate_sqlalchemy_models),
        ("AI Adapters", validate_ai_adapters),
        ("Agent Models", validate_agent_models),
        ("Database Schema", validate_database_schema),
        ("Function Signatures", validate_function_signatures)
    ]
    
    all_results = {}
    total_checks = 0
    passed_checks = 0
    
    for section_name, validation_func in validation_functions:
        print(f"📋 {section_name}")
        print("-" * 30)
        
        try:
            results = validation_func()
            all_results[section_name] = results
            
            for check_name, result in results.items():
                print(f"  {check_name:30}: {result}")
                total_checks += 1
                if "✅" in result:
                    passed_checks += 1
                    
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            total_checks += 1
        
        print()
    
    # Summary
    print("📊 Validation Summary")
    print("=" * 30)
    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    print(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%")
    
    if passed_checks == total_checks:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("The implementation matches the documentation.")
    else:
        print(f"\n⚠️  {total_checks - passed_checks} validation(s) failed.")
        print("Please review the implementation or update the documentation.")
    
    return all_results

def export_validation_results(results: Dict[str, Any]):
    """Export validation results to JSON file"""
    output_file = os.path.join(os.path.dirname(__file__), '..', 'validation_results.json')
    
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "validation_results": results,
        "summary": {
            "total_sections": len(results),
            "documentation_link": "DATA_MODEL_DOCUMENTATION.md"
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n💾 Results exported to: {output_file}")

if __name__ == "__main__":
    try:
        results = generate_validation_report()
        export_validation_results(results)
        
        # Exit with error code if any validations failed
        total_checks = sum(len(section_results) for section_results in results.values())
        passed_checks = sum(
            1 for section_results in results.values() 
            for result in section_results.values() 
            if "✅" in str(result)
        )
        
        exit_code = 0 if passed_checks == total_checks else 1
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"❌ Validation script failed: {str(e)}")
        sys.exit(1) 