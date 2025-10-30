#!/usr/bin/env python3
"""
Test script to debug domain matching
Run this to test if your domain normalization is working correctly
"""

def normalize_domain(url: str) -> str:
    """Normalize a domain/URL for comparison"""
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

def test_matching(target_domain: str, result_urls: list):
    """Test if domain matching works correctly"""
    normalized_target = normalize_domain(target_domain)
    
    print(f"\n{'='*60}")
    print(f"Testing domain: {target_domain}")
    print(f"Normalized to: {normalized_target}")
    print(f"{'='*60}\n")
    
    for idx, url in enumerate(result_urls, start=1):
        normalized_result = normalize_domain(url)
        
        # Check if exact match or subdomain match
        is_match = (normalized_result == normalized_target or 
                   normalized_result.endswith('.' + normalized_target))
        
        status = "✓ MATCH" if is_match else "✗ no match"
        print(f"#{idx:2d} {status:12s} | {normalized_result:30s} | {url[:60]}")
        
        if is_match:
            print(f"\n>>> FOUND AT POSITION #{idx} <<<\n")
            return idx
    
    print(f"\n>>> NOT FOUND in {len(result_urls)} results <<<\n")
    return None

# Example test cases
if __name__ == "__main__":
    print("\n" + "="*60)
    print("DOMAIN MATCHING TEST UTILITY")
    print("="*60)
    
    # Test Case 1: Simple domain
    print("\n\nTEST 1: Simple domain matching")
    test_matching(
        "example.com",
        [
            "https://www.google.com/search",
            "https://www.wikipedia.org/wiki/Example",
            "https://example.com/about",
            "https://www.example.com/products",
        ]
    )
    
    # Test Case 2: Subdomain matching
    print("\n\nTEST 2: Subdomain matching")
    test_matching(
        "example.com",
        [
            "https://www.google.com/search",
            "https://blog.example.com/post",
            "https://shop.example.com/products",
        ]
    )
    
    # Test Case 3: Should NOT match partial domains
    print("\n\nTEST 3: Should NOT match partial domains")
    test_matching(
        "example.com",
        [
            "https://www.notexample.com/page",
            "https://examplesite.com/page",
            "https://my-example.com/page",
        ]
    )
    
    print("\n" + "="*60)
    print("\nTo test with your actual domain:")
    print("1. Edit this file and add your test case")
    print("2. Run: python3 test_domain_matching.py")
    print("="*60 + "\n")
