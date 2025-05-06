import json
import pandas as pd
import os
from typing import Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP
import sys
import logging
import unicodedata
import re

# Configure logging to stderr only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("elections-canada-mcp")

# Create an MCP server
mcp = FastMCP("elections_canada_data_and_predictions")

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

# Create a pandas DataFrame for more complex queries
vote_rows = []
for riding in ELECTION_DATA:
    for party_vote in riding["voteDistribution"]:
        vote_rows.append({
            "ridingCode": riding["ridingCode"],
            "ridingName": riding["ridingName_EN"],
            "province": riding["provCode"],
            "partyCode": party_vote["partyCode"],
            "votes": party_vote["votes"],
            "votePercent": party_vote["votePercent"]
        })
DF = pd.DataFrame(vote_rows)

# Text normalization function for accent-insensitive searching
def normalize_text(text):
    """Normalize text by removing accents, spaces, and hyphens."""
    if not text:
        return ''
    # First remove accents
    without_accents = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
    # Then remove spaces and all types of hyphens/dashes
    return re.sub(r'[\s\-\–\—]', '', without_accents).lower()

# Dictionary to map party names to their codes (centralized)
PARTY_NAME_TO_CODE = {
    # English names
    "liberal": "LPC",
    "liberals": "LPC",
    "liberal party": "LPC",
    "liberal party of canada": "LPC",
    
    "conservative": "CPC", 
    "conservatives": "CPC",
    "conservative party": "CPC",
    "conservative party of canada": "CPC",
    
    "ndp": "NDP",
    "new democratic": "NDP",
    "new democratic party": "NDP",
    
    "bloc": "BQ",
    "bloc quebecois": "BQ",
    "bloc québécois": "BQ",
    
    "green": "GPC",
    "green party": "GPC",
    "green party of canada": "GPC",
    
    "peoples": "PPC",
    "peoples party": "PPC",
    "people's": "PPC",
    "people's party": "PPC",
    "peoples party of canada": "PPC",
    "people's party of canada": "PPC",
    "ppc": "PPC",
    
    # French names
    "parti libéral": "LPC",
    "parti liberal": "LPC",
    "parti libéral du canada": "LPC",
    "parti liberal du canada": "LPC",
    
    "parti conservateur": "CPC",
    "parti conservateur du canada": "CPC",
    
    "nouveau parti démocratique": "NDP",
    "nouveau parti democratique": "NDP",
    
    "bloc québécois": "BQ",
    "bloc quebecois": "BQ",
    
    "parti vert": "GPC",
    "parti vert du canada": "GPC",
    
    "parti populaire": "PPC",
    "parti populaire du canada": "PPC"
}

# Dictionary for full party names (used in documentation and output)
PARTY_CODE_TO_NAME = {
    "LPC": "Liberal Party of Canada",
    "CPC": "Conservative Party of Canada",
    "NDP": "New Democratic Party",
    "BQ": "Bloc Québécois",
    "GPC": "Green Party of Canada",
    "PPC": "People's Party of Canada"
}

# Province name to code mapping
PROVINCE_NAME_TO_CODE = {
    # English names
    "alberta": "AB",
    "british columbia": "BC",
    "bc": "BC",
    "manitoba": "MB",
    "new brunswick": "NB",
    "newfoundland": "NL",
    "newfoundland and labrador": "NL",
    "newfoundland labrador": "NL",
    "northwest territories": "NT",
    "nova scotia": "NS",
    "nunavut": "NU",
    "ontario": "ON",
    "prince edward island": "PE",
    "pei": "PE",
    "quebec": "QC",
    "québec": "QC",
    "saskatchewan": "SK",
    "yukon": "YT",
    
    # French names
    "colombie britannique": "BC",
    "colombie-britannique": "BC",
    "nouveau brunswick": "NB",
    "nouveau-brunswick": "NB",
    "terre neuve": "NL",
    "terre-neuve": "NL",
    "terre neuve et labrador": "NL",
    "terre-neuve-et-labrador": "NL",
    "territoires du nord ouest": "NT",
    "territoires du nord-ouest": "NT",
    "nouvelle écosse": "NS",
    "nouvelle-écosse": "NS",
    "île du prince édouard": "PE",
    "île-du-prince-édouard": "PE",
    "ile du prince edouard": "PE",
    "ile-du-prince-edouard": "PE"
}

