"""
Validation script to ensure tool catalog and registry are in sync.

Run this script to verify that:
1. All tools in the catalog are registered
2. All registered tools are in the catalog
3. Tool descriptions match between catalog and registry

Usage:
    python validate_catalog.py
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.registry import ToolRegistry
from app.tools.tool_catalog import get_all_tool_names, get_tool_description
from app.tools import os_ops
from app.tools.web_search import web_search
from app.tools.image_tools import find_image
from app.tools.ppt_tools import create_presentation


def setup_registry():
    """Setup registry with all tools (copied from main.py)."""
    registry = ToolRegistry(safe_mode=False)
    
    # Basic System Controls
    registry.register("set_volume", os_ops.set_volume, get_tool_description("set_volume"), sensitive=False)
    registry.register("get_volume", os_ops.get_volume, get_tool_description("get_volume"), sensitive=False)
    registry.register("set_mouse_speed", os_ops.set_mouse_speed, get_tool_description("set_mouse_speed"), sensitive=True)
    registry.register("set_caps_lock", os_ops.set_caps_lock, get_tool_description("set_caps_lock"), sensitive=False)
    
    # File & Folder Operations
    registry.register("create_note", os_ops.create_and_open_file, get_tool_description("create_note"), sensitive=True)
    registry.register("create_folder", os_ops.create_folder, get_tool_description("create_folder"), sensitive=True)
    registry.register("list_folder", os_ops.list_directory, get_tool_description("list_folder"), sensitive=False)
    registry.register("search_files", os_ops.search_files, get_tool_description("search_files"), sensitive=False)
    
    # App Launching & File Opening
    registry.register("smart_search_and_open", os_ops.smart_search_and_open, get_tool_description("smart_search_and_open"), sensitive=True)
    registry.register("launch_app", os_ops.launch_app, get_tool_description("launch_app"), sensitive=True)
    registry.register("open_url", os_ops.open_url, get_tool_description("open_url"), sensitive=False)
    
    # Web & Research Tools
    registry.register("web_search", web_search, get_tool_description("web_search"), sensitive=False)
    registry.register("find_image", find_image, get_tool_description("find_image"), sensitive=False)
    
    # Document Creation
    registry.register("create_presentation", create_presentation, get_tool_description("create_presentation"), sensitive=True)
    
    return registry


def validate():
    """Validate catalog and registry consistency."""
    print("\n" + "="*60)
    print("Tool Catalog Validation")
    print("="*60 + "\n")
    
    # Initialize registry
    registry = setup_registry()
    
    # Get names from both sources
    catalog_names = set(get_all_tool_names())
    registered_names = set(registry.list_tools().keys())
    
    # Check for mismatches
    missing_from_registry = catalog_names - registered_names
    extra_in_registry = registered_names - catalog_names
    
    print(f"📊 Catalog tools: {len(catalog_names)}")
    print(f"📊 Registered tools: {len(registered_names)}\n")
    
    # Report missing tools
    if missing_from_registry:
        print("❌ Tools in catalog but NOT registered:")
        for tool in sorted(missing_from_registry):
            print(f"   - {tool}")
        print()
    
    # Report extra tools
    if extra_in_registry:
        print("⚠️  Tools registered but NOT in catalog:")
        for tool in sorted(extra_in_registry):
            print(f"   - {tool}")
        print()
    
    # Check description consistency
    print("📝 Checking description consistency...\n")
    description_mismatches = []
    
    for tool_name in catalog_names & registered_names:
        catalog_desc = get_tool_description(tool_name)
        registry_desc = registry.list_tools()[tool_name]
        
        if catalog_desc != registry_desc:
            description_mismatches.append({
                "tool": tool_name,
                "catalog": catalog_desc,
                "registry": registry_desc
            })
    
    if description_mismatches:
        print("⚠️  Description mismatches found:")
        for mismatch in description_mismatches:
            print(f"\n   Tool: {mismatch['tool']}")
            print(f"   Catalog:  {mismatch['catalog']}")
            print(f"   Registry: {mismatch['registry']}")
        print()
    
    # Final verdict
    print("-"*60)
    if not missing_from_registry and not extra_in_registry and not description_mismatches:
        print("✅ SUCCESS: Catalog and registry are perfectly in sync!")
        print("-"*60 + "\n")
        return True
    else:
        print("❌ FAILED: Inconsistencies detected")
        print("-"*60)
        print("\nRecommended actions:")
        if missing_from_registry:
            print("1. Register missing tools in main.py")
        if extra_in_registry:
            print("2. Add extra tools to tool_catalog.py or remove from main.py")
        if description_mismatches:
            print("3. Update descriptions to use get_tool_description() in main.py")
        print()
        return False


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)

