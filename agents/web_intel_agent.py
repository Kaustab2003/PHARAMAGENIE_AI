# agents/web_intel_agent.py
import requests
import feedparser
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

class WebIntelligenceAgent:
    """Agent for gathering open-source intelligence from the web, including scientific literature and news."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.cache = {}
        self.cache_ttl = timedelta(hours=6)  # Cache results for 6 hours

    def _get_cached(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.info(f"Returning cached data for key: {key}")
                return data
        return None

    def _set_cached(self, key: str, data: Dict):
        self.cache[key] = (data, datetime.now())

    def _search_pubmed(self, query: str, max_results: int = 3) -> List[Dict]:
        """Searches PubMed for relevant scientific articles."""
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        search_params = {'db': 'pubmed', 'term': query, 'retmax': max_results, 'sort': 'relevance'}
        try:
            logger.info(f"Searching PubMed with query: {query}")
            search_resp = self.session.get(f"{base_url}esearch.fcgi", params=search_params, timeout=15)
            search_resp.raise_for_status()
            id_list = ET.fromstring(search_resp.content).findall('.//IdList/Id')
            if not id_list:
                return []

            ids = ','.join([elem.text for elem in id_list])
            summary_params = {'db': 'pubmed', 'id': ids, 'retmode': 'json'}
            summary_resp = self.session.get(f"{base_url}esummary.fcgi", params=summary_params, timeout=15)
            summary_resp.raise_for_status()
            summary_data = summary_resp.json()['result']
            
            return [{
                'title': article.get('title', 'No title'),
                'source': 'PubMed',
                'date': article.get('pubdate', ''),
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                'snippet': f"Authors: {', '.join(a['name'] for a in article.get('authors', []))}. Journal: {article.get('source', 'N/A')}."
            } for uid, article in summary_data.items() if uid != 'uids']
        except requests.exceptions.RequestException as e:
            logger.error(f"PubMed search failed: {e}")
            return []

    def _search_google_news(self, query: str, max_results: int = 3) -> List[Dict]:
        """Searches Google News for recent news articles via RSS feed."""
        # Note: This is an unofficial method and may be unstable.
        url = f'https://news.google.com/rss/search?q={query.replace(" ", "+")}&hl=en-US&gl=US&ceid=US:en'
        try:
            logger.info(f"Searching Google News with query: {query}")
            feed = feedparser.parse(url)
            return [{
                'title': entry.title,
                'source': entry.source.title,
                'date': entry.published,
                'url': entry.link,
                'snippet': entry.get('summary', 'No summary available.')
            } for entry in feed.entries[:max_results]]
        except Exception as e:
            logger.error(f"Google News search failed: {e}")
            return []

    def search_evidence(self, query: str, sources: Optional[List[str]] = None) -> Dict:
        """ 
        Searches for evidence from multiple web sources.
        Query should be the drug name, optionally with the therapeutic area.
        """
        cache_key = f"web_intel_{query.lower()}"
        if cached_data := self._get_cached(cache_key):
            return cached_data

        # Fetch data from sources
        pubmed_findings = self._search_pubmed(f'{query} efficacy safety')
        news_articles = self._search_google_news(f'{query} pharmaceutical')

        findings = [f"{f['title']} (Source: {f['source']})" for f in pubmed_findings]
        if not findings:
            findings.append("No recent scientific literature found on PubMed.")

        sources = set()
        if pubmed_findings: 
            sources.add("PubMed")
        if news_articles:
            sources.add("Google News")

        result = {
            "sources": list(sources),
            "findings": findings,
            "news": news_articles
        }
        
        self._set_cached(cache_key, result)
        return result