# Province code to full name mapping
PROVINCE_CODE_TO_NAME = {
    "AB": "Alberta",
    "BC": "British Columbia",
    "MB": "Manitoba",
    "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador",
    "NT": "Northwest Territories",
    "NS": "Nova Scotia",
    "NU": "Nunavut",
    "ON": "Ontario",
    "PE": "Prince Edward Island",
    "QC": "Québec",
    "SK": "Saskatchewan",
    "YT": "Yukon"
}

# Function to get province code from name or code
def get_province_code(province_name_or_code: str) -> str:
    """
    Convert a province name or code to standardized province code.
    Handles variations in spelling, language, and capitalization.
    
    Args:
        province_name_or_code: Province name or code (e.g., 'Ontario', 'ON', 'Quebec', 'QC')
        
    Returns:
        Standardized province code (e.g., 'ON', 'QC', 'BC')
    """
    if not province_name_or_code:
        return None
        
    # If it's already a valid province code (uppercase)
    province_upper = province_name_or_code.upper()
    if province_upper in PROVINCE_CODE_TO_NAME:
        return province_upper
    
    # Normalize and look up in the mapping
    normalized_name = normalize_text(province_name_or_code)
    for name, code in PROVINCE_NAME_TO_CODE.items():
        if normalized_name == normalize_text(name):
            return code
    
    # If no match found, return the original (uppercased)
    return province_upper

# Function to get party code from name or code
def get_party_code(party_name_or_code: str) -> str:
    """
    Convert a party name or code to standardized party code.
    Handles variations in spelling, language, and capitalization.
    
    Args:
        party_name_or_code: Party name or code (e.g., 'Liberal', 'LPC', 'Conservative', 'CPC')
        
    Returns:
        Standardized party code (e.g., 'LPC', 'CPC', 'NDP')
    """
    if not party_name_or_code:
        return None
        
    # If it's already a valid party code (uppercase)
    party_upper = party_name_or_code.upper()
    if party_upper in PARTY_CODE_TO_NAME:
        return party_upper
    
    # Normalize and look up in the mapping
    normalized_name = normalize_text(party_name_or_code)
    for name, code in PARTY_NAME_TO_CODE.items():
        if normalized_name == normalize_text(name):
            return code
    
    # If no match found, return the original (uppercased)
    return party_upper

# Helper function to summarize election results for a set of ridings
def summarize_results(ridings, region_name=None, region_code=None):
    """
    Summarize election results for a set of ridings, calculating seat counts, 
    vote counts, and vote percentages for each party.
    
    Args:
        ridings: List of riding data to analyze
        region_name: Name of the region (province or "National")
        region_code: Code of the region (province code or None for national)
        
    Returns:
        Dictionary with summary statistics
    """
    party_seats = {}
    party_votes = {}
    total_votes = 0
    
    # Process each riding
    for riding in ridings:
        vote_distribution = riding["voteDistribution"]
        if not vote_distribution:
            continue
        
        # Find the winning party and count seats
        winning_party = max(vote_distribution, key=lambda x: x["votes"])
        party_code = winning_party["partyCode"]
        
        # Count seats by party
        if party_code not in party_seats:
            party_seats[party_code] = 0
        party_seats[party_code] += 1
        
        # Count votes by party
        for party_vote in vote_distribution:
            party = party_vote["partyCode"]
            votes = party_vote["votes"]
            
            if party not in party_votes:
                party_votes[party] = 0
            party_votes[party] += votes
            total_votes += votes
    
    # Calculate vote percentages
    party_percentages = {}
    for party, votes in party_votes.items():
        party_percentages[party] = round((votes / total_votes) * 100, 2) if total_votes > 0 else 0
    
    # Create detailed party results
    party_results = []
    for party in sorted(set(list(party_seats.keys()) + list(party_votes.keys()))):
        party_results.append({
            "partyCode": party,
            "partyName": PARTY_CODE_TO_NAME.get(party, party),
            "seats": party_seats.get(party, 0),
            "votes": party_votes.get(party, 0),
            "votePercent": party_percentages.get(party, 0)
        })
    
    # Sort by seats (descending), then by votes (descending)
    party_results = sorted(
        party_results, 
        key=lambda x: (-x["seats"], -x["votes"])
    )
    
    # Create the result dictionary
    result = {
        "totalRidings": len(ridings),
        "totalVotes": total_votes,
        "partyResults": party_results
    }
    
    # Add region information if provided
    if region_name:
        result["regionName"] = region_name
    if region_code:
        result["regionCode"] = region_code
        
    return result

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
        return json.dumps({"error": f"Riding code {riding_code} not found"}, indent=2)
    
    return json.dumps(RIDING_LOOKUP[riding_code], indent=2)

