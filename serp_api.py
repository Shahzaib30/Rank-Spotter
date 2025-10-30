"""
SerpApi integration module
Handles all interactions with the SerpApi                logger.info(f"Fetching page {page + 1} for keyword: '{keyword}' (start={start})")
                response = requests.get(self.BASE_URL, params=params, timeout=20)
                response.raise_for_status()rvice
"""
import requests
import logging
import time
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
        try:
            # Determine how many pages we need to fetch (10 results per page)
            per_page = 10
            pages_needed = (max_results + per_page - 1) // per_page
            pages_needed = min(pages_needed, 5)  # safety cap: 5 pages (50 results)

            # Build params for each page
            pages_params = []
            for page_idx in range(pages_needed):
                start = page_idx * per_page
                params = {
                    'api_key': self.api_key,
                    'engine': self.engine,
                    'q': keyword,
                    'location': self.location,
                    'num': per_page,
                    'start': start,
                    'gl': 'us',
                    'hl': 'en',
                    'device': self.device,
                    'google_domain': 'google.com',
                    'safe': 'off',
                    'no_cache': 'true'
                }
                pages_params.append((page_idx, params))

            # Fetch pages in parallel to reduce overall latency
            try:
                from concurrent.futures import ThreadPoolExecutor, as_completed

                results_by_page = {}
                # Use 3-4 workers for better speed while managing rate limits
                max_workers = min(pages_needed, 3)
                with ThreadPoolExecutor(max_workers=max_workers) as ex:
                    futures = {}
                    for page_idx, params in pages_params:
                        logger.info(f"Submitting fetch for page {page_idx + 1} (start={params['start']})")
                        futures[ex.submit(requests.get, self.BASE_URL, params=params, timeout=15)] = page_idx

                    for fut in as_completed(futures):
                        page_idx = futures[fut]
                        try:
                            resp = fut.result()
                            resp.raise_for_status()
                            data = resp.json()
                            organic = data.get('organic_results', [])
                            results_by_page[page_idx] = (organic, data)
                            logger.info(f"Page {page_idx + 1}: fetched {len(organic)} results")
                        except Exception as e:
                            logger.warning(f"Parallel fetch for page {page_idx + 1} failed: {e}")

                # If any page failed during parallel fetch, fall back to sequential fetching
                if len(results_by_page) < pages_needed:
                    logger.warning("Parallel fetch incomplete; falling back to sequential fetch to ensure correctness")
                    all_organic_results = []
                    last_data = {}
                    for page_idx, params in pages_params:
                        logger.info(f"Fetching page {page_idx + 1} for keyword: '{keyword}' (start={params['start']})")
                        # Retry on 429 (Too Many Requests) with exponential backoff
                        success = False
                        last_attempt_data = None
                        for attempt in range(1, 3):  # Reduce retries from 3 to 2
                            try:
                                resp = requests.get(self.BASE_URL, params=params, timeout=15)  # Reduce timeout to 15s
                                if resp.status_code == 429:
                                    wait = 0.5 * (2 ** (attempt - 1))  # Faster backoff: 0.5s, 1s
                                    logger.warning(f"Received 429 from SerpApi on page {page_idx + 1}, attempt {attempt}. Backing off {wait}s")
                                    time.sleep(wait)
                                    continue
                                resp.raise_for_status()
                                data = resp.json()
                                organic = data.get('organic_results', [])
                                last_attempt_data = (organic, data)
                                success = True
                                break
                            except requests.exceptions.RequestException as e:
                                logger.warning(f"Request failed for page {page_idx + 1} attempt {attempt}: {e}")
                                time.sleep(1 * attempt)

                        if not success:
                            logger.error(f"Failed to fetch page {page_idx + 1} after retries; aborting sequential fetch")
                            break

                        organic, data = last_attempt_data
                        if not organic:
                            break
                        all_organic_results.extend(organic)
                        last_data = data
                else:
                    # Assemble results in page order
                    last_data = {}
                    for page_idx in range(pages_needed):
                        page_data = results_by_page.get(page_idx)
                        organic, last_data = page_data
                        if not organic:
                            logger.info(f"No organic results on page {page_idx + 1}, stopping")
                            break
                        all_organic_results.extend(organic)

            except Exception as e:
                # If parallel fetching fails completely, return what we have or error
                logger.error(f"Parallel fetch failed: {e}")
                if not all_organic_results:
                    raise Exception(f"Failed to fetch search results: {e}")

            # Trim to max_results
            all_organic_results = all_organic_results[:max_results]

            logger.info(f"Successfully fetched {len(all_organic_results)} total organic results for '{keyword}'")

            # Return in the same format as before
            return {
                'organic_results': all_organic_results,
                'search_metadata': last_data.get('search_metadata', {}) if last_data else {},
                'search_parameters': last_data.get('search_parameters', {}) if last_data else {}
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
    
    def find_domain_rank(self, keyword: str, domain: str, max_results: int = None) -> Dict:
        """
        Search for a keyword and find the ranking position of a specific domain
        
        Args:
            keyword: Search keyword
            domain: Domain to find in results (e.g., 'example.com')
            max_results: Maximum results to fetch (default: self.num_results)
            
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
            # Perform search with early termination capability
            # Start with smaller batch, expand if needed
            if max_results is None:
                max_results = self.num_results
            
            # Normalize domain for comparison
            normalized_domain = self._normalize_domain(domain)
            logger.info(f"Searching for domain '{normalized_domain}' with max {max_results} results")
            
            # Fetch in chunks and check after each chunk for early termination
            chunk_size = 20  # Fetch 2 pages (20 results) at a time
            position = None
            found_result = None
            all_organic_results = []
            
            for chunk_start in range(0, max_results, chunk_size):
                chunk_max = min(chunk_size, max_results - chunk_start)
                logger.info(f"Fetching chunk: results {chunk_start+1}-{chunk_start+chunk_max}")
                
                # Fetch this chunk
                results = self.search(keyword, max_results=chunk_start + chunk_max)
                all_organic_results = results.get('organic_results', [])
                
                # Check if domain found in current results
                for idx, result in enumerate(all_organic_results, start=1):
                    result_link = result.get('link', '')
                    result_domain = self._normalize_domain(result_link)
                    
                    if result_domain == normalized_domain or result_domain.endswith('.' + normalized_domain):
                        position = idx
                        found_result = result
                        logger.info(f"✓ Domain '{domain}' found at position #{position} (URL: {result_link})")
                        # EARLY EXIT - domain found!
                        return self._create_response(keyword, domain, position, all_organic_results, found_result)
                
                # If we've fetched all requested results and not found, stop
                if len(all_organic_results) >= max_results:
                    break
            
            # Domain not found after all chunks
            logger.warning(f"✗ Domain '{domain}' not found in top {len(all_organic_results)} results")
            return self._create_response(keyword, domain, None, all_organic_results)
            
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
