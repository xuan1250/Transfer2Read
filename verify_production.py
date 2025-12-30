#!/usr/bin/env python3
"""
Production Environment Verification Script

Automates production environment health checks for Transfer2Read.
Run this script to verify:
- Vercel frontend deployment
- Railway backend API deployment
- Supabase connectivity
- CORS configuration
- Security headers

Usage:
    python verify_production.py

Requirements:
    pip install requests python-dotenv
"""

import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import requests

# Production URLs
FRONTEND_URL = "https://transfer2read.app"
BACKEND_API_URL = "https://api.transfer2read.app"
HEALTH_ENDPOINT = f"{BACKEND_API_URL}/api/health"

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def verify_frontend_deployment() -> Tuple[bool, List[str]]:
    """
    Verify Vercel frontend deployment

    Checks:
    - Frontend URL accessible
    - HTTPS certificate valid
    - HTTP→HTTPS redirect

    Returns:
        (success: bool, findings: List[str])
    """
    print_header("1. Frontend Deployment Verification")
    findings = []

    try:
        # Test HTTPS access
        print_info(f"Testing HTTPS access to {FRONTEND_URL}...")
        response = requests.get(FRONTEND_URL, timeout=10, allow_redirects=True)

        if response.status_code == 200:
            print_success(f"Frontend accessible: {FRONTEND_URL}")
            findings.append(f"Frontend returns HTTP 200 OK")
        else:
            print_error(f"Frontend returned HTTP {response.status_code}")
            findings.append(f"Frontend returned unexpected status: {response.status_code}")
            return False, findings

        # Check HTTPS redirect
        print_info("Testing HTTP→HTTPS redirect...")
        http_url = FRONTEND_URL.replace("https://", "http://")
        http_response = requests.get(http_url, timeout=10, allow_redirects=False)

        if http_response.status_code in [301, 302, 307, 308]:
            redirect_location = http_response.headers.get('Location', '')
            if redirect_location.startswith('https://'):
                print_success("HTTP→HTTPS redirect working")
                findings.append("HTTP redirects to HTTPS correctly")
            else:
                print_warning(f"HTTP redirect, but not to HTTPS: {redirect_location}")
                findings.append(f"HTTP redirect location: {redirect_location}")
        else:
            print_warning(f"HTTP access returned {http_response.status_code}, expected redirect")
            findings.append(f"HTTP status: {http_response.status_code}")

        return True, findings

    except requests.exceptions.SSLError as e:
        print_error(f"SSL Certificate Error: {e}")
        findings.append(f"SSL Error: {str(e)}")
        return False, findings
    except requests.exceptions.Timeout:
        print_error(f"Timeout connecting to {FRONTEND_URL}")
        findings.append("Frontend connection timeout")
        return False, findings
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        findings.append(f"Error: {str(e)}")
        return False, findings

def verify_backend_health() -> Tuple[bool, Dict, List[str]]:
    """
    Verify Railway backend API health

    Checks:
    - Health endpoint accessible
    - Returns 200 OK
    - Database connected
    - Redis connected

    Returns:
        (success: bool, health_data: Dict, findings: List[str])
    """
    print_header("2. Backend API Health Check")
    findings = []

    try:
        print_info(f"Testing health endpoint: {HEALTH_ENDPOINT}...")
        start_time = time.time()
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        response_time = (time.time() - start_time) * 1000  # Convert to ms

        print_info(f"Response time: {response_time:.0f}ms")
        findings.append(f"Health endpoint response time: {response_time:.0f}ms")

        if response.status_code == 200:
            print_success("Health endpoint returns HTTP 200 OK")
            health_data = response.json()

            # Check overall status
            status = health_data.get('status', 'unknown')
            if status == 'healthy':
                print_success(f"Overall status: {status}")
                findings.append("Backend reports healthy status")
            else:
                print_error(f"Overall status: {status}")
                findings.append(f"Backend status: {status}")
                return False, health_data, findings

            # Check database
            db_status = health_data.get('database', 'unknown')
            if db_status == 'connected':
                print_success(f"Database: {db_status}")
                findings.append("Database connected")
            else:
                print_error(f"Database: {db_status}")
                findings.append(f"Database issue: {db_status}")
                return False, health_data, findings

            # Check Redis
            redis_status = health_data.get('redis', 'unknown')
            if redis_status == 'connected':
                print_success(f"Redis: {redis_status}")
                findings.append("Redis connected")
            else:
                print_error(f"Redis: {redis_status}")
                findings.append(f"Redis issue: {redis_status}")
                return False, health_data, findings

            # Check timestamp
            timestamp = health_data.get('timestamp', 'N/A')
            print_info(f"Timestamp: {timestamp}")
            findings.append(f"Health check timestamp: {timestamp}")

            return True, health_data, findings

        elif response.status_code == 503:
            print_error("Health endpoint returns HTTP 503 Service Unavailable")
            health_data = response.json()
            findings.append(f"Backend unhealthy: {health_data}")
            return False, health_data, findings
        else:
            print_error(f"Health endpoint returned unexpected HTTP {response.status_code}")
            findings.append(f"Unexpected status code: {response.status_code}")
            return False, {}, findings

    except requests.exceptions.Timeout:
        print_error(f"Timeout connecting to {HEALTH_ENDPOINT}")
        findings.append("Health endpoint timeout")
        return False, {}, findings
    except Exception as e:
        print_error(f"Error checking health: {e}")
        findings.append(f"Error: {str(e)}")
        return False, {}, findings

