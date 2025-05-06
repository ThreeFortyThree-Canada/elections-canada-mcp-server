# Elections Canada MCP Server

This is a Model Context Protocol (MCP) server that will eventually provide access to querying, in a general purpose way, three data sources:
1. Past Canadian federal election data, starting from 2015 (so 2015, 2019, 2021, 2025)
2. Canadian Census data for each of the ridings, including demographic splits such as age, ethnicity, gender, income, education, religion, etc.
3. Current riding-by-riding projections

This is a project of ThreeFortyThree Canada (https://threefortythree.ca).

Currently, it only provides access to Canadian federal election data from 2021, redistributed to the current federal electoral district boundaries (based on the 2023 Redistribution). The server exposes resources and tools to query and analyze election results by riding, province, and party.

This MCP server powers threefortythree.ca/chat. You can also bring the same insights into a local model.

## Data Source

The server uses the 2021 Canadian federal election data stored in `datafiles/2021_riding_vote_redistributed_ElectionsCanada.json`.

## Installation

### From PyPI

Install the package from PyPI:

```bash
pip install elections_canada_mcp_server
```

### From Source

Install the required dependencies using `uv`:

```bash
uv pip install -e .
```

For development dependencies:

```bash
uv pip install -e ".[dev]"
```

## Usage

### Running the Server

To run the server:

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

- `search_ridings(search_term)` - Search for ridings by name (accent-insensitive)
- `get_party_votes(riding_code, party_code)` - Get vote distribution for a party in a riding
- `get_winning_party(riding_code)` - Get the party that won a specific riding
- `summarize_province_results(province_name_or_code)` - Summarize election results for a province
- `summarize_national_results()` - Summarize national election results
- `find_closest_ridings(num_results, party)` - Find the closest ridings by vote margin
- `best_and_worst_results(party, num_entries)` - Get best and worst results for a party

## Examples

### Using with Claude Desktop

1. Install the package from PyPI:
```bash
pip install elections_canada_mcp_server
```

2. Add the server to Claude Desktop:
   - Open Claude Desktop
   - Go to Settings > MCP Servers
   - Click "Add MCP Server"
   - Enter the path to the installed server module

3. In Claude, you can then use the server to query election data:
```
What were the election results in 2021 in Toronto Centre?
Can you tell me the closest ridings won by the NDP in 2021?
What were the ridings won by the conservative party with the highest % margin of victory in 2021?
```

### Using with the MCP Inspector

Run the server with the MCP Inspector:
```bash
mcp dev server.py
```

This will open a web interface where you can test the server's resources and tools.

## Tool Details

### search_ridings(search_term)
Search for ridings by name. This search is accent-insensitive and ignores spaces and hyphens, so searches like 'montreal' will match 'Montréal' and 'st laurent' will match 'Saint-Laurent'.

### get_party_votes(riding_code, party_code)
Get vote distribution for a specific party in a riding, or all parties if no party code is provided.

### get_winning_party(riding_code)
Get the party that won a specific riding.

### summarize_province_results(province_name_or_code)
Summarize election results for a province, showing seats won, votes received, and vote percentages for each party.

### summarize_national_results()
Summarize national election results for the 2021 Canadian federal election, showing seats won, votes received, and vote percentages for each party across Canada.

### find_closest_ridings(num_results=10, party=None)
Find the closest ridings in the 2021 Canadian federal election based on vote margin. This tool identifies competitive ridings where the difference between the winning party and the runner-up was smallest, making them potential "battleground" ridings.

### best_and_worst_results(party, num_entries=10)
Get the best and worst results for a specific party across all ridings. Returns JSON with four categories:
1. Top ridings by vote percentage
2. Top ridings by winning margin (when party won)
3. Worst ridings by vote percentage
4. Worst ridings by losing margin (when party lost)

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
- QC: Québec
- SK: Saskatchewan
- YT: Yukon

## Party Codes

- LPC: Liberal Party of Canada
- CPC: Conservative Party of Canada
- NDP: New Democratic Party
- BQ: Bloc Québécois
- GPC: Green Party of Canada
- PPC: People's Party of Canada
