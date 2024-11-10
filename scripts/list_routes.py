# scripts/list_routes.py

from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app

app = create_app()

print("\nAll Registered Routes:")
print("-" * 80)
for rule in app.url_map.iter_rules():
    print(f"Endpoint: {rule.endpoint}")
    print(f"URL Pattern: {rule.rule}")
    print(f"Methods: {', '.join(rule.methods)}")
    print("-" * 80)