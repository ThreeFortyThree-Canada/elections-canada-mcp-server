import json
import os
from typing import Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Elections Canada Data")

# Path to the data file
DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    "datafiles/2021_riding_vote_redistributed_ElectionsCanada.json"
)

# Load the election data
with open(DATA_FILE, 'r') as f:
    ELECTION_DATA = json.load(f)

# Create a lookup dictionary for faster access
RIDING_LOOKUP = {riding["ridingCode"]: riding for riding in ELECTION_DATA}
PROVINCE_LOOKUP = {}
for riding in ELECTION_DATA:
    prov = riding["provCode"]
    if prov not in PROVINCE_LOOKUP:
        PROVINCE_LOOKUP[prov] = []
    PROVINCE_LOOKUP[prov].append(riding)

# Resource to get all ridings
@mcp.resource("elections-canada://ridings")
def get_all_ridings() -> str:
    """Get a list of all ridings in the 2021 Canadian federal election."""
    riding_list = [
        {
            "ridingCode": riding["ridingCode"],
            "ridingName": riding["ridingName_EN"],
            "province": riding["provCode"]
        }
        for riding in ELECTION_DATA
    ]
    return json.dumps(riding_list, indent=2)

# Resource to get a specific riding by code
@mcp.resource("elections-canada://riding/{riding_code}")
def get_riding(riding_code: int) -> str:
    """Get detailed information about a specific riding by its code."""
    if riding_code not in RIDING_LOOKUP:
        return json.dumps({"error": f"Riding code {riding_code} not found"})
    
    return json.dumps(RIDING_LOOKUP[riding_code], indent=2)

# Resource to get ridings by province
@mcp.resource("elections-canada://province/{province_code}")
def get_province_ridings(province_code: str) -> str:
    """Get all ridings in a specific province by province code."""
    province_code = province_code.upper()
    if province_code not in PROVINCE_LOOKUP:
        return json.dumps({"error": f"Province code {province_code} not found"})
    
    return json.dumps(PROVINCE_LOOKUP[province_code], indent=2)

# Tool to search for ridings by name
@mcp.tool()
def search_ridings(search_term: str) -> str:
    """Search for ridings by name."""
    search_term = search_term.lower()
    results = [
        riding for riding in ELECTION_DATA
        if search_term in riding["ridingName_EN"].lower() or search_term in riding["ridingName_FR"].lower()
    ]
    
    if not results:
        return f"No ridings found matching '{search_term}'"
    
    return json.dumps(results, indent=2)

# Tool to get party vote distribution for a riding
@mcp.tool()
def get_party_votes(riding_code: int, party_code: Optional[str] = None) -> str:
    """Get vote distribution for a specific party in a riding, or all parties if no party code is provided."""
    if riding_code not in RIDING_LOOKUP:
        return f"Riding code {riding_code} not found"
    
    riding = RIDING_LOOKUP[riding_code]
    
    if party_code:
        party_code = party_code.upper()
        for party_votes in riding["voteDistribution"]:
            if party_votes["partyCode"] == party_code:
                return json.dumps({
                    "ridingName": riding["ridingName_EN"],
                    "party": party_code,
                    "votes": party_votes["votes"],
                    "votePercent": party_votes["votePercent"]
                }, indent=2)
        
        return f"Party code {party_code} not found in riding {riding_code}"
    
    # Return all parties if no specific party is requested
    return json.dumps({
        "ridingName": riding["ridingName_EN"],
        "voteDistribution": riding["voteDistribution"]
    }, indent=2)

# Tool to get the winning party in a riding
@mcp.tool()
def get_winning_party(riding_code: int) -> str:
    """Get the party that won a specific riding."""
    if riding_code not in RIDING_LOOKUP:
        return f"Riding code {riding_code} not found"
    
    riding = RIDING_LOOKUP[riding_code]
    vote_distribution = riding["voteDistribution"]
    
    if not vote_distribution:
        return f"No vote data available for riding {riding_code}"
    
    # Find the party with the most votes
    winning_party = max(vote_distribution, key=lambda x: x["votes"])
    
    return json.dumps({
        "ridingName": riding["ridingName_EN"],
        "winningParty": winning_party["partyCode"],
        "votes": winning_party["votes"],
        "votePercent": winning_party["votePercent"]
    }, indent=2)

# Tool to summarize election results by province
@mcp.tool()
def summarize_province_results(province_code: str) -> str:
    """Summarize election results for a province, showing seats won by each party."""
    province_code = province_code.upper()
    if province_code not in PROVINCE_LOOKUP:
        return f"Province code {province_code} not found"
    
    ridings = PROVINCE_LOOKUP[province_code]
    party_seats = {}
    
    for riding in ridings:
        vote_distribution = riding["voteDistribution"]
        if not vote_distribution:
            continue
        
        # Find the winning party
        winning_party = max(vote_distribution, key=lambda x: x["votes"])
        party_code = winning_party["partyCode"]
        
        # Count seats by party
        if party_code not in party_seats:
            party_seats[party_code] = 0
        party_seats[party_code] += 1
    
    return json.dumps({
        "province": province_code,
        "totalRidings": len(ridings),
        "seatsByParty": party_seats
    }, indent=2)

if __name__ == "__main__":
    # Run the server in development mode
    import mcp.cli
    import sys
    sys.argv = ["mcp", "dev"]
    mcp.cli.app()
