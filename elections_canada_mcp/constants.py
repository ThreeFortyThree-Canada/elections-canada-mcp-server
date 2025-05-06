"""
Constants for the Elections Canada MCP Server.

This module contains all the constant mappings used in the server.
"""

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
