"""Run all tests for the dungeon crawler game."""

import unittest
import sys
import os

# Get the current directory (tests directory)
current_dir = os.path.dirname(__file__)
# Get the parent directory (dungeon-crawler root)
parent_dir = os.path.dirname(current_dir)
# Get the src directory
src_dir = os.path.join(parent_dir, 'src')

# Add src directory to Python path
sys.path.insert(0, src_dir)

# Change to the dungeon-crawler root directory
os.chdir(parent_dir)

def run_individual_tests():
    """Run each test file individually since discovery has issues."""
    test_files = [
        'tests/test_game_engine.py',
        'tests/test_dungeon.py'
    ]
    
    # Add any other test files that exist
    test_dir = os.path.join(parent_dir, 'tests')
    if os.path.exists(test_dir):
        for filename in os.listdir(test_dir):
            if filename.startswith('test_') and filename.endswith('.py') and filename not in ['test_game_engine.py', 'test_dungeon.py']:
                test_files.append(f'tests/{filename}')
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load tests from each file
    for test_file in test_files:
        file_path = os.path.join(parent_dir, test_file)
        if os.path.exists(file_path):
            # Convert file path to module name
            module_name = test_file.replace('/', '.').replace('.py', '')
            try:
                # Load the module
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Load tests from the module
                tests = loader.loadTestsFromModule(module)
                suite.addTest(tests)
            except Exception as e:
                print(f"Warning: Could not load tests from {test_file}: {e}")
    
    return suite

if __name__ == '__main__':
    import importlib.util
    
    # Try to use test discovery first
    try:
        loader = unittest.TestLoader()
        suite = loader.discover('tests', pattern='test_*.py')
        if suite.countTestCases() == 0:
            raise ImportError("No tests found with discovery")
    except (ImportError, AttributeError):
        # Fall back to individual test loading
        print("Test discovery failed, loading tests individually...")
        suite = run_individual_tests()
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    if not result.wasSuccessful():
        sys.exit(1)