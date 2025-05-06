"""
Utility functions for the Elections Canada MCP Server.

This module contains helper functions for data processing and analysis.
"""

import unicodedata
import re
from typing import Dict, List, Optional, Union, Any
from .constants import (
    PARTY_NAME_TO_CODE,
    PROVINCE_NAME_TO_CODE,
    PARTY_CODE_TO_NAME,
    PROVINCE_CODE_TO_NAME
)

def normalize_text(text: str) -> str:
    """Normalize text by removing accents, spaces, and hyphens."""
    if not text:
        return ''
    # First remove accents
    without_accents = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
    # Then remove spaces and all types of hyphens/dashes
    return re.sub(r'[\s\-\–\—]', '', without_accents).lower()

def get_province_code(province_name_or_code: str) -> Optional[str]:
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
        
    # If it's already a valid province code, return it
    province_code = province_name_or_code.upper()
    if province_code in PROVINCE_CODE_TO_NAME:
        return province_code
    
    # Try to find a match in the province name to code mapping
    normalized_name = normalize_text(province_name_or_code)
    for name, code in PROVINCE_NAME_TO_CODE.items():
        if normalize_text(name) == normalized_name:
            return code
    
    # If no match found, return None
    return None

def get_party_code(party_name_or_code: str) -> Optional[str]:
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
        
    # If it's already a valid party code, return it
    party_code = party_name_or_code.upper()
    if party_code in PARTY_CODE_TO_NAME:
        return party_code
    
    # Try to find a match in the party name to code mapping
    normalized_name = normalize_text(party_name_or_code)
    for name, code in PARTY_NAME_TO_CODE.items():
        if normalize_text(name) == normalized_name:
            return code
    
    # If no match found, return None
    return None

def summarize_results(ridings: List[Dict[str, Any]], region_name: Optional[str] = None, region_code: Optional[str] = None) -> Dict[str, Any]:
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
    # Initialize counters
    total_votes = 0
    party_votes = {}
    party_seats = {}
    
    # Count votes and seats by party
    for riding in ridings:
        # Find the winning party in this riding
        max_votes = 0
        winning_party = None
        
        for party_vote in riding["voteDistribution"]:
            party_code = party_vote["partyCode"]
            votes = party_vote["votes"]
            
            # Update total votes for this party
            if party_code not in party_votes:
                party_votes[party_code] = 0
                party_seats[party_code] = 0
                
            party_votes[party_code] += votes
            total_votes += votes
            
            # Check if this is the winning party in this riding
            if votes > max_votes:
                max_votes = votes
                winning_party = party_code
        
        # Increment seat count for the winning party
        if winning_party:
            party_seats[winning_party] += 1
    
    # Calculate percentages and prepare results
    parties_data = []
    for party_code, votes in party_votes.items():
        vote_percent = (votes / total_votes * 100) if total_votes > 0 else 0
        
        parties_data.append({
            "partyCode": party_code,
            "partyName": PARTY_CODE_TO_NAME.get(party_code, party_code),
            "seats": party_seats.get(party_code, 0),
            "votes": votes,
            "votePercent": round(vote_percent, 2)
        })
    
    # Sort by seats (descending), then by votes (descending)
    parties_data.sort(key=lambda x: (-x["seats"], -x["votes"]))
    
    # Prepare the summary
    summary = {
        "totalRidings": len(ridings),
        "totalVotes": total_votes,
        "parties": parties_data
    }
    
    # Add region information if provided
    if region_name:
        summary["regionName"] = region_name
    if region_code:
        summary["regionCode"] = region_code
        
    return summary
