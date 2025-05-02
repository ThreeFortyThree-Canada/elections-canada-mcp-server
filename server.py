# Feature flag to disable pandas operations and query_election_data
DISABLE_PANDAS_OPERATIONS = False

import json
import pandas as pd
import os
from typing import Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP

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

# Tool to query election data using LangChain's Pandas Agent
@mcp.tool()
def query_election_data(question: str) -> str:
    """Answer flexible questions about election results using pandas and LangChain.
    For example: 'How many votes did the Liberals get in Newfoundland?'
    
    This function uses LangChain's Pandas Agent to interpret natural language questions
    and execute pandas operations on the election data.
    """
    # Import necessary libraries
    import os
    import json
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI
    from langchain.agents.agent_types import AgentType
    from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
    
    # Load environment variables (for OpenAI API key)
    load_dotenv()
    
    # Check if OpenAI API key is available
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return json.dumps({
            "error": "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
        }, indent=2)
    
    try:
        # Create a copy of the DataFrame with additional context
        df = DF.copy()
        
        # Add helpful column descriptions as metadata
        df_metadata = {
            "ridingCode": "Unique identifier for each electoral riding",
            "ridingName": "English name of the electoral riding",
            "province": "Province code (e.g., 'ON' for Ontario)",
            "partyCode": "Political party code (e.g., 'LPC' for Liberal Party of Canada)",
            "votes": "Number of votes received by the party in this riding",
            "votePercent": "Percentage of votes received by the party in this riding"
        }
        
        # Common party codes for easier reference
        party_codes = {
            "LPC": "Liberal Party of Canada",
            "CPC": "Conservative Party of Canada",
            "NDP": "New Democratic Party",
            "BQ": "Bloc Québécois",
            "GPC": "Green Party of Canada",
            "PPC": "People's Party of Canada"
        }
        
        # Common province codes
        province_codes = {
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
            "QC": "Quebec",
            "SK": "Saskatchewan",
            "YT": "Yukon"
        }
        
        # Create an LLM instance
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
        
        # Create a Pandas DataFrame agent
        agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=False,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            prefix=f"""
            You are an expert data analyst working with Canadian election data.
            The DataFrame contains election results from the 2021 Canadian federal election.
            
            Column descriptions:
            {json.dumps(df_metadata, indent=2)}
            
            Party codes:
            {json.dumps(party_codes, indent=2)}
            
            Province codes:
            {json.dumps(province_codes, indent=2)}
            
            When analyzing the data:
            1. For party-related queries, filter by the 'partyCode' column
            2. For province-related queries, filter by the 'province' column
            3. To find riding winners, group by ridingCode and find the party with max votes in each group
            4. Return your results as a JSON object with clear keys and values
            """
        )
        
        # Run the agent to answer the question
        result = agent.invoke({"input": question})
        
        # Extract the output
        output = result.get("output", "No result found")
        
        # Try to parse the output as JSON if it looks like JSON
        if output.strip().startswith("{") and output.strip().endswith("}"):
            try:
                parsed_json = json.loads(output)
                return json.dumps(parsed_json, indent=2)
            except json.JSONDecodeError:
                pass
        
        # Return the raw output if it's not valid JSON
        return output
        
    except Exception as e:
        return json.dumps({"error": f"Failed to execute query: {str(e)}"}, indent=2)

# Tool to get Python runtime information
@mcp.tool()
def get_python_runtime() -> str:
    """Returns info about the Python interpreter used by the Claude Desktop."""
    import sys
    import platform
    return json.dumps({
        "executable": sys.executable,
        "version": sys.version,
        "platform": platform.platform(),
        "sys_path": sys.path,
    }, indent=2)

if __name__ == "__main__":
    # Run the server in development mode
    import mcp.cli
    import sys
    import logging
    
    # Configure logging for MCP server
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("elections-canada-mcp")
    logger.info("Elections Canada MCP Server starting...")
    
    sys.argv = ["mcp", "dev"]
    mcp.cli.app()