# Elections Canada MCP Server

This is a Model Context Protocol (MCP) server that provides access to Canadian federal election data from 2021. The server exposes resources and tools to query and analyze election results by riding, province, and party.

## Data Source

The server uses the 2021 Canadian federal election data stored in `datafiles/2021_riding_vote_redistributed_ElectionsCanada.json`.

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Server

To run the server in development mode:

```bash
python server.py
```

### Resources

The server provides the following resources:

- `elections-canada://ridings` - Get a list of all ridings
- `elections-canada://riding/{riding_code}` - Get detailed information about a specific riding
- `elections-canada://province/{province_code}` - Get all ridings in a specific province

### Tools

The server provides the following tools:

- `search_ridings(search_term)` - Search for ridings by name
- `get_party_votes(riding_code, party_code)` - Get vote distribution for a party in a riding
- `get_winning_party(riding_code)` - Get the party that won a specific riding
- `summarize_province_results(province_code)` - Summarize election results for a province

## Examples

### Using with Claude Desktop

1. Install the server in Claude Desktop:
```bash
mcp install server.py
```

2. In Claude, you can then use the server to query election data:
```
What were the election results for Toronto ridings?
```

### Using with the MCP Inspector

Run the server with the MCP Inspector:
```bash
mcp dev server.py
```

This will open a web interface where you can test the server's resources and tools.

## Province Codes

- AB: Alberta
- BC: British Columbia
- MB: Manitoba
- NB: New Brunswick
- NL: Newfoundland and Labrador
- NS: Nova Scotia
- NT: Northwest Territories
- NU: Nunavut
- ON: Ontario
- PE: Prince Edward Island
- QC: Quebec
- SK: Saskatchewan
- YT: Yukon
