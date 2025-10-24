"""
Comprehensive System Testing Script
Tests all components of the Agentic RAG Platform
"""

import sys
import os
import json
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

# Test results storage
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def test_python_version():
    """Test Python version"""
    print_header("Testing Python Environment")
    
    version = sys.version_info
    print_info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 10:
        print_success("Python version is compatible (3.10+)")
        test_results["passed"].append("Python version check")
        return True
    else:
        print_error(f"Python version {version.major}.{version.minor} is not compatible. Need 3.10+")
        test_results["failed"].append("Python version check")
        return False

def test_backend_structure():
    """Test backend directory structure"""
    print_header("Testing Backend Structure")
    
    required_dirs = [
        "backend/app",
        "backend/app/api",
        "backend/app/rag",
        "backend/app/agents",
        "backend/app/security",
        "backend/app/analytics"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_success(f"Directory exists: {dir_path}")
        else:
            print_error(f"Directory missing: {dir_path}")
            all_exist = False
    
    if all_exist:
        test_results["passed"].append("Backend structure check")
    else:
        test_results["failed"].append("Backend structure check")
    
    return all_exist

def test_backend_files():
    """Test critical backend files"""
    print_header("Testing Backend Files")
    
    required_files = [
        "backend/app/__init__.py",
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/app/models.py",
        "backend/requirements.txt",
        "backend/.env"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"File exists: {file_path}")
        else:
            print_error(f"File missing: {file_path}")
            all_exist = False
    
    if all_exist:
        test_results["passed"].append("Backend files check")
    else:
        test_results["failed"].append("Backend files check")
    
    return all_exist

def test_frontend_structure():
    """Test frontend directory structure"""
    print_header("Testing Frontend Structure")
    
    required_dirs = [
        "src",
        "src/components",
        "src/pages",
        "src/lib",
        "src/hooks",
        "src/contexts"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_success(f"Directory exists: {dir_path}")
        else:
            print_error(f"Directory missing: {dir_path}")
            all_exist = False
    
    if all_exist:
        test_results["passed"].append("Frontend structure check")
    else:
        test_results["failed"].append("Frontend structure check")
    
    return all_exist

def test_frontend_files():
    """Test critical frontend files"""
    print_header("Testing Frontend Files")
    
    required_files = [
        "src/App.tsx",
        "src/main.tsx",
        "src/index.css",
        "package.json",
        "vite.config.ts",
        "tsconfig.json",
        ".env"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"File exists: {file_path}")
        else:
            print_error(f"File missing: {file_path}")
            all_exist = False
    
    if all_exist:
        test_results["passed"].append("Frontend files check")
    else:
        test_results["failed"].append("Frontend files check")
    
    return all_exist

def test_env_files():
    """Test environment configuration files"""
    print_header("Testing Environment Configuration")
    
    # Check frontend .env
    if Path(".env").exists():
        print_success("Frontend .env file exists")
        with open(".env", "r") as f:
            content = f.read()
            if "VITE_SUPABASE_URL" in content:
                print_success("  - VITE_SUPABASE_URL configured")
            else:
                print_warning("  - VITE_SUPABASE_URL not found")
                test_results["warnings"].append("Frontend VITE_SUPABASE_URL not configured")
            
            if "VITE_SUPABASE_ANON_KEY" in content:
                print_success("  - VITE_SUPABASE_ANON_KEY configured")
            else:
                print_warning("  - VITE_SUPABASE_ANON_KEY not found")
                test_results["warnings"].append("Frontend VITE_SUPABASE_ANON_KEY not configured")
    else:
        print_error("Frontend .env file missing")
        test_results["failed"].append("Frontend .env file")
    
    # Check backend .env
    if Path("backend/.env").exists():
        print_success("Backend .env file exists")
        with open("backend/.env", "r") as f:
            content = f.read()
            required_vars = [
                "SUPABASE_URL",
                "SUPABASE_SERVICE_KEY",
                "OPENAI_API_KEY"
            ]
            for var in required_vars:
                if var in content:
                    print_success(f"  - {var} configured")
                else:
                    print_warning(f"  - {var} not found")
                    test_results["warnings"].append(f"Backend {var} not configured")
    else:
        print_error("Backend .env file missing")
        test_results["failed"].append("Backend .env file")
    
    test_results["passed"].append("Environment files check")
    return True

def test_python_imports():
    """Test if critical Python modules can be imported"""
    print_header("Testing Python Module Imports")
    
    # Change to backend directory
    sys.path.insert(0, str(Path("backend").absolute()))
    
    modules_to_test = [
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic"),
        ("pydantic_settings", "Pydantic Settings"),
    ]
    
    all_imported = True
    for module_name, display_name in modules_to_test:
        try:
            __import__(module_name)
            print_success(f"{display_name} can be imported")
        except ImportError as e:
            print_error(f"{display_name} import failed: {e}")
            all_imported = False
    
    if all_imported:
        test_results["passed"].append("Python imports check")
    else:
        test_results["failed"].append("Python imports check")
        print_warning("Run: cd backend && pip install -r requirements.txt")
    
    return all_imported

def test_backend_syntax():
    """Test backend Python files for syntax errors"""
    print_header("Testing Backend Python Syntax")
    
    python_files = list(Path("backend/app").rglob("*.py"))
    
    syntax_errors = []
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), str(py_file), 'exec')
            print_success(f"Syntax OK: {py_file}")
        except SyntaxError as e:
            print_error(f"Syntax error in {py_file}: {e}")
            syntax_errors.append(str(py_file))
    
    if not syntax_errors:
        test_results["passed"].append("Backend syntax check")
        return True
    else:
        test_results["failed"].append("Backend syntax check")
        return False

