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
    # System prompt to guide Gemini's behavior
    SYSTEM_PROMPT = """
    You are an intelligent AI assistant powered by Gemini, capable of using external tools to complete tasks efficiently.

    Your workflow is as follows:

    1. When a user's request requires external tools, identify the most appropriate tool from the available options.

    2. Use the following exact format to invoke a tool:
    <tool_name>:{"param1": "value1", "param2": "value2"}

    3. If any URLs are mentioned in the user request, always convert them to full URLs in the parameters (e.g., "google.com" becomes "https://www.google.com").

    4. After the tool call, briefly explain in plain language what action you're taking and why.

    5. Wait for the tool's response. Once received, use it as the input for your next action in the workflow.

    6. Repeat tool usage and explanation until the full task is completed.

    7. Once the workflow is fully completed, end your response with:
    THE END

    Additional Rules:
    - Always use correct JSON syntax inside the angle brackets.
    - Never guess tool names or parameters—only use what's available.
    - Be precise, clear, and goal-focused in all steps.
    - If no tool is needed, respond naturally and helpfully as a conversational assistant.
    """



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
        print("\n[DEBUG] Starting query processing...")

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]
        print(f"[DEBUG] Available tools: {[t['name'] for t in available_tools]}")

        # Format tools info and combine with system prompt
        tools_context = "Available tools:\n" + "\n".join(
            f"- {tool['name']}: {tool['description']}" 
            for tool in available_tools
        )
        
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{tools_context}\n\nUser query: {query}"
        print("[DEBUG] Sending query to Gemini with system prompt...")
        
        chat = self.model.start_chat(history=[])
        response = chat.send_message(full_prompt, stream=False)
        print("[DEBUG] Received response from Gemini")

        final_text = []
        response_text = response.text
        print(f"\n[DEBUG] Raw Gemini response:\n{response_text}\n")

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
                        result = await self.session.call_tool(tool_name, tool_args)
                        print(f"[DEBUG] Tool result: {result.content}")
                        final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                        print("[DEBUG] Getting follow-up response from Gemini...")
                        follow_up = chat.send_message(
                            f"Tool {tool_name} returned: {result.content}",
                            stream=False
                        )
                        final_text.append(follow_up.text)
                    except Exception as e:
                        print(f"[DEBUG] Error in tool execution: {str(e)}")
                        final_text.append(f"Error processing tool call: {str(e)}")
        else:
            print("[DEBUG] No tool calls detected")
            final_text.append(response_text)

        print("[DEBUG] Query processing completed")
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
