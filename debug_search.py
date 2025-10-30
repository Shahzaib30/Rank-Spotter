#!/usr/bin/env python3
"""
Quick test script to debug a specific keyword search
Usage: python3 debug_search.py "your keyword" "yourdomain.com"
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serp_api import SerpApiClient
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_search(keyword, domain):
    """Test a specific keyword and domain search"""
    api_key = os.getenv('SERPAPI_KEY')
    
    if not api_key:
        print("❌ ERROR: SERPAPI_KEY not found in .env file")
        return
    
    print(f"\n{'='*70}")
    print(f"Testing Search")
    print(f"{'='*70}")
    print(f"Keyword: {keyword}")
    print(f"Domain:  {domain}")
    print(f"{'='*70}\n")
    
    # Create client
    client = SerpApiClient(
        api_key=api_key,
        location=os.getenv('SERPAPI_LOCATION', 'United States')
    )
    
    try:
        # Perform search
        result = client.find_domain_rank(keyword, domain)
        
        print(f"\n{'='*70}")
        print(f"RESULT")
        print(f"{'='*70}")
        print(f"Found:           {result['found']}")
        print(f"Position:        {result['position'] if result['found'] else 'Not found'}")
        print(f"Total Results:   {result['total_results']}")
        
        if result['found']:
            print(f"\nMatched URL:     {result['url']}")
            print(f"Title:           {result['title']}")
            print(f"Snippet:         {result['snippet'][:100]}...")
        else:
            print(f"\n⚠️  Domain not found in top {result['total_results']} results")
            print(f"\nPlease check the server logs above for detailed domain list")
        
        print(f"\n{'='*70}\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Default test values (edit these or pass as command line arguments)
    default_keyword = "aba therapy mckinney texas"
    default_domain = "https://evolveabacare.com/"  # REPLACE WITH YOUR DOMAIN
    
    if len(sys.argv) >= 3:
        keyword = sys.argv[1]
        domain = sys.argv[2]
    else:
        keyword = default_keyword
        domain = default_domain
        print(f"\n💡 TIP: You can pass arguments: python3 debug_search.py 'keyword' 'domain.com'\n")
    
    test_search(keyword, domain)
