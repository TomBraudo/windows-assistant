"""
Tool Registry - Tool Management System.
Implements an allow-list protocol to prevent arbitrary code execution.
Only registered tools can be executed by the agent.
"""

import os
import inspect
from typing import Dict, Callable, Any, Optional
from dotenv import load_dotenv

from app.core.logging_utils import get_logger

# Load environment variables
load_dotenv()


class ToolRegistry:
    """
    Registry that manages allowed tools.
    Implements the allow-list protocol to prevent arbitrary code execution.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Dict[str, Any]] = {}
        self.logger = get_logger("tools", "tools.log")
    
    def register(self, name: str, function: Callable, description: str):
        """Register a tool and auto-generate its JSON schema."""
        # Store the function
        self._tools[name] = {
            "function": function,
            "description": description
        }
    
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
        Execute a registered tool.
        
        Args:
            tool_name: Name of the tool to execute
            *args: Positional arguments for the tool
            **kwargs: Keyword arguments for the tool
        
        Returns:
            Result of tool execution
        
        Raises:
            ValueError: If tool is not registered
        """
        if not self.is_registered(tool_name):
            raise ValueError(
                f"Tool '{tool_name}' is not registered. "
                f"Only registered tools can be executed for safety."
            )
        
        tool_info = self._tools[tool_name]
        
        # Execute the tool
        self.logger.info("Executing tool '%s' with args=%s kwargs=%s", tool_name, args, kwargs)
        try:
            result = tool_info["function"](*args, **kwargs)
            self.logger.info("Tool '%s' completed successfully", tool_name)
            return result
        except Exception as e:
            self.logger.exception("Tool '%s' execution failed: %s", tool_name, e)
            raise RuntimeError(f"Tool '{tool_name}' execution failed: {e}")
    
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

