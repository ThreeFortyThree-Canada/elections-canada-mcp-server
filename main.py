#!/usr/bin/env python
"""
Elections Canada MCP Server - Command Line Interface

This script serves as the entry point for running the Elections Canada MCP server.
"""

import sys
import argparse
from elections_canada_mcp.server import mcp

def main():
    """Run the Elections Canada MCP server."""
    parser = argparse.ArgumentParser(description="Elections Canada MCP Server")
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1", 
        help="Host to run the server on"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to run the server on"
    )
    args = parser.parse_args()
    
    # Start the server
    print(f"Starting Elections Canada MCP server on {args.host}:{args.port}")
    mcp.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
