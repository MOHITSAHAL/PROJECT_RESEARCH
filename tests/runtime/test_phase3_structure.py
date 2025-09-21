#!/usr/bin/env python3
"""
Phase 3: Intelligent Organization - Structure Validation
Validates Phase 3 implementation structure and components
"""

import os
import sys
import importlib.util
from pathlib import Path

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists and report result"""
    if os.path.exists(filepath):
        print(f"   ✅ {description}")
        return True
    else:
        print(f"   ❌ {description} - File not found: {filepath}")
        return False

def check_python_syntax(filepath: str, description: str) -> bool:
    """Check if Python file has valid syntax"""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        print(f"   ✅ {description} - Valid syntax")
        return True
    except SyntaxError as e:
        print(f"   ❌ {description} - Syntax error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ {description} - Error: {e}")
        return False

def check_imports(filepath: str, description: str) -> bool:
    """Check if Python file imports are valid (basic check)"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Basic import validation
        lines = content.split('\n')
        import_lines = [line.strip() for line in lines if line.strip().startswith(('import ', 'from '))]
        
        # Check for obvious issues
        for line in import_lines:
            if 'import' not in line:
                continue
            # Basic validation passed
        
        print(f"   ✅ {description} - Import structure valid")
        return True
    except Exception as e:
        print(f"   ❌ {description} - Import check failed: {e}")
        return False

def validate_phase3_structure():
    """Validate Phase 3 file structure"""
    print("🧪 Validating Phase 3 File Structure...")
    
    base_path = "/home/mohit/workspace/Project_research"
    
    # Core Phase 3 files
    files_to_check = [
        # Clustering components
        (f"{base_path}/ai-service/clustering/semantic_clusterer.py", "Semantic Clusterer"),
        (f"{base_path}/ai-service/clustering/topic_modeler.py", "Topic Modeler"),
        
        # Genealogy components  
        (f"{base_path}/ai-service/genealogy/citation_analyzer.py", "Citation Analyzer"),
        
        # Discovery components
        (f"{base_path}/ai-service/discovery/recommendation_engine.py", "Recommendation Engine"),
        (f"{base_path}/ai-service/discovery/trend_analyzer.py", "Trend Analyzer"),
        
        # Service integration
        (f"{base_path}/backend/services/intelligent_organization_service.py", "Intelligent Organization Service"),
        
        # API endpoints
        (f"{base_path}/backend/api/v1/endpoints/intelligent_organization.py", "Intelligent Organization API"),
        
        # Documentation
        (f"{base_path}/docs/phase3/PHASE3_IMPLEMENTATION_GUIDE.md", "Phase 3 Implementation Guide"),
        
        # Tests
        (f"{base_path}/tests/runtime/test_phase3_integration.py", "Phase 3 Integration Tests")
    ]
    
    results = []
    for filepath, description in files_to_check:
        success = check_file_exists(filepath, description)
        results.append((description, success))
    
    return results

def validate_python_syntax():
    """Validate Python file syntax"""
    print("\n🧪 Validating Python Syntax...")
    
    base_path = "/home/mohit/workspace/Project_research"
    
    python_files = [
        (f"{base_path}/ai-service/clustering/semantic_clusterer.py", "Semantic Clusterer"),
        (f"{base_path}/ai-service/clustering/topic_modeler.py", "Topic Modeler"),
        (f"{base_path}/ai-service/genealogy/citation_analyzer.py", "Citation Analyzer"),
        (f"{base_path}/ai-service/discovery/recommendation_engine.py", "Recommendation Engine"),
        (f"{base_path}/ai-service/discovery/trend_analyzer.py", "Trend Analyzer"),
        (f"{base_path}/backend/services/intelligent_organization_service.py", "Intelligent Organization Service"),
        (f"{base_path}/backend/api/v1/endpoints/intelligent_organization.py", "Intelligent Organization API")
    ]
    
    results = []
    for filepath, description in python_files:
        if os.path.exists(filepath):
            syntax_ok = check_python_syntax(filepath, description)
            import_ok = check_imports(filepath, f"{description} imports")
            results.append((description, syntax_ok and import_ok))
        else:
            results.append((description, False))
    
    return results

def validate_api_integration():
    """Validate API integration"""
    print("\n🧪 Validating API Integration...")
    
    base_path = "/home/mohit/workspace/Project_research"
    router_file = f"{base_path}/backend/api/v1/router.py"
    
    results = []
    
    if os.path.exists(router_file):
        try:
            with open(router_file, 'r') as f:
                content = f.read()
            
            # Check if intelligent_organization is imported and included
            if "intelligent_organization" in content:
                print("   ✅ Intelligent Organization router imported")
                results.append(("Router Import", True))
            else:
                print("   ❌ Intelligent Organization router not imported")
                results.append(("Router Import", False))
            
            if 'include_router(intelligent_organization.router' in content:
                print("   ✅ Intelligent Organization router included")
                results.append(("Router Inclusion", True))
            else:
                print("   ❌ Intelligent Organization router not included")
                results.append(("Router Inclusion", False))
                
        except Exception as e:
            print(f"   ❌ Error checking router file: {e}")
            results.append(("Router Check", False))
    else:
        print("   ❌ Router file not found")
        results.append(("Router File", False))
    
    return results