def test_package_json():
    """Test package.json configuration"""
    print_header("Testing package.json")
    
    if not Path("package.json").exists():
        print_error("package.json not found")
        test_results["failed"].append("package.json check")
        return False
    
    try:
        with open("package.json", "r") as f:
            pkg = json.load(f)
        
        print_success("package.json is valid JSON")
        
        # Check for required dependencies
        required_deps = ["react", "@supabase/supabase-js", "lucide-react"]
        deps = pkg.get("dependencies", {})
        
        for dep in required_deps:
            if dep in deps:
                print_success(f"  - {dep}: {deps[dep]}")
            else:
                print_warning(f"  - {dep} not found in dependencies")
        
        # Check for scripts
        scripts = pkg.get("scripts", {})
        if "dev" in scripts:
            print_success(f"  - dev script: {scripts['dev']}")
        if "build" in scripts:
            print_success(f"  - build script: {scripts['build']}")
        
        test_results["passed"].append("package.json check")
        return True
    except json.JSONDecodeError as e:
        print_error(f"package.json is invalid: {e}")
        test_results["failed"].append("package.json check")
        return False

def test_requirements_txt():
    """Test requirements.txt"""
    print_header("Testing requirements.txt")
    
    if not Path("backend/requirements.txt").exists():
        print_error("requirements.txt not found")
        test_results["failed"].append("requirements.txt check")
        return False
    
    with open("backend/requirements.txt", "r") as f:
        requirements = f.read()
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "langchain",
        "langgraph",
        "llama-index"
    ]
    
    all_found = True
    for package in required_packages:
        if package in requirements:
            print_success(f"  - {package} listed")
        else:
            print_warning(f"  - {package} not found")
            all_found = False
    
    if all_found:
        test_results["passed"].append("requirements.txt check")
    else:
        test_results["warnings"].append("Some packages missing in requirements.txt")
    
    return True

def print_summary():
    """Print test summary"""
    print_header("Test Summary")
    
    total_tests = len(test_results["passed"]) + len(test_results["failed"])
    
    print(f"\n{Colors.BOLD}Total Tests: {total_tests}{Colors.RESET}")
    print(f"{Colors.GREEN}Passed: {len(test_results['passed'])}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {len(test_results['failed'])}{Colors.RESET}")
    print(f"{Colors.YELLOW}Warnings: {len(test_results['warnings'])}{Colors.RESET}")
    
    if test_results["passed"]:
        print(f"\n{Colors.GREEN}✓ Passed Tests:{Colors.RESET}")
        for test in test_results["passed"]:
            print(f"  - {test}")
    
    if test_results["failed"]:
        print(f"\n{Colors.RED}✗ Failed Tests:{Colors.RESET}")
        for test in test_results["failed"]:
            print(f"  - {test}")
    
    if test_results["warnings"]:
        print(f"\n{Colors.YELLOW}⚠ Warnings:{Colors.RESET}")
        for warning in test_results["warnings"]:
            print(f"  - {warning}")
    
    # Overall status
    print(f"\n{Colors.BOLD}Overall Status:{Colors.RESET}")
    if len(test_results["failed"]) == 0:
        print(f"{Colors.GREEN}✓ All critical tests passed!{Colors.RESET}")
        if len(test_results["warnings"]) > 0:
            print(f"{Colors.YELLOW}⚠ Some warnings need attention{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}✗ Some tests failed. Please fix the issues above.{Colors.RESET}")
        return False

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     Agentic RAG Platform - System Testing Suite           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")
    
    # Run all tests
    test_python_version()
    test_backend_structure()
    test_backend_files()
    test_frontend_structure()
    test_frontend_files()
    test_env_files()
    test_package_json()
    test_requirements_txt()
    test_backend_syntax()
    test_python_imports()
    
    # Print summary
    success = print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
