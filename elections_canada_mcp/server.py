"""
Elections Canada MCP Server

This Model Context Protocol (MCP) server provides access to Canadian federal election data from 2021.
The server exposes resources and tools to query and analyze election results by riding, province, and party.

This is a project of ThreeFortyThree Canada (https://threefortythree.ca).

Available tools:
- search_ridings: Search for ridings by name (accent-insensitive)
- get_party_votes: Get vote distribution for a party in a riding
- get_winning_party: Get the party that won a specific riding
- summarize_province_results: Summarize election results for a province
- summarize_national_results: Summarize national election results
- find_closest_ridings: Find the closest ridings by vote margin
- best_and_worst_results: Get best and worst results for a party
"""

import json
import pandas as pd
import os
from typing import Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP
import sys
import logging

# Import utility functions and constants
from elections_canada_mcp.utils import (
    normalize_text,
    get_province_code,
    get_party_code,
    summarize_results
)
from elections_canada_mcp.constants import (
    PARTY_CODE_TO_NAME,
    PROVINCE_CODE_TO_NAME
)

# Configure logging to stderr only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("elections_canada_mcp_server")

# Create an MCP server
mcp = FastMCP("elections_canada_data_and_predictions")

# Path to the data file
DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
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

# Resource to get all ridings
@mcp.resource("elections-canada://ridings")
def get_all_ridings():
    """Get a list of all ridings in the 2021 Canadian federal election."""
    return json.dumps([{
        "ridingCode": riding["ridingCode"],
        "ridingName": riding["ridingName_EN"],
        "province": riding["provCode"]
    } for riding in ELECTION_DATA], indent=2)

# Resource to get a specific riding by code
@mcp.resource("elections-canada://riding/{riding_code}")
def get_riding(riding_code: int):
    """Get detailed information about a specific riding by its code."""
    if riding_code in RIDING_LOOKUP:
        return json.dumps(RIDING_LOOKUP[riding_code], indent=2)
    return json.dumps({"error": f"Riding code {riding_code} not found"}, indent=2)

# Resource to get ridings by province
@mcp.resource("elections-canada://province/{province_code}")
def get_province_ridings(province_code: str):
    """Get all ridings in a specific province by province code."""
    province_code = province_code.upper()
    if province_code in PROVINCE_LOOKUP:
        return json.dumps(PROVINCE_LOOKUP[province_code], indent=2)
    return json.dumps({"error": f"Province code {province_code} not found"}, indent=2)

# Tool to search for ridings by name
@mcp.tool()
def search_ridings(search_term: str):
    """
    Search for ridings by name.
    
    This search is accent-insensitive and ignores spaces and hyphens,
    so searches like 'montreal' will match 'Montréal' and 'st laurent' will match 'Saint-Laurent'.
    """
    if not search_term:
        return json.dumps({"error": "Search term is required"}, indent=2)
    
    normalized_search = normalize_text(search_term)
    
    # Search for ridings with matching names
    matches = []
    for riding in ELECTION_DATA:
        riding_name_en = riding["ridingName_EN"]
        riding_name_fr = riding.get("ridingName_FR", "")
        
        if (normalized_search in normalize_text(riding_name_en) or 
            (riding_name_fr and normalized_search in normalize_text(riding_name_fr))):
            matches.append({
                "ridingCode": riding["ridingCode"],
                "ridingName": riding["ridingName_EN"],
                "province": riding["provCode"],
                "provinceName": PROVINCE_CODE_TO_NAME.get(riding["provCode"], riding["provCode"])
            })
    
    # Sort by province, then by riding name
    matches.sort(key=lambda x: (x["province"], x["ridingName"]))
    
    return json.dumps(matches, indent=2)

