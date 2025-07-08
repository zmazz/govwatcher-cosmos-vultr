#!/usr/bin/env python3
"""
Hackathon Compliance Check Script for Vultr Track
Validates all requirements for the Cosmos Governance Risk & Compliance Co-Pilot
"""

import sys
import os
import json
import re
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class VultrTrackChecker:
    """Validates all Vultr Track requirements for the hackathon submission."""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        # Get project root (one level up from scripts directory)
        self.root_path = Path(__file__).parent.parent
        
    def check(self, requirement: str, condition: bool, details: str = "") -> bool:
        """Check a requirement and record the result."""
        status = "✅ PASS" if condition else "❌ FAIL"
        self.results.append(f"{status} {requirement}")
        if details:
            self.results.append(f"    {details}")
        
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            
        return condition
    
    def check_team_name(self) -> bool:
        """Check if team name contains 'Vultr Track'."""
        # Check for team name in various places
        team_indicators = [
            "Vultr Track",
            "vultr-track", 
            "VultrTrack",
            "VULTR_TRACK"
        ]
        
        # Check README.md
        readme_path = self.root_path / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            for indicator in team_indicators:
                if indicator.lower() in content.lower():
                    return self.check(
                        "Team name contains 'Vultr Track'",
                        True,
                        f"Found '{indicator}' in README.md"
                    )
        
        # Check project title/description
        scratchpad_path = self.root_path / ".cursor" / "scratchpad.md"
        if scratchpad_path.exists():
            content = scratchpad_path.read_text()
            if "vultr track" in content.lower():
                return self.check(
                    "Team name contains 'Vultr Track'",
                    True,
                    "Found 'Vultr Track' in project documentation"
                )
        
        return self.check(
            "Team name contains 'Vultr Track'",
            False,
            "Team name not found in project files"
        )
    
    def check_groq_integration(self) -> bool:
        """Check for Groq API integration."""
        groq_patterns = [
            r"groq",
            r"GROQ",
            r"GroqClient",
            r"groq\.com",
            r"gsk_"  # Groq API key pattern
        ]
        
        # Check source files
        src_path = self.root_path / "src"
        if src_path.exists():
            for py_file in src_path.rglob("*.py"):
                content = py_file.read_text()
                for pattern in groq_patterns:
                    if re.search(pattern, content):
                        return self.check(
                            "Groq API integration present",
                            True,
                            f"Found Groq integration in {py_file.name}"
                        )
        
        # Check requirements.txt
        req_path = self.root_path / "requirements.txt"
        if req_path.exists():
            content = req_path.read_text()
            if "groq" in content.lower():
                return self.check(
                    "Groq API integration present",
                    True,
                    "Found groq dependency in requirements.txt"
                )
        
        return self.check(
            "Groq API integration present",
            False,
            "No Groq integration found"
        )
    
    def check_llama_integration(self) -> bool:
        """Check for Llama model integration."""
        llama_patterns = [
            r"llama",
            r"LLAMA",
            r"LlamaClient",
            r"llama-\d+",
            r"meta-llama"
        ]
        
        # Check source files
        src_path = self.root_path / "src"
        if src_path.exists():
            for py_file in src_path.rglob("*.py"):
                content = py_file.read_text()
                for pattern in llama_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return self.check(
                            "Llama model integration present",
                            True,
                            f"Found Llama integration in {py_file.name}"
                        )
        
        # Check requirements.txt
        req_path = self.root_path / "requirements.txt"
        if req_path.exists():
            content = req_path.read_text()
            if any(pattern in content.lower() for pattern in ["llama", "meta-llama"]):
                return self.check(
                    "Llama model integration present",
                    True,
                    "Found Llama dependency in requirements.txt"
                )
        
        return self.check(
            "Llama model integration present",
            False,
            "No Llama integration found"
        )
    
    def check_vultr_deployment(self) -> bool:
        """Check for Vultr deployment configuration."""
        vultr_indicators = [
            "vultr",
            "VULTR",
            "vultr.com",
            "vultr-api",
            "docker-compose",
            "VPS"
        ]
        
        # Check for Vultr-specific files in new locations
        vultr_files = [
            "infra/docker/docker-compose.yml",
            "infra/vultr/deploy-vultr.sh",
            "deploy.sh",           # Main deployment script
            "docker-compose.yml",  # Legacy location
            "deploy-vultr.sh"      # Legacy location
        ]
        
        found_files = []
        for file_name in vultr_files:
            file_path = self.root_path / file_name
            if file_path.exists():
                found_files.append(file_name)
        
        if found_files:
            return self.check(
                "Vultr deployment configuration present",
                True,
                f"Found Vultr deployment files: {', '.join(found_files)}"
            )
        
        # Check for Vultr mentions in documentation
        doc_locations = [
            "README.md", 
            "docs/MASTER_DEPLOYMENT_GUIDE.md", 
            "docs/DEPLOYMENT_INSTRUCTIONS.md",
            "MASTER_DEPLOYMENT_GUIDE.md"  # Legacy
        ]
        
        for doc_file in doc_locations:
            doc_path = self.root_path / doc_file
            if doc_path.exists():
                content = doc_path.read_text()
                if any(indicator.lower() in content.lower() for indicator in vultr_indicators):
                    return self.check(
                        "Vultr deployment configuration present",
                        True,
                        f"Found Vultr references in {doc_file}"
                    )
        
        return self.check(
            "Vultr deployment configuration present",
            False,
            "No Vultr deployment configuration found"
        )
    
    def check_web_interface(self) -> bool:
        """Check for web-based interface."""
        web_patterns = [
            r"fastapi",
            r"FastAPI",
            r"flask",
            r"Flask",
            r"@app\.route",
            r"@app\.get",
            r"@app\.post",
            r"jinja2",
            r"Jinja2",
            r"templates",
            r"dashboard",
            r"web_ui"
        ]
        
        # Check source files
        src_path = self.root_path / "src"
        if src_path.exists():
            for py_file in src_path.rglob("*.py"):
                content = py_file.read_text()
                for pattern in web_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return self.check(
                            "Web-based interface present",
                            True,
                            f"Found web interface in {py_file.name}"
                        )
        
        # Check requirements.txt
        req_path = self.root_path / "requirements.txt"
        if req_path.exists():
            content = req_path.read_text()
            if any(pattern in content.lower() for pattern in ["fastapi", "flask", "jinja2"]):
                return self.check(
                    "Web-based interface present",
                    True,
                    "Found web framework dependency in requirements.txt"
                )
        
        return self.check(
            "Web-based interface present",
            False,
            "No web interface found"
        )
    
    def check_enterprise_features(self) -> bool:
        """Check for enterprise-ready features."""
        enterprise_patterns = [
            r"enterprise",
            r"Enterprise",
            r"GRC",
            r"governance",
            r"compliance",
            r"risk",
            r"organization",
            r"multi.?tenant",
            r"policy",
            r"template",
            r"dashboard",
            r"auth",
            r"jwt"
        ]
        
        enterprise_found = False
        
        # Check source files
        src_path = self.root_path / "src"
        if src_path.exists():
            for py_file in src_path.rglob("*.py"):
                content = py_file.read_text()
                for pattern in enterprise_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        enterprise_found = True
                        break
                if enterprise_found:
                    break
        
        # Check documentation
        doc_locations = [
            "README.md", 
            ".cursor/scratchpad.md",
            "docs/MASTER_DEPLOYMENT_GUIDE.md",
            "docs/DEPLOYMENT_INSTRUCTIONS.md"
        ]
        
        for doc_file in doc_locations:
            doc_path = self.root_path / doc_file
            if doc_path.exists():
                content = doc_path.read_text()
                if any(re.search(pattern, content, re.IGNORECASE) for pattern in enterprise_patterns):
                    enterprise_found = True
                    break
        
        return self.check(
            "Enterprise features present",
            enterprise_found,
            "Found enterprise/GRC features in codebase" if enterprise_found else "No enterprise features found"
        )
    
    def check_tech_tags(self) -> bool:
        """Check for required technology tags."""
        required_tags = ["Vultr", "Groq", "Llama", "Fetch.ai"]
        found_tags = []
        
        # Check README.md
        readme_path = self.root_path / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            for tag in required_tags:
                if tag.lower() in content.lower():
                    found_tags.append(tag)
        
        # Check scratchpad.md
        scratchpad_path = self.root_path / ".cursor" / "scratchpad.md"
        if scratchpad_path.exists():
            content = scratchpad_path.read_text()
            for tag in required_tags:
                if tag.lower() in content.lower():
                    if tag not in found_tags:
                        found_tags.append(tag)
        
        return self.check(
            "Technology tags present",
            len(found_tags) >= 3,
            f"Found tags: {', '.join(found_tags)} ({len(found_tags)}/4)"
        )
    
    def check_autonomous_agents(self) -> bool:
        """Check for autonomous agent implementation."""
        agent_patterns = [
            r"uagents",
            r"Agent",
            r"@agent",
            r"autonomous",
            r"multi.?agent",
            r"WatcherAgent",
            r"AnalysisAgent",
            r"MailAgent",
            r"SubscriptionAgent"
        ]
        
        # Check source files
        src_path = self.root_path / "src"
        if src_path.exists():
            for py_file in src_path.rglob("*.py"):
                content = py_file.read_text()
                agent_count = 0
                for pattern in agent_patterns:
                    if re.search(pattern, content):
                        agent_count += 1
                
                if agent_count >= 3:
                    return self.check(
                        "Autonomous agents present",
                        True,
                        f"Found agent implementation in {py_file.name}"
                    )
        
        # Check requirements.txt
        req_path = self.root_path / "requirements.txt"
        if req_path.exists():
            content = req_path.read_text()
            if "uagents" in content.lower():
                return self.check(
                    "Autonomous agents present",
                    True,
                    "Found uagents dependency in requirements.txt"
                )
        
        return self.check(
            "Autonomous agents present",
            False,
            "No autonomous agents found"
        )
    
    def check_health_endpoint(self) -> bool:
        """Check for /status or health endpoint."""
        health_patterns = [
            r"/status",
            r"/health",
            r"health_check",
            r"status_check",
            r"@app\.get.*status",
            r"@app\.get.*health"
        ]
        
        # Check source files
        src_path = self.root_path / "src"
        if src_path.exists():
            for py_file in src_path.rglob("*.py"):
                content = py_file.read_text()
                for pattern in health_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return self.check(
                            "Health/status endpoint present",
                            True,
                            f"Found health endpoint in {py_file.name}"
                        )
        
        return self.check(
            "Health/status endpoint present",
            False,
            "No health endpoint found"
        )
    
    def run_all_checks(self) -> Dict[str, any]:
        """Run all compliance checks."""
        print("🔍 Running Vultr Track Compliance Checks...")
        print("=" * 50)
        
        # Required checks
        self.check_team_name()
        self.check_groq_integration()
        self.check_llama_integration()
        self.check_vultr_deployment()
        self.check_web_interface()
        self.check_enterprise_features()
        self.check_tech_tags()
        self.check_autonomous_agents()
        self.check_health_endpoint()
        
        # Print results
        print("\n📊 COMPLIANCE RESULTS:")
        print("=" * 50)
        for result in self.results:
            print(result)
        
        print(f"\n🎯 SUMMARY: {self.passed}/{self.passed + self.failed} checks passed")
        
        if self.failed == 0:
            print("🎉 ALL CHECKS PASSED! Project is compliant with Vultr Track requirements.")
            print("\n📚 Documentation Available:")
            print("   📖 Complete Deployment Guide: MASTER_DEPLOYMENT_GUIDE.md")
            print("   🗄️ Data Model Documentation: DATA_MODEL_DOCUMENTATION.md")
            print("   🔍 Run data model validation: python scripts/validate_data_models.py")
            print("   🚀 Deploy to Vultr: ./deploy.sh vultr deploy")
            return {"status": "PASS", "passed": self.passed, "failed": self.failed}
        else:
            print(f"⚠️  {self.failed} checks failed. Please address these issues.")
            return {"status": "FAIL", "passed": self.passed, "failed": self.failed}


def main():
    """Main function to run compliance checks."""
    checker = VultrTrackChecker()
    result = checker.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main() 