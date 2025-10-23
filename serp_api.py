"""
SerpApi integration module
Handles all interactions with the SerpApi service
"""
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SerpApiClient:
    """Client for interacting with SerpApi"""
    
    BASE_URL = "https://serpapi.com/search"
    
    def __init__(self, api_key: str, engine: str = 'google', location: str = 'United States', num_results: int = 100):
        """
        Initialize SerpApi client
        
        Args:
            api_key: SerpApi API key
            engine: Search engine to use (default: google)
            location: Location for search results (e.g., 'United States', 'New York, NY', 'Los Angeles, CA')
            num_results: Number of results to fetch
        """
        self.api_key = api_key
        self.engine = engine
        self.location = location
        self.num_results = num_results
        self.device = 'desktop'  # Use desktop device for more accurate rankings
    
    def search(self, keyword: str, max_results: int = None) -> Dict:
        """
        Perform a search query using SerpApi with pagination support
        
        Args:
            keyword: Search keyword/query
            max_results: Maximum number of results to fetch (default: self.num_results)
            
        Returns:
            Dictionary containing search results
            
        Raises:
            Exception: If API request fails
        """
        if max_results is None:
            max_results = self.num_results
            
        all_organic_results = []
        page = 0
        start = 0
        
        try:
            # Fetch results with pagination (Google shows 10 per page by default)
            # We need to paginate to get up to 100 results
            while len(all_organic_results) < max_results:
                params = {
                    'api_key': self.api_key,
                    'engine': self.engine,
                    'q': keyword,
                    'location': self.location,
                    'num': 10,  # Results per page (10 is standard)
                    'start': start,  # Starting position for pagination
                    'gl': 'us',      # Country code - United States
                    'hl': 'en',      # Language - English
                    'device': self.device,  # Desktop device for consistent rankings
                    'google_domain': 'google.com',  # Use google.com (US domain)
                    'safe': 'off',   # Disable safe search for complete results
                    'no_cache': 'true'  # Get fresh results, not cached
                }
                
                logger.info(f"Fetching page {page + 1} for keyword: '{keyword}' (start={start})")
                response = requests.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                organic_results = data.get('organic_results', [])
                
                if not organic_results:
                    logger.info(f"No more results found at page {page + 1}")
                    break
                
                all_organic_results.extend(organic_results)
                logger.info(f"Page {page + 1}: Fetched {len(organic_results)} results (total: {len(all_organic_results)})")
                
                # Check if we have enough results or if there are no more pages
                if len(all_organic_results) >= max_results:
                    break
                    
                # Check if there's a next page
                serpapi_pagination = data.get('serpapi_pagination', {})
                if not serpapi_pagination.get('next'):
                    logger.info(f"No more pages available")
                    break
                
                # Move to next page
                page += 1
                start += 10
                
                # Safety limit: don't fetch more than 10 pages
                if page >= 10:
                    logger.warning(f"Reached maximum page limit (10 pages)")
                    break
            
            # Trim to max_results
            all_organic_results = all_organic_results[:max_results]
            
            logger.info(f"Successfully fetched {len(all_organic_results)} total organic results for '{keyword}'")
            
            # Return in the same format as before
            return {
                'organic_results': all_organic_results,
                'search_metadata': data.get('search_metadata', {}),
                'search_parameters': data.get('search_parameters', {})
            }
            
        except requests.exceptions.Timeout:
            logger.error("SerpApi request timed out")
            raise Exception("Search request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            logger.error(f"SerpApi request failed: {str(e)}")
            raise Exception(f"Failed to fetch search results: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in SerpApi search: {str(e)}")
            raise Exception(f"An unexpected error occurred: {str(e)}")
    
    def find_domain_rank(self, keyword: str, domain: str) -> Dict:
        """
        Search for a keyword and find the ranking position of a specific domain
        
        Args:
            keyword: Search keyword
            domain: Domain to find in results (e.g., 'example.com')
            
        Returns:
            Dictionary containing:
                - keyword: Search keyword
                - domain: Target domain
                - position: Ranking position (1-indexed) or None if not found
                - url: Full URL if found
                - title: Page title if found
                - snippet: Page snippet if found
                - top_results: List of top 10 results
                - total_results: Total number of results fetched
                - timestamp: ISO format timestamp
                - found: Boolean indicating if domain was found
        """
        try:
            # Perform search
            results = self.search(keyword)
            
            # Extract organic results
            organic_results = results.get('organic_results', [])
            
            if not organic_results:
                logger.warning(f"No organic results found for keyword: {keyword}")
                return self._create_response(keyword, domain, None, organic_results)
            
            # Normalize domain for comparison (remove www, http, https, trailing slash)
            normalized_domain = self._normalize_domain(domain)
            
            logger.info(f"Searching for domain '{normalized_domain}' in {len(organic_results)} results")
            
            # Search for domain in results
            position = None
            found_result = None
            
            for idx, result in enumerate(organic_results, start=1):
                result_link = result.get('link', '')
                result_domain = self._normalize_domain(result_link)
                
                # Exact match or subdomain match
                # e.g., if searching for "example.com", match "example.com" or "blog.example.com"
                if result_domain == normalized_domain or result_domain.endswith('.' + normalized_domain):
                    position = idx
                    found_result = result
                    logger.info(f"✓ Domain '{domain}' found at position #{position} (URL: {result_link})")
                    break
                else:
                    # Log for debugging (only first 20 to avoid spam)
                    if idx <= 20:
                        logger.debug(f"  Position #{idx}: {result_domain} != {normalized_domain}")
            
            if not found_result:
                logger.warning(f"✗ Domain '{domain}' (normalized: '{normalized_domain}') not found in top {len(organic_results)} results")
                # Log all domains for debugging (limit to 20 to avoid spam)
                logger.info(f"All {min(len(organic_results), 20)} domains checked:")
                for idx, result in enumerate(organic_results[:20], start=1):
                    result_link = result.get('link', 'N/A')
                    result_domain = self._normalize_domain(result_link)
                    logger.info(f"  #{idx:2d}: {result_domain} ({result_link[:60]}...)")
            
            return self._create_response(keyword, domain, position, organic_results, found_result)
            
        except Exception as e:
            logger.error(f"Error finding domain rank: {str(e)}")
            raise
    
    @staticmethod
    def _normalize_domain(url: str) -> str:
        """
        Normalize a domain/URL for comparison
        
        Args:
            url: URL or domain to normalize
            
        Returns:
            Normalized domain string (e.g., "example.com")
            
        Examples:
            "https://www.example.com/path" -> "example.com"
            "http://example.com?query=1" -> "example.com"
            "example.com/" -> "example.com"
            "www.example.com" -> "example.com"
        """
        if not url:
            return ""
            
        domain = url.lower().strip()
        
        # Remove protocol
        domain = domain.replace('https://', '').replace('http://', '')
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove path (everything after first /)
        domain = domain.split('/')[0]
        
        # Remove query params
        domain = domain.split('?')[0]
        
        # Remove port if present
        domain = domain.split(':')[0]
        
        # Remove trailing dots
        domain = domain.rstrip('.')
        
        return domain
    
    @staticmethod
    def _create_response(keyword: str, domain: str, position: Optional[int], 
                        organic_results: List[Dict], found_result: Optional[Dict] = None) -> Dict:
        """
        Create a standardized response object
        
        Args:
            keyword: Search keyword
            domain: Target domain
            position: Ranking position or None
            organic_results: List of organic search results
            found_result: The result object if found
            
        Returns:
            Standardized response dictionary
        """
        # Get top 10 results for preview
        top_results = []
        for idx, result in enumerate(organic_results[:10], start=1):
            top_results.append({
                'position': idx,
                'title': result.get('title', 'N/A'),
                'link': result.get('link', 'N/A'),
                'snippet': result.get('snippet', 'N/A'),
                'displayed_link': result.get('displayed_link', 'N/A')
            })
        
        response = {
            'keyword': keyword,
            'domain': domain,
            'position': position,
            'found': position is not None,
            'total_results': len(organic_results),
            'top_results': top_results,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Add details if domain was found
        if found_result:
            response['url'] = found_result.get('link', 'N/A')
            response['title'] = found_result.get('title', 'N/A')
            response['snippet'] = found_result.get('snippet', 'N/A')
            response['displayed_link'] = found_result.get('displayed_link', 'N/A')
        
        return response
