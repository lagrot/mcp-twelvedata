# TwelveData MCP Server

A Model Context Protocol (MCP) server for financial analysis using the TwelveData API.

## Features
- Real-time stock, crypto, and forex prices.
- Historical time series data.
- Access to 100+ technical indicators.
- Quote details.

## Requirements
- Python 3.12+
- `uv` (recommended for environment and dependency management)
- TwelveData API Key (Free tier supported)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-twelvedata
   ```

2. Set up your Python environment and install dependencies:
   ```bash
   uv sync
   ```

3. Configure your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your TWELVE_DATA_API_KEY
   ```

## Running the Server

### Stand-Alone Mode
To run the MCP server as a standalone service, use `uv` from your project's root directory:
```bash
uv run mcp-twelvedata
```
This command starts the server, making its tools available for clients like Gemini CLI or Claude Desktop.

### Testing with MCP Inspector
For local development and testing, you can use the MCP Inspector:
```bash
npx @modelcontextprotocol/inspector uv run mcp-twelvedata
```

## License
MIT
