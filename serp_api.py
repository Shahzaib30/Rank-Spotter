"""
SerpApi integration module (U.S.-wide rotation)
Handles all interactions with the SerpApi service
"""
import requests
import logging
import random
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SerpApiClient:
    """Client for interacting with SerpApi (U.S.-optimized with rotation)"""
    
    BASE_URL = "https://serpapi.com/search.json"
    
    # ✅ List of major U.S. cities for nationwide coverage
    US_LOCATIONS = [
        "New York, New York, United States",
        "Los Angeles, California, United States",
        "Chicago, Illinois, United States",
        "Houston, Texas, United States",
        "Phoenix, Arizona, United States",
        "Philadelphia, Pennsylvania, United States",
        "San Antonio, Texas, United States",
        "San Diego, California, United States",
        "Dallas, Texas, United States",
        "San Jose, California, United States",
        "Austin, Texas, United States",
        "Jacksonville, Florida, United States",
        "San Francisco, California, United States",
        "Columbus, Ohio, United States",
        "Indianapolis, Indiana, United States",
        "Fort Worth, Texas, United States",
        "Charlotte, North Carolina, United States",
        "Seattle, Washington, United States",
        "Denver, Colorado, United States",
        "Washington, D.C., United States"
    ]
    
    def __init__(
        self,
        api_key: str,
        engine: str = 'google',
        num_results: int = 100,
        google_domain: str = 'google.com',
        gl: str = 'us',
        hl: str = 'en',
        rotate_mode: str = 'random',  # or 'sequential'
        device: str = 'desktop'       # or 'mobile'
    ):
        """
        Initialize SerpApi client
        
        Args:
            api_key: SerpApi API key
            engine: Search engine to use (default: google)
            num_results: Number of results to fetch
            google_domain: Google TLD (default google.com)
            gl: Country code (default: us)
            hl: Language code (default: en)
            rotate_mode: 'random' or 'sequential' for rotating cities
            device: 'desktop' (default) or 'mobile' to simulate device type
        """
        self.api_key = api_key
        self.engine = engine
        self.num_results = num_results
        self.google_domain = google_domain
        self.gl = gl
        self.hl = hl
        self.rotate_mode = rotate_mode
        self.device = device
        self._city_index = 0  # used for sequential rotation
        
        # 🎯 Choose user-agent based on device
        if self.device == 'mobile':
            self.headers = {
                "User-Agent": (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/17.0 Mobile/15E148 Safari/604.1"
                )
            }
        else:  # desktop default
            self.headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/129.0.0.0 Safari/537.36"
                )
            }

    def _get_next_location(self) -> str:
        """Return the next U.S. city (random or sequential)"""
        if self.rotate_mode == 'random':
            return random.choice(self.US_LOCATIONS)
        else:
            location = self.US_LOCATIONS[self._city_index]
            self._city_index = (self._city_index + 1) % len(self.US_LOCATIONS)
            return location

    def search(self, keyword: str) -> Dict:
        """Perform a U.S.-wide search query using rotating cities"""
        try:
            location = self._get_next_location()
            
            params = {
                'api_key': self.api_key,
                'engine': self.engine,
                'q': keyword,
                'location': location,
                'num': self.num_results,
                'gl': self.gl,
                'hl': self.hl,
                'google_domain': self.google_domain,
                'device': self.device
            }
            
            logger.info(f"Searching SerpApi for '{keyword}' (location: {location}, device: {self.device})")
            response = requests.get(self.BASE_URL, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Fetched {len(data.get('organic_results', []))} results for '{keyword}' from {location}")
            
            return data
            
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
        """Search for a keyword and find the ranking position of a specific domain"""
        try:
            results = self.search(keyword)
            organic_results = results.get('organic_results', [])
            
            if not organic_results:
                logger.warning(f"No organic results found for keyword: {keyword}")
                return self._create_response(keyword, domain, None, organic_results)
            
            normalized_domain = self._normalize_domain(domain)
            position = None
            found_result = None
            
            for idx, result in enumerate(organic_results, start=1):
                result_link = result.get('link', '')
                result_domain = self._normalize_domain(result_link)
                
                if normalized_domain in result_domain:
                    position = idx
                    found_result = result
                    logger.info(f"Domain {domain} found at position {position}")
                    break
            
            if not found_result:
                logger.info(f"Domain {domain} not found in top {len(organic_results)} results")
            
            return self._create_response(keyword, domain, position, organic_results, found_result)
            
        except Exception as e:
            logger.error(f"Error finding domain rank: {str(e)}")
            raise

    @staticmethod
    def _normalize_domain(url: str) -> str:
        """Normalize a domain/URL for comparison"""
        domain = url.lower()
        domain = domain.replace('https://', '').replace('http://', '')
        domain = domain.replace('www.', '')
        domain = domain.split('/')[0]
        domain = domain.split('?')[0]
        return domain

    @staticmethod
    def _create_response(keyword: str, domain: str, position: Optional[int], 
                        organic_results: List[Dict], found_result: Optional[Dict] = None) -> Dict:
        """Create a standardized response object"""
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
        
        if found_result:
            response['url'] = found_result.get('link', 'N/A')
            response['title'] = found_result.get('title', 'N/A')
            response['snippet'] = found_result.get('snippet', 'N/A')
            response['displayed_link'] = found_result.get('displayed_link', 'N/A')
        
        return response