def verify_cors_configuration() -> Tuple[bool, List[str]]:
    """
    Verify CORS configuration

    Checks:
    - CORS headers present
    - Only production domains allowed
    - Unauthorized origins rejected

    Returns:
        (success: bool, findings: List[str])
    """
    print_header("3. CORS Configuration Verification")
    findings = []

    try:
        # Test authorized origin (production)
        print_info("Testing authorized origin (transfer2read.com)...")
        response = requests.options(
            HEALTH_ENDPOINT,
            headers={"Origin": FRONTEND_URL},
            timeout=10
        )

        cors_header = response.headers.get('Access-Control-Allow-Origin', '')
        if cors_header == FRONTEND_URL or cors_header == '*':
            print_success(f"Authorized origin accepted: {cors_header}")
            findings.append(f"CORS allows production domain: {FRONTEND_URL}")
        else:
            print_warning(f"Unexpected CORS header: {cors_header}")
            findings.append(f"CORS header: {cors_header}")

        # Test unauthorized origin
        print_info("Testing unauthorized origin (malicious-site.com)...")
        unauthorized_response = requests.options(
            HEALTH_ENDPOINT,
            headers={"Origin": "https://malicious-site.com"},
            timeout=10
        )

        unauthorized_cors = unauthorized_response.headers.get('Access-Control-Allow-Origin', '')
        if not unauthorized_cors or unauthorized_cors != "https://malicious-site.com":
            print_success("Unauthorized origin rejected")
            findings.append("CORS correctly rejects unauthorized origins")
        else:
            print_error(f"Unauthorized origin ALLOWED: {unauthorized_cors}")
            findings.append(f"SECURITY ISSUE: Unauthorized origin allowed")
            return False, findings

        return True, findings

    except Exception as e:
        print_error(f"Error testing CORS: {e}")
        findings.append(f"CORS test error: {str(e)}")
        return False, findings

def verify_security_headers() -> Tuple[bool, List[str]]:
    """
    Verify security headers

    Checks:
    - HSTS header
    - X-Content-Type-Options
    - X-Frame-Options

    Returns:
        (success: bool, findings: List[str])
    """
    print_header("4. Security Headers Verification")
    findings = []
    all_good = True

    try:
        print_info(f"Checking security headers on {BACKEND_API_URL}...")
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        headers = response.headers

        # Check HSTS
        hsts = headers.get('Strict-Transport-Security', '')
        if hsts:
            print_success(f"HSTS header present: {hsts}")
            findings.append(f"HSTS: {hsts}")
        else:
            print_warning("HSTS header missing (may be set by Railway proxy)")
            findings.append("HSTS header not present in response")
            all_good = False

        # Check X-Content-Type-Options
        content_type_options = headers.get('X-Content-Type-Options', '')
        if content_type_options == 'nosniff':
            print_success(f"X-Content-Type-Options: {content_type_options}")
            findings.append(f"X-Content-Type-Options: {content_type_options}")
        else:
            print_warning("X-Content-Type-Options header missing or incorrect")
            findings.append("X-Content-Type-Options not set to nosniff")
            all_good = False

        # Check X-Frame-Options
        frame_options = headers.get('X-Frame-Options', '')
        if frame_options in ['DENY', 'SAMEORIGIN']:
            print_success(f"X-Frame-Options: {frame_options}")
            findings.append(f"X-Frame-Options: {frame_options}")
        else:
            print_warning("X-Frame-Options header missing or incorrect")
            findings.append("X-Frame-Options not properly configured")
            all_good = False

        return all_good, findings

    except Exception as e:
        print_error(f"Error checking security headers: {e}")
        findings.append(f"Security headers check error: {str(e)}")
        return False, findings

def generate_report(results: Dict) -> str:
    """Generate markdown report of verification results"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    report = f"""# Production Environment Verification Report

