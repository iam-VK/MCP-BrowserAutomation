import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        # Configure Gemini API
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.0-flash')

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
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        messages = [{"role": "user", "parts": [query]}]

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Format tools info for Gemini context
        tools_context = "Available tools:\n" + "\n".join(
            f"- {tool['name']}: {tool['description']}" 
            for tool in available_tools
        )
        
        # Initial Gemini API call
        chat = self.model.start_chat(history=[])
        response = chat.send_message(
            f"{tools_context}\n\nUser query: {query}",
            stream=False
        )

        final_text = []
        response_text = response.text

        # Basic tool call detection - you may need to enhance this
        if any(tool['name'] in response_text for tool in available_tools):
            # Extract tool name and args from response
            # This is a simple implementation - you might need more sophisticated parsing
            for tool in available_tools:
                if tool['name'] in response_text:
                    tool_name = tool['name']
                    # Simple extraction of JSON-like args from response
                    try:
                        import re
                        args_match = re.search(r'\{.*\}', response_text)
                        tool_args = eval(args_match.group(0)) if args_match else {}
                        
                        # Execute tool call
                        result = await self.session.call_tool(tool_name, tool_args)
                        final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                        # Continue conversation with tool results
                        follow_up = chat.send_message(
                            f"Tool {tool_name} returned: {result.content}",
                            stream=False
                        )
                        final_text.append(follow_up.text)
                    except Exception as e:
                        final_text.append(f"Error processing tool call: {str(e)}")
        else:
            final_text.append(response_text)

        return "\n".join(final_text)

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
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
