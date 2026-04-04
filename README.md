# TwelveData MCP Server

A Model Context Protocol (MCP) server for deep financial analysis using the TwelveData API. Designed for AI agents (Claude, Gemini) to perform real-time market research, technical analysis, and instrument correlation.

## 🚀 Features

- **Real-time Data:** Single and batch price fetching for Stocks, Crypto, and Forex.
- **Deep Analysis:** Dedicated tools for Correlation, Beta, RSI, and MACD.
- **Discovery:** Dynamic discovery of 100+ technical indicators and global exchanges.
- **Reliability:** Built-in rate limiting advice and structured logging.

## 🛠 Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended)
- TwelveData API Key ([Get a free key here](https://twelvedata.com))

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lagrot/mcp-twelvedata.git
   cd mcp-twelvedata
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   # Add your TWELVE_DATA_API_KEY to .env
   ```

3. Sync dependencies:
   ```bash
   uv sync
   ```

## 🔌 Integration

### 1. Gemini CLI
To add this server to your Gemini CLI as a persistent tool:
```bash
gemini mcp add twelvedata uv --project /home/count/git/mcp-twelvedata run mcp-twelvedata
```

### 2. Claude Desktop / Claude Code
Add this to your `claude_desktop_config.json` (usually in `~/.config/Claude/` or `%APPDATA%/Claude/`):

```json
{
  "mcpServers": {
    "twelvedata": {
      "command": "uv",
      "args": [
        "--project",
        "/home/count/git/mcp-twelvedata",
        "run",
        "mcp-twelvedata"
      ],
      "env": {
        "TWELVE_DATA_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### 3. Stand-Alone Start (Any Project)
You can start the server manually to inspect it or use it with ad-hoc tools:
```bash
cd /home/count/git/mcp-twelvedata
uv run mcp-twelvedata
```

## 🔍 Examples for AI Agents

- **Batch Prices:** "Get the latest prices for AAPL, MSFT, and BTC/USD."
- **Correlation:** "What is the correlation between TSLA and QQQ over the last 20 days?"
- **Technical Analysis:** "Show me the RSI and MACD for NVIDIA on a 1h interval."
- **Discovery:** "List all supported exchanges for cryptocurrency."

## 🧪 Testing
Run the test suite to verify your setup:
```bash
uv run pytest
```

## 📜 License
MIT
