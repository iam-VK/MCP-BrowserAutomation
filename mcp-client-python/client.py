import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()  # load environment variables from .env

class MCPClient:
    # System prompt to guide Gemini's behavior
    SYSTEM_PROMPT = """
    You are an intelligent AI assistant powered by Gemini, capable of using external tools to complete tasks efficiently.

    Your workflow is as follows:

    1. When a user's request requires external tools, identify the most appropriate tool from the available options.

    2. Use the following exact format to invoke a tool:
    tool_name:{"element":"this would be a reference just for the user to understand", "ref": "s1e6", "param2": "value2"}
    always refer the tool's required input params and provide the required params in the tool call all the time.

    3. If any URLs are mentioned in the user request, always convert them to full URLs in the parameters (e.g., "google.com" becomes "https://www.google.com").

    4. Always follow the tool's required parameters: the required parameters for each tool must be provided without fail, in all cases.

    5. After the tool call, briefly explain in plain language what action you're taking and why.

    6. Wait for the tool's response. Once received, use it as the input for your next action in the workflow.

    7. Repeat tool usage and explanation until the full task is completed.

    8. Once the workflow is fully completed, end your response with:
    THE END

    Additional Rules:
    - Always use correct JSON syntax inside the angle brackets.
    - Never guess tool names or parameters—only use what's available.
    - Be precise, clear, and goal-focused in all steps.
    - If no tool is needed, respond naturally and helpfully as a conversational assistant.
    """


    TOOLS_CONFIG_PATH = Path(__file__).parent.parent / "tools_config.json"
    LOGS_DIR = Path(__file__).parent.parent / "logs"

    def __init__(self):
        # Create logs directory if it doesn't exist
        self.LOGS_DIR.mkdir(exist_ok=True)
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        # Configure Gemini API
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.tools_data = None

    async def _save_tools_config(self, tools_data):
        """Save tools configuration to JSON file"""
        config = {
            "last_updated": datetime.now().isoformat(),
            "tools": tools_data
        }
        with open(self.TOOLS_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"[DEBUG] Tools configuration saved to {self.TOOLS_CONFIG_PATH}")

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools and save to config
        response = await self.session.list_tools()
        tools = response.tools
        self.tools_data = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,
            "parameters": tool.parameters if hasattr(tool, 'parameters') else None,
            "required": tool.required if hasattr(tool, 'required') else None,
            "required_params": tool.inputSchema.get("required", [])
        } for tool in tools]
        
        await self._save_tools_config(self.tools_data)
        print("\nConnected to server with tools:", [tool["name"] for tool in self.tools_data])

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        print("\n[DEBUG] Starting query processing...")

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,
            "required_params": tool.inputSchema.get("required", [])
        } for tool in response.tools]
        print(f"[DEBUG] Available tools: {[t['name'] for t in available_tools]}")

        tools_context = "Available tools:\n" + "\n".join(
            f"- {tool['name']}: {tool['description'], tool['required_params']}" 
            for tool in available_tools
        )
        
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{tools_context}\n\nUser query: {query}"
        print("[DEBUG] Sending query to Gemini with system prompt...")
        
        chat = self.model.start_chat(history=[])
        current_response = chat.send_message(full_prompt, stream=False)
        final_text = []

        while True:
            response_text = current_response.text
            print(f"\n[DEBUG] Raw Gemini response:\n{response_text}\n")
            final_text.append(response_text)

            if "THE END" in response_text:
                print("[DEBUG] Found THE END marker, completing conversation")
                break

            if any(tool['name'] in response_text for tool in available_tools):
                print("[DEBUG] Tool usage detected in response")
                for tool in available_tools:
                    if tool['name'] in response_text:
                        tool_name = tool['name']
                        print(f"[DEBUG] Processing tool: {tool_name}")
                        try:
                            import re
                            args_match = re.search(r'\{.*\}', response_text)
                            tool_args = eval(args_match.group(0)) if args_match else {}
                            print(f"[DEBUG] Extracted args: {tool_args}")
                            
                            print(f"[DEBUG] Executing tool {tool_name}...")
                            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                            result = await self.session.call_tool(tool_name, tool_args)
                            print(f"[DEBUG] Tool result: {result.content}")

                            print("[DEBUG] Getting follow-up response from Gemini...")
                            current_response = chat.send_message(
                                f"Tool {tool_name} returned: {result.content}\nContinue the task or respond with THE END if completed.",
                                stream=False
                            )
                            break  # Break after first tool call to process follow-up
                        except Exception as e:
                            error_msg = f"Error in tool execution: {str(e)}"
                            print(f"[DEBUG] {error_msg}")
                            final_text.append(error_msg)
                            return "\n".join(final_text)
            else:
                print("[DEBUG] No tool calls detected")
                break

        print("[DEBUG] Query processing completed")
        return "\n".join(final_text)

    def _log_interaction(self, query: str, response: str):
        """Log the interaction to a daily log file"""
        timestamp = datetime.now()
        log_file = self.LOGS_DIR / f"chat_log_{timestamp.strftime('%Y-%m-%d')}.txt"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}]\n")
            f.write(f"Query: {query}\n")
            f.write(f"Response: {response}\n")
            f.write("-" * 80 + "\n")

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                # print("\n" + response)
                self._log_interaction(query, response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
                self._log_interaction(query, f"Error: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    MCP_SERVER_PATH = sys.argv[1] if len(sys.argv) > 1 else "../ms-playwright-mcp-server/cli.js"

    # if len(sys.argv) < 2:
        # print("Usage: python client.py <path_to_server_script>")
        # sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(MCP_SERVER_PATH)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
