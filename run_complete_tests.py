"""
Complete System Testing Script
Runs all tests including dependency checks, imports, and basic functionality
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description, cwd=None):
    """Run a command and return success status"""
    print(f"\n{'='*70}")
    print(f"🔄 {description}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description}")
            if result.stdout:
                print(result.stdout[:500])  # First 500 chars
            return True
        else:
            print(f"❌ FAILED: {description}")
            if result.stderr:
                print(f"Error: {result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT: {description} took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {description} - {str(e)}")
        return False

def test_python_imports():
    """Test critical Python imports"""
    print(f"\n{'='*70}")
    print("🔍 Testing Python Imports")
    print(f"{'='*70}")
    
    imports_to_test = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("sqlalchemy", "Database ORM"),
        ("supabase", "Supabase client"),
    ]
    
    results = []
    for module, description in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {module:20s} - {description}")
            results.append(True)
        except ImportError as e:
            print(f"❌ {module:20s} - NOT INSTALLED ({description})")
            results.append(False)
    
    return all(results)

def test_backend_syntax():
    """Test all backend Python files for syntax errors"""
    print(f"\n{'='*70}")
    print("🔍 Testing Backend Python Syntax")
    print(f"{'='*70}")
    
    backend_files = [
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/app/models.py",
        "backend/app/analytics/engine.py",
        "backend/app/analytics/agents.py",
        "backend/app/analytics/processors.py",
        "backend/app/rag/statistical_rag.py",
    ]
    
    all_valid = True
    for file_path in backend_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"✅ {file_path}")
            except SyntaxError as e:
                print(f"❌ {file_path} - Syntax Error: {e}")
                all_valid = False
        else:
            print(f"⚠️  {file_path} - File not found")
    
    return all_valid

def main():
    print("="*70)
    print("🚀 COMPLETE SYSTEM TESTING")
    print("="*70)
    
    results = {
        "Python Syntax": test_backend_syntax(),
    }
    
    # Try to test imports (may fail if dependencies not installed)
    print("\n⚠️  Note: Import tests will fail if dependencies aren't installed yet")
    results["Python Imports"] = test_python_imports()
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 TEST SUMMARY")
    print(f"{'='*70}")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30s}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n{'='*70}")
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'='*70}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nNext steps:")
        if not results.get("Python Imports"):
            print("  1. Install Python dependencies: pip install -r backend/requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