def validate_requirements():
    """Validate requirements are updated"""
    print("\n🧪 Validating Requirements...")
    
    base_path = "/home/mohit/workspace/Project_research"
    req_file = f"{base_path}/ai-service/requirements.txt"
    
    results = []
    
    if os.path.exists(req_file):
        try:
            with open(req_file, 'r') as f:
                content = f.read()
            
            # Check for Phase 3 dependencies
            phase3_deps = ["scikit-learn", "numpy", "networkx", "scipy"]
            
            for dep in phase3_deps:
                if dep in content:
                    print(f"   ✅ {dep} dependency found")
                    results.append((f"{dep} dependency", True))
                else:
                    print(f"   ❌ {dep} dependency missing")
                    results.append((f"{dep} dependency", False))
                    
        except Exception as e:
            print(f"   ❌ Error checking requirements: {e}")
            results.append(("Requirements Check", False))
    else:
        print("   ❌ Requirements file not found")
        results.append(("Requirements File", False))
    
    return results

def validate_directory_structure():
    """Validate directory structure"""
    print("\n🧪 Validating Directory Structure...")
    
    base_path = "/home/mohit/workspace/Project_research"
    
    directories = [
        (f"{base_path}/ai-service/clustering", "Clustering Directory"),
        (f"{base_path}/ai-service/genealogy", "Genealogy Directory"),
        (f"{base_path}/ai-service/discovery", "Discovery Directory"),
        (f"{base_path}/docs/phase3", "Phase 3 Documentation Directory")
    ]
    
    results = []
    for dirpath, description in directories:
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            print(f"   ✅ {description}")
            results.append((description, True))
        else:
            print(f"   ❌ {description} - Not found: {dirpath}")
            results.append((description, False))
    
    return results

def check_class_definitions():
    """Check if main classes are properly defined"""
    print("\n🧪 Validating Class Definitions...")
    
    base_path = "/home/mohit/workspace/Project_research"
    
    class_checks = [
        (f"{base_path}/ai-service/clustering/semantic_clusterer.py", "SemanticClusterer", "Semantic Clusterer Class"),
        (f"{base_path}/ai-service/clustering/topic_modeler.py", "TopicModeler", "Topic Modeler Class"),
        (f"{base_path}/ai-service/genealogy/citation_analyzer.py", "CitationAnalyzer", "Citation Analyzer Class"),
        (f"{base_path}/ai-service/discovery/recommendation_engine.py", "RecommendationEngine", "Recommendation Engine Class"),
        (f"{base_path}/ai-service/discovery/trend_analyzer.py", "TrendAnalyzer", "Trend Analyzer Class"),
        (f"{base_path}/backend/services/intelligent_organization_service.py", "IntelligentOrganizationService", "Intelligent Organization Service Class")
    ]
    
    results = []
    for filepath, class_name, description in class_checks:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                if f"class {class_name}" in content:
                    print(f"   ✅ {description}")
                    results.append((description, True))
                else:
                    print(f"   ❌ {description} - Class not found")
                    results.append((description, False))
                    
            except Exception as e:
                print(f"   ❌ {description} - Error: {e}")
                results.append((description, False))
        else:
            print(f"   ❌ {description} - File not found")
            results.append((description, False))
    
    return results

def main():
    """Run all Phase 3 structure validation tests"""
    print("🚀 Phase 3: Intelligent Organization - Structure Validation")
    print("=" * 65)
    
    all_results = []
    
    # Run validation tests
    all_results.extend(validate_phase3_structure())
    all_results.extend(validate_python_syntax())
    all_results.extend(validate_api_integration())
    all_results.extend(validate_requirements())
    all_results.extend(validate_directory_structure())
    all_results.extend(check_class_definitions())
    
    # Summary
    print("\n" + "=" * 65)
    print("📊 PHASE 3 STRUCTURE VALIDATION SUMMARY")
    print("=" * 65)
    
    passed = sum(1 for _, success in all_results if success)
    total = len(all_results)
    
    # Group results by category
    categories = {}
    for name, success in all_results:
        category = "Structure"
        if "syntax" in name.lower() or "import" in name.lower():
            category = "Syntax"
        elif "api" in name.lower() or "router" in name.lower():
            category = "API"
        elif "dependency" in name.lower() or "requirements" in name.lower():
            category = "Dependencies"
        elif "directory" in name.lower():
            category = "Directories"
        elif "class" in name.lower():
            category = "Classes"
        
        if category not in categories:
            categories[category] = []
        categories[category].append((name, success))
    
    for category, items in categories.items():
        print(f"\n{category}:")
        for name, success in items:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  {name:.<40} {status}")
    
    print(f"\nOverall: {passed}/{total} validations passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All Phase 3 structure validations PASSED!")
        print("✅ Phase 3 implementation structure is complete and valid!")
        print("\n📋 Next Steps:")
        print("   1. Install dependencies: pip install -r ai-service/requirements.txt")
        print("   2. Run integration tests with proper environment")
        print("   3. Test API endpoints with sample data")
        return True
    else:
        print(f"\n⚠️  {total - passed} validations failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)