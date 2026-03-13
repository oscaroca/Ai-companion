"""
WaniKani API client for fetching learned vocabulary and kanji.
Includes caching to minimize API calls.
"""

import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import WaniKaniConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class WaniKaniClient:
    """Client for WaniKani API with caching."""
    
    BASE_URL = "https://api.wanikani.com/v2"
    
    def __init__(self, config: WaniKaniConfig):
        """
        Initialize WaniKani client.
        
        Args:
            config: WaniKani configuration
        """
        self.config = config
        self.api_key = config.api_key
        self.cache_path = Path(config.cache_path)
        self.cache_ttl = config.cache_ttl
        
        if not self.api_key:
            raise ValueError("WaniKani API key is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Wanikani-Revision": "20170710"
        }
        
        # Ensure cache directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("WaniKani client initialized")
    
    def fetch_learned_items(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch user's learned vocabulary and kanji.
        
        Args:
            force_refresh: Force refresh from API (ignore cache)
            
        Returns:
            List of learned items
        """
        # Check cache first
        if not force_refresh and self._is_cache_valid():
            logger.debug("Using cached WaniKani data")
            return self._load_cache()
        
        logger.info("Fetching learned items from WaniKani API...")
        
        try:
            # Fetch assignments (learned items)
            assignments = self._fetch_assignments()
            
            # Get subject IDs
            subject_ids = [a["data"]["subject_id"] for a in assignments]
            
            if not subject_ids:
                logger.warning("No learned items found")
                return []
            
            # Fetch subject details
            subjects = self._fetch_subjects(subject_ids)
            
            # Build learned items list
            learned_items = []
            for assignment in assignments:
                subject_id = assignment["data"]["subject_id"]
                subject = subjects.get(subject_id)
                
                if not subject:
                    continue
                
                sdata = subject["data"]
                
                learned_items.append({
                    "type": subject["object"],  # vocabulary or kanji
                    "characters": sdata.get("characters"),
                    "meanings": [m["meaning"] for m in sdata.get("meanings", [])],
                    "readings": [r["reading"] for r in sdata.get("readings", [])],
                    "srs_stage": assignment["data"]["srs_stage"]
                })
            
            # Cache the results
            self._save_cache(learned_items)
            
            logger.info(f"Fetched {len(learned_items)} learned items")
            return learned_items
        
        except Exception as e:
            logger.error(f"Failed to fetch WaniKani data: {e}")
            # Try to return cached data even if expired
            if self.cache_path.exists():
                logger.warning("Returning expired cache due to API error")
                return self._load_cache()
            return []
    
    def _fetch_assignments(self) -> List[Dict[str, Any]]:
        """Fetch user assignments (learned items)."""
        params = {
            "subject_types": "vocabulary,kanji",
            "srs_stages": "1,2,3,4,5,6,7,8,9"  # Apprentice → Burned
        }
        
        return self._fetch_all_pages(f"{self.BASE_URL}/assignments", params)
    
    def _fetch_subjects(self, subject_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Fetch subject details by IDs."""
        subjects = {}
        chunk_size = 1000  # API limit
        
        for i in range(0, len(subject_ids), chunk_size):
            chunk = subject_ids[i:i + chunk_size]
            params = {"ids": ",".join(map(str, chunk))}
            
            data = self._fetch_all_pages(f"{self.BASE_URL}/subjects", params)
            
            for item in data:
                subjects[item["id"]] = item
        
        return subjects
    
    def _fetch_all_pages(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch all pages from paginated API endpoint."""
        results = []
        
        while url:
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                results.extend(data["data"])
                
                url = data["pages"]["next_url"]
                params = None  # Only needed for first request
            
            except requests.exceptions.RequestException as e:
                logger.error(f"WaniKani API request failed: {e}")
                raise
        
        return results
    
    def format_for_context(self, items: List[Dict[str, Any]]) -> str:
        """
        Format learned items for LLM context.
        
        Args:
            items: List of learned items
            
        Returns:
            Formatted string for LLM context
        """
        if not items:
            return "No Japanese vocabulary learned yet."
        
        lines = ["JAPANESE LEARNED SO FAR:"]
        
        for item in items[:50]:  # Limit to avoid context overflow
            if item['type'] == 'vocabulary':
                meanings = ", ".join(item['meanings'][:3])  # Limit meanings
                readings = ", ".join(item['readings'][:2])  # Limit readings
                lines.append(
                    f"- Vocab: {item['characters']} ({readings}) = {meanings}"
                )
            elif item['type'] == 'kanji':
                meanings = ", ".join(item['meanings'][:3])
                readings = ", ".join(item['readings'][:2])
                lines.append(
                    f"- Kanji: {item['characters']} ({readings}) = {meanings}"
                )
        
        if len(items) > 50:
            lines.append(f"... and {len(items) - 50} more items")
        
        return "\n".join(lines)
    
    def _is_cache_valid(self) -> bool:
        """Check if cache exists and is not expired."""
        if not self.cache_path.exists():
            return False
        
        cache_age = time.time() - self.cache_path.stat().st_mtime
        return cache_age < self.cache_ttl
    
    def _load_cache(self) -> List[Dict[str, Any]]:
        """Load cached data."""
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return []
    
    def _save_cache(self, data: List[Dict[str, Any]]) -> None:
        """Save data to cache."""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cached WaniKani data to {self.cache_path}")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