# Resource to get ridings by province
@mcp.resource("elections-canada://province/{province_code}")
def get_province_ridings(province_code: str) -> str:
    """Get all ridings in a specific province by province code."""
    province_code = province_code.upper()
    if province_code not in PROVINCE_LOOKUP:
        return json.dumps({"error": f"Province code {province_code} not found"}, indent=2)
    
    return json.dumps(PROVINCE_LOOKUP[province_code], indent=2)

# Tool to search for ridings by name
@mcp.tool()
def search_ridings(search_term: str) -> str:
    """Search for ridings by name.
    
    This search is accent-insensitive and ignores spaces and hyphens,
    so searches like 'montreal' will match 'Montréal' and 'st laurent' will match 'Saint-Laurent'.
    """
    # Normalize the search term
    normalized_search_term = normalize_text(search_term)
    
    # Search using normalized text
    results = [
        riding for riding in ELECTION_DATA
        if normalized_search_term in normalize_text(riding["ridingName_EN"]) or 
           normalized_search_term in normalize_text(riding["ridingName_FR"])
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
        party_code = get_party_code(party_code)
        for party_votes in riding["voteDistribution"]:
            if party_votes["partyCode"] == party_code:
                return json.dumps({
                    "ridingName": riding["ridingName_EN"],
                    "party": party_code,
                    "partyName": PARTY_CODE_TO_NAME.get(party_code, party_code),
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
        "partyName": PARTY_CODE_TO_NAME.get(winning_party["partyCode"], winning_party["partyCode"]),
        "votes": winning_party["votes"],
        "votePercent": winning_party["votePercent"]
    }, indent=2)

# Tool to summarize election results for a province
@mcp.tool()
def summarize_province_results(province_name_or_code: str) -> str:
    """
    Summarize election results for a province, showing seats won, votes received,
    and vote percentages for each party.
    
    Args:
        province_name_or_code: Province name or code (e.g., 'Ontario', 'ON', 'Quebec', 'QC')
                              Handles variations in spelling and language.
    
    Returns:
        JSON with summary statistics including seat counts, vote counts, and vote percentages
        for each party in the specified province.
    """
    # Get standardized province code
    province_code = get_province_code(province_name_or_code)
    
    if province_code not in PROVINCE_LOOKUP:
        return json.dumps({
            "error": f"Province '{province_name_or_code}' (code: {province_code}) not found"
        }, indent=2)
    
    # Get the ridings for this province
    ridings = PROVINCE_LOOKUP[province_code]
    
    # Get the province name
    province_name = PROVINCE_CODE_TO_NAME.get(province_code, province_code)
    
    # Summarize the results
    results = summarize_results(ridings, province_name, province_code)
    
    return json.dumps(results, indent=2)

# Tool to summarize national election results
@mcp.tool()
def summarize_national_results() -> str:
    """
    Summarize national election results for the 2021 Canadian federal election,
    showing seats won, votes received, and vote percentages for each party across Canada.
    
    Returns:
        JSON with summary statistics including seat counts, vote counts, and vote percentages
        for each party at the national level.
    """
    # Use all ridings for national results
    results = summarize_results(ELECTION_DATA, "National")
    
    return json.dumps(results, indent=2)

# Tool to find the closest ridings by vote margin
@mcp.tool()
def find_closest_ridings(num_results: int = 10, party: Optional[str] = None) -> str:
    """
    Find the closest ridings in the 2021 Canadian federal election based on vote margin.
    
    This tool identifies competitive ridings where the difference between the winning party
    and the runner-up was smallest, making them potential "battleground" ridings.
    
    Args:
        num_results: Number of results to return (default: 10)
        party: Optional party name or code (e.g., 'Liberal', 'LPC', 'Conservative', 'CPC').
               If provided, only shows close ridings won by this party.
    
    Returns:
        JSON with the closest ridings sorted by both raw vote margin and percentage margin,
        including details about the winner and runner-up in each riding.
    """
    logger.info(f"Finding closest ridings{f' won by {party}' if party else ''}")
    
    # Get standardized party code if provided
    party_code = get_party_code(party) if party else None
    
    # Calculate margins for all ridings
    riding_margins = []
    for riding in ELECTION_DATA:
        riding_code = riding["ridingCode"]
        riding_name = riding["ridingName_EN"]
        province = riding["provCode"]
        province_name = PROVINCE_CODE_TO_NAME.get(province, province)
        
        vote_distribution = riding["voteDistribution"]
        if not vote_distribution or len(vote_distribution) < 2:
            continue  # Skip ridings with insufficient data
        
        # Sort parties by votes to find winner and runner-up
        sorted_parties = sorted(vote_distribution, key=lambda x: x["votes"], reverse=True)
        winner = sorted_parties[0]
        runner_up = sorted_parties[1]
        
        # Skip if we're filtering by party and this riding wasn't won by that party
        if party_code and winner["partyCode"] != party_code:
            continue
            
        # Calculate margins
        vote_margin = winner["votes"] - runner_up["votes"]
        percent_margin = winner["votePercent"] - runner_up["votePercent"]
        
        riding_margins.append({
            "ridingCode": riding_code,
            "ridingName": riding_name,
            "province": province,
            "provinceName": province_name,
            "winner": {
                "partyCode": winner["partyCode"],
                "partyName": PARTY_CODE_TO_NAME.get(winner["partyCode"], winner["partyCode"]),
                "votes": winner["votes"],
                "votePercent": winner["votePercent"]
            },
            "runnerUp": {
                "partyCode": runner_up["partyCode"],
                "partyName": PARTY_CODE_TO_NAME.get(runner_up["partyCode"], runner_up["partyCode"]),
                "votes": runner_up["votes"],
                "votePercent": runner_up["votePercent"]
            },
            "voteMargin": vote_margin,
            "percentMargin": percent_margin,
            "totalVotes": riding.get("validVotes", sum(p["votes"] for p in vote_distribution))
        })
    
    # Sort by percentage margin (closest first)
    by_percent_margin = sorted(riding_margins, key=lambda x: x["percentMargin"])[:num_results]
    
    # Sort by raw vote margin (closest first)
    by_vote_margin = sorted(riding_margins, key=lambda x: x["voteMargin"])[:num_results]
    
    # Create result object
    result = {
        "totalRidingsAnalyzed": len(riding_margins),
        "closestByPercentMargin": by_percent_margin,
        "closestByVoteMargin": by_vote_margin
    }
    
    # Add party filter info if applicable
    if party_code:
        result["partyFilter"] = {
            "partyCode": party_code,
            "partyName": PARTY_CODE_TO_NAME.get(party_code, party_code)
        }
    
    return json.dumps(result, indent=2)

# Tool to get best and worst results for a party
@mcp.tool()
def best_and_worst_results(party: str, num_entries: int = 10) -> str:
    """
    Get the best and worst results for a specific party across all ridings.
    
    Args:
        party: Party name or code (e.g., 'Liberal', 'LPC', 'Conservative', 'CPC')
        num_entries: Number of entries to return for each category (default: 10)
        
    Returns:
        JSON with four categories:
        1. Top ridings by vote percentage
        2. Top ridings by winning margin (when party won)
        3. Worst ridings by vote percentage
        4. Worst ridings by losing margin (when party lost)
    """
    # Get standardized party code
    party_code = get_party_code(party)
    
    logger.info(f"Analyzing results for party: {party_code}")
    
    # Collect all riding results for this party
    party_results = []
    for riding in ELECTION_DATA:
        riding_code = riding["ridingCode"]
        riding_name = riding["ridingName_EN"]
        province = riding["provCode"]
        
        # Find this party's result in the riding
        party_result = None
        for vote in riding["voteDistribution"]:
            if vote["partyCode"] == party_code:
                party_result = vote
                break
        
        if not party_result:
            continue  # Party didn't run in this riding
        
        # Find the winning party's result
        winning_party = max(riding["voteDistribution"], key=lambda x: x["votes"])
        
        # Calculate margin (positive if party won, negative if party lost)
        margin = party_result["votePercent"] - winning_party["votePercent"]
        if party_result["partyCode"] == winning_party["partyCode"]:
            # If this party won, calculate margin to second place
            sorted_results = sorted(riding["voteDistribution"], key=lambda x: x["votes"], reverse=True)
            if len(sorted_results) > 1:  # Ensure there's a second-place party
                second_place = sorted_results[1]
                margin = party_result["votePercent"] - second_place["votePercent"]
            else:
                margin = party_result["votePercent"]  # No opposition
        
        party_results.append({
            "ridingCode": riding_code,
            "ridingName": riding_name,
            "province": province,
            "votePercent": party_result["votePercent"],
            "votes": party_result["votes"],
            "margin": margin,
            "won": party_result["partyCode"] == winning_party["partyCode"]
        })
    
    # Check if we have enough results
    if not party_results:
        return json.dumps({
            "error": f"No results found for party '{party}' (code: {party_code})"
        }, indent=2)
    
    # Adjust num_entries if we don't have enough data
    num_entries = min(num_entries, len(party_results))
    
    # Sort for different categories
    top_by_percent = sorted(party_results, key=lambda x: x["votePercent"], reverse=True)[:num_entries]
    
    # Top by winning margin (only where party won)
    winning_results = [r for r in party_results if r["won"]]
    top_by_margin = sorted(winning_results, key=lambda x: x["margin"], reverse=True)[:num_entries if winning_results else 0]
    
    # Worst by percent
    worst_by_percent = sorted(party_results, key=lambda x: x["votePercent"])[:num_entries]
    
    # Worst by losing margin (only where party lost)
    losing_results = [r for r in party_results if not r["won"]]
    worst_by_margin = sorted(losing_results, key=lambda x: x["margin"])[:num_entries if losing_results else 0]
    
    return json.dumps({
        "party": party_code,
        "partyName": PARTY_CODE_TO_NAME.get(party_code, party_code),
        "totalRidingsContested": len(party_results),
        "ridingsWon": len(winning_results),
        "topByVotePercent": top_by_percent,
        "topByWinningMargin": top_by_margin,
        "worstByVotePercent": worst_by_percent,
        "worstByLosingMargin": worst_by_margin
    }, indent=2)

if __name__ == "__main__":
    import mcp.cli
    import sys
    
    # Configure logging for MCP server (already configured at the top)
    logger.info("Elections Canada MCP Server starting...")
    
    sys.argv = ["mcp", "dev"]
    mcp.cli.app()