<<<<<<< HEAD
# slack-mcp
# mcp-twelvedata
=======
# TwelveData MCP Server

A Model Context Protocol (MCP) server for financial analysis using the TwelveData API.

## Features
- Real-time stock, crypto, and forex prices.
- Historical time series data.
- Access to 100+ technical indicators.
- Quote details.

## Requirements
- Python 3.12+
- `uv` (recommended)
- TwelveData API Key (Free tier supported)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-twelvedata
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your TWELVE_DATA_API_KEY
   ```

## Usage

Run the server using `uv`:
```bash
uv run mcp-twelvedata
```

Or run with the MCP Inspector for testing:
```bash
npx @modelcontextprotocol/inspector uv run mcp-twelvedata
```

## License
MIT
>>>>>>> 3e7a6bc (chore: initial project setup with uv and fastmcp)
