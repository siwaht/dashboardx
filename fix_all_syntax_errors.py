"""
Complete syntax error fix script for all backend files
"""

import os
import sys

def fix_processors_py():
    """Fix backend/app/analytics/processors.py - unterminated triple quote"""
    file_path = "backend/app/analytics/processors.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count triple quotes
        triple_double = content.count('"""')
        
        if triple_double % 2 != 0:
            print(f"✗ {file_path} has unmatched triple quotes ({triple_double} found)")
            print(f"  Adding closing triple quote at end of file...")
            
            # Add closing triple quote if missing
            if not content.rstrip().endswith('"""'):
                content = content.rstrip() + '\n"""\n'
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✓ Fixed {file_path}")
                return True
        else:
            print(f"✓ {file_path} - triple quotes are balanced")
            return False
            
    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}")
        return False

def fix_statistical_rag_py():
    """Fix backend/app/rag/statistical_rag.py - unclosed parenthesis"""
    file_path = "backend/app/rag/statistical_rag.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 755:
            print(f"⚠ {file_path} has fewer than 755 lines")
            return False
        
        # Check line 755 (index 754)
        line_755 = lines[754]
        print(f"Checking {file_path} line 755: {line_755.strip()}")
        
        # Count parentheses in the file
        content = ''.join(lines)
        open_parens = content.count('(')
        close_parens = content.count(')')
        
        if open_parens != close_parens:
            print(f"✗ {file_path} has unmatched parentheses: {open_parens} open, {close_parens} close")
            print(f"  Difference: {open_parens - close_parens}")
            
            # Add missing closing parentheses at the end
            if open_parens > close_parens:
                missing = open_parens - close_parens
                content += ')' * missing + '\n'
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✓ Fixed {file_path} - added {missing} closing parentheses")
                return True
        else:
            print(f"✓ {file_path} - parentheses are balanced")
            return False
            
    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}")
        return False

def test_syntax(file_path):
    """Test Python file syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), file_path, 'exec')
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 70)
    print("COMPREHENSIVE SYNTAX ERROR FIX")
    print("=" * 70)
    print()
    
    fixes_applied = 0
    
    # Fix each problematic file
    print("1. Fixing backend/app/analytics/processors.py...")
    if fix_processors_py():
        fixes_applied += 1
    print()
    
    print("2. Fixing backend/app/rag/statistical_rag.py...")
    if fix_statistical_rag_py():
        fixes_applied += 1
    print()
    
    # Test all fixed files
    print("=" * 70)
    print("SYNTAX VALIDATION")
    print("=" * 70)
    print()
    
    files_to_test = [
        "backend/app/analytics/engine.py",
        "backend/app/analytics/agents.py",
        "backend/app/analytics/processors.py",
        "backend/app/rag/statistical_rag.py"
    ]
    
    all_valid = True
    for file_path in files_to_test:
        if os.path.exists(file_path):
            valid, error = test_syntax(file_path)
            if valid:
                print(f"✓ {file_path} - syntax OK")
            else:
                print(f"✗ {file_path} - syntax error: {error}")
                all_valid = False
        else:
            print(f"⚠ {file_path} - file not found")
    
    print()
    print("=" * 70)
    print(f"SUMMARY")
    print("=" * 70)
    print(f"Fixes applied: {fixes_applied}")
    print(f"All files valid: {'YES' if all_valid else 'NO'}")
    print("=" * 70)
    
    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())