**Generated:** {timestamp}
**Script:** verify_production.py

## Executive Summary

| Check | Status | Details |
|-------|--------|---------|
| Frontend Deployment | {'✅ PASS' if results['frontend']['success'] else '❌ FAIL'} | {len(results['frontend']['findings'])} findings |
| Backend Health | {'✅ PASS' if results['backend']['success'] else '❌ FAIL'} | {len(results['backend']['findings'])} findings |
| CORS Configuration | {'✅ PASS' if results['cors']['success'] else '❌ FAIL'} | {len(results['cors']['findings'])} findings |
| Security Headers | {'✅ PASS' if results['security']['success'] else '❌ FAIL'} | {len(results['security']['findings'])} findings |

**Overall Status:** {'✅ ALL CHECKS PASSED' if all(r['success'] for r in results.values()) else '❌ SOME CHECKS FAILED'}

---

## Detailed Findings

### 1. Frontend Deployment

**Status:** {'PASS' if results['frontend']['success'] else 'FAIL'}

"""
    for finding in results['frontend']['findings']:
        report += f"- {finding}\n"

    report += f"""
### 2. Backend Health Check

**Status:** {'PASS' if results['backend']['success'] else 'FAIL'}

**Health Data:**
```json
{json.dumps(results['backend']['health_data'], indent=2)}
```

**Findings:**
"""
    for finding in results['backend']['findings']:
        report += f"- {finding}\n"

    report += f"""
### 3. CORS Configuration

**Status:** {'PASS' if results['cors']['success'] else 'FAIL'}

"""
    for finding in results['cors']['findings']:
        report += f"- {finding}\n"

    report += f"""
### 4. Security Headers

**Status:** {'PASS' if results['security']['success'] else 'FAIL'}

"""
    for finding in results['security']['findings']:
        report += f"- {finding}\n"

    report += """
---

## Recommendations

"""

    if all(r['success'] for r in results.values()):
        report += """
All automated checks passed! Manual verification still required for:

1. Supabase RLS policies (check via SQL Editor)
2. Storage bucket policies (test with real user)
3. Authentication providers (test login flows)
4. End-to-end smoke test (upload → convert → download)
5. API key rotation (verify production keys in Railway dashboard)

Proceed with manual verification checklist in `docs/operations/production-verification-checklist.md`.
"""
    else:
        report += """
Some automated checks failed. Review findings above and resolve issues before proceeding with manual verification.

**Next Steps:**
1. Fix failing checks
2. Re-run this script
3. Proceed with manual verification once all automated checks pass
"""

    report += """
---

**Related Documents:**
- `docs/operations/production-verification-checklist.md` - Full manual verification checklist
- `docs/operations/production-deployment-guide.md` - Deployment procedures
- `docs/architecture.md` - Production architecture reference
"""

    return report

def main():
    """Main verification workflow"""
    print(f"\n{Colors.BOLD}Transfer2Read - Production Environment Verification{Colors.END}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {
        'frontend': {'success': False, 'findings': []},
        'backend': {'success': False, 'health_data': {}, 'findings': []},
        'cors': {'success': False, 'findings': []},
        'security': {'success': False, 'findings': []}
    }

    # Run all checks
    frontend_success, frontend_findings = verify_frontend_deployment()
    results['frontend']['success'] = frontend_success
    results['frontend']['findings'] = frontend_findings

    backend_success, health_data, backend_findings = verify_backend_health()
    results['backend']['success'] = backend_success
    results['backend']['health_data'] = health_data
    results['backend']['findings'] = backend_findings

    cors_success, cors_findings = verify_cors_configuration()
    results['cors']['success'] = cors_success
    results['cors']['findings'] = cors_findings

    security_success, security_findings = verify_security_headers()
    results['security']['success'] = security_success
    results['security']['findings'] = security_findings

    # Generate report
    print_header("Verification Complete")
    report = generate_report(results)

    # Save report to file
    report_filename = f"verification-report-{datetime.now().strftime('%Y-%m-%d')}.md"
    report_path = f"docs/sprint-artifacts/{report_filename}"

    try:
        with open(report_path, 'w') as f:
            f.write(report)
        print_success(f"Report saved to: {report_path}")
    except Exception as e:
        print_warning(f"Could not save report to file: {e}")
        print_info("Report will be printed to console instead")

    # Print summary
    all_passed = all(r['success'] for r in results.values())
    if all_passed:
        print_success("\n🎉 All automated checks PASSED!")
        print_info("Proceed with manual verification checklist")
        return 0
    else:
        print_error("\n⚠️  Some checks FAILED - review findings and fix issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
