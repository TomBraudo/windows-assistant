"""
Tool Registry - The "Safe Mode" Manager.
Implements an allow-list protocol to prevent arbitrary code execution.
Only registered tools can be executed by the agent.
"""

import os
import inspect
from typing import Dict, Callable, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ToolRegistry:
    """
    Registry that manages allowed tools and enforces safe mode restrictions.
    Implements the allow-list protocol to prevent arbitrary code execution.
    """
    
    def __init__(self, safe_mode: Optional[bool] = None):
        """
        Initialize the tool registry.
        
        Args:
            safe_mode: Whether to require confirmation for sensitive operations.
                      If None, reads from SAFE_MODE environment variable.
        """
        if safe_mode is None:
            safe_mode = os.getenv("SAFE_MODE", "True").lower() == "true"
        
        self.safe_mode = safe_mode
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._sensitive_tools: set = set()
    
    def register(self, name: str, function: Callable, description: str, sensitive: bool = False):
        """Register a tool and auto-generate its JSON schema."""
        # 1. Store the function
        self._tools[name] = {
            "function": function,
            "description": description,
            "sensitive": sensitive
        }
        if sensitive:
            self._sensitive_tools.add(name)
    
    def is_registered(self, tool_name: str) -> bool:
        """
        Check if a tool is registered in the allow-list.
        
        Args:
            tool_name: Name of the tool to check
        
        Returns:
            True if the tool is registered, False otherwise
        """
        return tool_name in self._tools
    
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get tool information by name.
        
        Args:
            tool_name: Name of the tool
        
        Returns:
            Tool dictionary or None if not found
        """
        return self._tools.get(tool_name)
    
    def execute(
        self,
        tool_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a registered tool with safety checks.
        
        Args:
            tool_name: Name of the tool to execute
            *args: Positional arguments for the tool
            **kwargs: Keyword arguments for the tool
        
        Returns:
            Result of tool execution
        
        Raises:
            ValueError: If tool is not registered
            PermissionError: If safe mode blocks execution
        """
        if not self.is_registered(tool_name):
            raise ValueError(
                f"Tool '{tool_name}' is not registered. "
                f"Only registered tools can be executed for safety."
            )
        
        tool_info = self._tools[tool_name]
        
        # Check if confirmation is needed
        if self.safe_mode and tool_info["sensitive"]:
            if not self._request_confirmation(tool_name, tool_info["description"]):
                raise PermissionError(
                    f"Execution of '{tool_name}' was denied by user."
                )
        
        # Execute the tool
        try:
            return tool_info["function"](*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Tool '{tool_name}' execution failed: {e}")
    
    def _request_confirmation(self, tool_name: str, description: str) -> bool:
        """
        Request user confirmation for sensitive operations.
        
        Args:
            tool_name: Name of the tool
            description: Description of what the tool does
        
        Returns:
            True if user confirms, False otherwise
        """
        print(f"\n⚠️  SAFE MODE: Sensitive operation detected")
        print(f"Tool: {tool_name}")
        print(f"Description: {description}")
        response = input("Proceed? (Y/N): ").strip().upper()
        return response == "Y"
    
    def list_tools(self) -> Dict[str, str]:
        """
        Get a list of all registered tools with their descriptions.
        
        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {
            name: info["description"]
            for name, info in self._tools.items()
        }
    
    def get_tool_schema(self) -> list:
        """Generate OpenAI-compatible JSON schemas for all tools."""
        schemas = []
        for name, info in self._tools.items():
            func = info["function"]
            sig = inspect.signature(func)
            
            # Build parameters dict
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                # Map Python types to JSON types
                p_type = "string"
                if param.annotation == int: p_type = "integer"
                elif param.annotation == bool: p_type = "boolean"
                elif param.annotation == float: p_type = "number"
                
                properties[param_name] = {"type": p_type}
                
                # Assume all parameters without defaults are required
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)

            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": info["description"],
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })
        return schemas