# Tool to get party vote distribution for a riding
@mcp.tool()
def get_party_votes(riding_code: int, party_code: Optional[str] = None):
    """Get vote distribution for a specific party in a riding, or all parties if no party code is provided."""
    if riding_code not in RIDING_LOOKUP:
        return json.dumps({"error": f"Riding code {riding_code} not found"}, indent=2)
    
    riding = RIDING_LOOKUP[riding_code]
    
    # If party code is provided, standardize it
    if party_code:
        party_code = get_party_code(party_code)
        if not party_code:
            return json.dumps({"error": f"Invalid party code or name: {party_code}"}, indent=2)
    
    # Filter vote distribution by party if specified
    vote_distribution = riding["voteDistribution"]
    if party_code:
        vote_distribution = [v for v in vote_distribution if v["partyCode"] == party_code]
        if not vote_distribution:
            return json.dumps({"error": f"Party {party_code} not found in riding {riding_code}"}, indent=2)
    
    # Add party names to the results
    for vote in vote_distribution:
        vote["partyName"] = PARTY_CODE_TO_NAME.get(vote["partyCode"], vote["partyCode"])
    
    # Sort by votes (descending)
    vote_distribution.sort(key=lambda x: x["votes"], reverse=True)
    
    return json.dumps({
        "ridingCode": riding["ridingCode"],
        "ridingName": riding["ridingName_EN"],
        "province": riding["provCode"],
        "voteDistribution": vote_distribution
    }, indent=2)

# Tool to get the winning party in a riding
@mcp.tool()
def get_winning_party(riding_code: int):
    """Get the party that won a specific riding."""
    if riding_code not in RIDING_LOOKUP:
        return json.dumps({"error": f"Riding code {riding_code} not found"}, indent=2)
    
    riding = RIDING_LOOKUP[riding_code]
    
    # Find the party with the most votes
    max_votes = 0
    winning_party = None
    
    for party_vote in riding["voteDistribution"]:
        if party_vote["votes"] > max_votes:
            max_votes = party_vote["votes"]
            winning_party = party_vote
    
    if winning_party:
        winning_party["partyName"] = PARTY_CODE_TO_NAME.get(winning_party["partyCode"], winning_party["partyCode"])
        
        return json.dumps({
            "ridingCode": riding["ridingCode"],
            "ridingName": riding["ridingName_EN"],
            "province": riding["provCode"],
            "winningParty": winning_party
        }, indent=2)
    
    return json.dumps({"error": "No winning party found"}, indent=2)

# Tool to summarize election results for a province
@mcp.tool()
def summarize_province_results(province_name_or_code: str):
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
    if not province_code:
        return json.dumps({"error": f"Invalid province name or code: {province_name_or_code}"}, indent=2)
    
    # Get all ridings in the province
    if province_code not in PROVINCE_LOOKUP:
        return json.dumps({"error": f"Province code {province_code} not found"}, indent=2)
    
    province_ridings = PROVINCE_LOOKUP[province_code]
    province_name = PROVINCE_CODE_TO_NAME.get(province_code, province_code)
    
    # Summarize the results
    summary = summarize_results(province_ridings, province_name, province_code)
    
    return json.dumps(summary, indent=2)

# Tool to summarize national election results
@mcp.tool()
def summarize_national_results():
    """
    Summarize national election results for the 2021 Canadian federal election,
    showing seats won, votes received, and vote percentages for each party across Canada.
    
    Returns:
        JSON with summary statistics including seat counts, vote counts, and vote percentages
        for each party at the national level.
    """
    # Summarize the results for all ridings
    summary = summarize_results(ELECTION_DATA, "National")
    
    return json.dumps(summary, indent=2)

# Tool to find the closest ridings by vote margin
@mcp.tool()
def find_closest_ridings(num_results: int = 10, party: Optional[str] = None):
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
    # Validate party code if provided
    party_code = None
    if party:
        party_code = get_party_code(party)
        if not party_code:
            return json.dumps({"error": f"Invalid party name or code: {party}"}, indent=2)
    
    # Calculate margins for all ridings
    ridings_with_margins = []
    
    for riding in ELECTION_DATA:
        # Sort vote distribution by votes (descending)
        vote_dist = sorted(riding["voteDistribution"], key=lambda x: x["votes"], reverse=True)
        
        if len(vote_dist) < 2:
            continue  # Skip ridings with fewer than 2 parties
        
        winner = vote_dist[0]
        runner_up = vote_dist[1]
        
        # Skip if we're filtering by party and this riding wasn't won by that party
        if party_code and winner["partyCode"] != party_code:
            continue
        
        # Calculate margins
        vote_margin = winner["votes"] - runner_up["votes"]
        percent_margin = winner["votePercent"] - runner_up["votePercent"]
        
        ridings_with_margins.append({
            "ridingCode": riding["ridingCode"],
            "ridingName": riding["ridingName_EN"],
            "province": riding["provCode"],
            "provinceName": PROVINCE_CODE_TO_NAME.get(riding["provCode"], riding["provCode"]),
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
            "percentMargin": percent_margin
        })
    
    # Sort by percentage margin (ascending)
    ridings_by_percent = sorted(ridings_with_margins, key=lambda x: x["percentMargin"])[:num_results]
    
    # Sort by vote margin (ascending)
    ridings_by_votes = sorted(ridings_with_margins, key=lambda x: x["voteMargin"])[:num_results]
    
    return json.dumps({
        "byVoteMargin": ridings_by_votes,
        "byPercentMargin": ridings_by_percent
    }, indent=2)

