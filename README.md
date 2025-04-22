# Quickstart Resources

A repository containing both Python client and Node.js server implementations for the Model Context Protocol (MCP), focused on browser automation with Playwright.

## Project Structure

- `mcp-client-python/` - Python-based MCP client implementation
- `ms-playwright-mcp-server/` - Node.js-based Playwright MCP server

## Demo


In this demo, you can see:
* E-commerce flow on Sauce Demo
   - Product selection
   - Cart management
   - Checkout process
* Snapshot-based interactions

## Prerequisites

- Python 3.10 or higher
- Node.js 22 or higher
- npm package manager
- uv (install via `pip install uv`)

## Setup Instructions

### Python Client Setup

```bash
# Navigate to the Python client directory
cd mcp-client-python

# Create and activate a virtual environment using uv
uv venv
source .venv/bin/activate  # For Linux/Mac
.\.venv\Scripts\activate   # For Windows

# Install required packages with uv
uv pip sync
```

### Playwright MCP Server Setup

```bash
# Navigate to the Playwright MCP server directory
cd ms-playwright-mcp-server

# Install dependencies
npm install

# Build the project
npm run build
```

## Environment Configuration

In the `.env` file located inside `mcp-client-python` directory, fill your Gemini API key

```env
GEMINI_API_KEY=your_google_api_key_here
```

## Usage

Run the Python client:
```bash
cd mcp-client-python
python client.py
```

## Available Tools

The server provides various browser automation capabilities through Playwright, organized by interaction type:

### Snapshot-based Interactions
Recommended for most automation tasks due to better reliability:

- **browser_snapshot**
  - Description: Capture accessibility snapshot of the current page, this is better than screenshot
  - Parameters: None

- **browser_click**
  - Description: Perform click on a web page
  - Parameters:
    - `element` (string): Human-readable element description used to obtain permission to interact with the element
    - `ref` (string): Exact target element reference from the page snapshot

- **browser_drag**
  - Description: Perform drag and drop between two elements
  - Parameters:
    - `startElement` (string): Human-readable source element description 
    - `startRef` (string): Exact source element reference
    - `endElement` (string): Human-readable target element description    - `endRef` (string): Exact target element reference

- **browser_hover**
  - Description: Hover over element on page
  - Parameters:
    - `element` (string): Human-readable element description
    - `ref` (string): Exact target element reference

- **browser_type**
  - Description: Type text into editable element
  - Parameters:
    - `element` (string): Human-readable element description
    - `ref` (string): Exact target element reference
    - `text` (string): Text to type
    - `submit` (boolean, optional): Whether to press Enter after
    - `slowly` (boolean, optional): Whether to type one character at a time

- **browser_select_option**
  - Description: Select an option in a dropdown
  - Parameters:
    - `element` (string): Human-readable element description
    - `ref` (string): Exact target element reference
    - `values` (array): Values to select (single or multiple)

### Vision-based Interactions

- **browser_screen_capture**
  - Description: Take a screenshot of the current page
  - Parameters: None

- **browser_screen_move_mouse**
  - Description: Move mouse to a given position
  - Parameters:
    - `element` (string): Human-readable element description
    - `x` (number): X coordinate
    - `y` (number): Y coordinate

- **browser_screen_click**, **browser_screen_drag**, **browser_screen_type**
  (See documentation for detailed parameters)

### Navigation & Tabs

- **browser_navigate**
  - Description: Navigate to a URL
  - Parameters:
    - `url` (string): The URL to navigate to

- **browser_navigate_back**, **browser_navigate_forward**
  - Description: Navigate browser history
  - Parameters: None

- **browser_tab_list**, **browser_tab_new**, **browser_tab_select**, **browser_tab_close**
  (See documentation for detailed parameters)

### Utility Tools

- **browser_console_messages**
  - Description: Returns all console messages
  - Parameters: None

- **browser_file_upload**
  - Description: Upload one or multiple files
  - Parameters:
    - `paths` (array): File paths to upload

- **browser_pdf_save**
  - Description: Save page as PDF
  - Parameters: None

- **browser_wait**, **browser_resize**, **browser_install**, **browser_handle_dialog**
  (See documentation for detailed parameters)

## Resources

- [Model Context Protocol](https://modelcontextprotocol.io)
- [Playwright Documentation](https://playwright.dev)
- [Playwright MCP server](https://github.com/microsoft/playwright-mcp)