# Tool to get best and worst results for a party
@mcp.tool()
def best_and_worst_results(party: str, num_entries: int = 10):
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
    # Validate party code
    party_code = get_party_code(party)
    if not party_code:
        return json.dumps({"error": f"Invalid party name or code: {party}"}, indent=2)
    
    # Lists to store results
    by_percent = []
    by_margin_win = []
    by_margin_loss = []
    
    for riding in ELECTION_DATA:
        # Get party's result in this riding
        party_result = None
        for vote in riding["voteDistribution"]:
            if vote["partyCode"] == party_code:
                party_result = vote
                break
        
        if not party_result:
            continue  # Party didn't run in this riding
        
        # Sort vote distribution by votes (descending)
        vote_dist = sorted(riding["voteDistribution"], key=lambda x: x["votes"], reverse=True)
        winner = vote_dist[0]
        
        # Add to by_percent list
        by_percent.append({
            "ridingCode": riding["ridingCode"],
            "ridingName": riding["ridingName_EN"],
            "province": riding["provCode"],
            "provinceName": PROVINCE_CODE_TO_NAME.get(riding["provCode"], riding["provCode"]),
            "votes": party_result["votes"],
            "votePercent": party_result["votePercent"]
        })
        
        # Check if party won or lost
        if winner["partyCode"] == party_code:
            # Party won - calculate winning margin
            if len(vote_dist) > 1:
                runner_up = vote_dist[1]
                margin = party_result["votePercent"] - runner_up["votePercent"]
                
                by_margin_win.append({
                    "ridingCode": riding["ridingCode"],
                    "ridingName": riding["ridingName_EN"],
                    "province": riding["provCode"],
                    "provinceName": PROVINCE_CODE_TO_NAME.get(riding["provCode"], riding["provCode"]),
                    "votes": party_result["votes"],
                    "votePercent": party_result["votePercent"],
                    "runnerUp": {
                        "partyCode": runner_up["partyCode"],
                        "partyName": PARTY_CODE_TO_NAME.get(runner_up["partyCode"], runner_up["partyCode"]),
                        "votes": runner_up["votes"],
                        "votePercent": runner_up["votePercent"]
                    },
                    "margin": margin
                })
        else:
            # Party lost - calculate losing margin
            margin = winner["votePercent"] - party_result["votePercent"]
            
            by_margin_loss.append({
                "ridingCode": riding["ridingCode"],
                "ridingName": riding["ridingName_EN"],
                "province": riding["provCode"],
                "provinceName": PROVINCE_CODE_TO_NAME.get(riding["provCode"], riding["provCode"]),
                "votes": party_result["votes"],
                "votePercent": party_result["votePercent"],
                "winner": {
                    "partyCode": winner["partyCode"],
                    "partyName": PARTY_CODE_TO_NAME.get(winner["partyCode"], winner["partyCode"]),
                    "votes": winner["votes"],
                    "votePercent": winner["votePercent"]
                },
                "margin": margin
            })
    
    # Sort the lists
    top_by_percent = sorted(by_percent, key=lambda x: x["votePercent"], reverse=True)[:num_entries]
    worst_by_percent = sorted(by_percent, key=lambda x: x["votePercent"])[:num_entries]
    top_by_margin = sorted(by_margin_win, key=lambda x: x["margin"], reverse=True)[:num_entries]
    worst_by_margin = sorted(by_margin_loss, key=lambda x: x["margin"], reverse=True)[:num_entries]
    
    return json.dumps({
        "topByVotePercent": top_by_percent,
        "topByWinningMargin": top_by_margin,
        "worstByVotePercent": worst_by_percent,
        "worstByLosingMargin": worst_by_margin
    }, indent=2)

def main():
    """Entry point for the elections-canada-mcp command."""
    import mcp.cli
    import sys
    mcp.cli.main(mcp, sys.argv[1:])

if __name__ == "__main__":
    main()