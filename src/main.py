import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import requests
import json
import re
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# News API configuration - Using free API without key requirement
NEWS_API_BASE_URL = "https://saurav.tech/NewsAPI"

# Political bias classification constants
POLITICAL_BIAS = {
    "EXTREME_LEFT": "Extreme Left",
    "MODERATE_LEFT": "Moderate Left",
    "CENTER_LEFT": "Center Left",
    "CENTER": "Center",
    "CENTER_RIGHT": "Center Right",
    "MODERATE_RIGHT": "Moderate Right",
    "EXTREME_RIGHT": "Extreme Right",
    "NEUTRAL": "Mechanically Neutral"
}

# Source reliability ratings (pre-defined for MVP)
SOURCE_RELIABILITY = {
    "washington post": 93,
    "new york times": 92,
    "wall street journal": 95,
    "reuters": 98,
    "associated press": 99,
    "cnn": 85,
    "fox news": 80,
    "bbc news": 94,
    "bbc-news": 94,
    "npr": 92,
    "the guardian": 90,
    "the economist": 93,
    "politico": 88,
    "the hill": 87,
    "bloomberg": 91,
    "axios": 89
}

# Default reliability for unknown sources
DEFAULT_RELIABILITY = 75

# Available categories and countries for the API
CATEGORIES = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
COUNTRIES = ["us", "gb", "ca", "au", "in"]
DEFAULT_CATEGORY = "general"
DEFAULT_COUNTRY = "us"

# Available sources for the "everything" endpoint
SOURCES = ["bbc-news", "cnn", "fox-news", "google-news"]
DEFAULT_SOURCE = "cnn"

@app.route('/')
def index():
    """Render the main page of the application."""
    return render_template('index.html')

@app.route('/api/news')
def get_news():
    """Fetch news articles and apply bias detection."""
    # Get query parameters
    topic = request.args.get('topic', '')
    time_range = request.args.get('time_range', '7')  # Default to 7 days
    
    try:
        logger.info(f"Fetching news for topic: {topic}, time_range: {time_range}")
        
        # First try to get articles from the top-headlines endpoint
        articles = []
        
        # Map topic to category if possible
        category = map_topic_to_category(topic)
        logger.info(f"Mapped topic {topic} to category {category}")
        
        # Try each category if no specific topic is requested or if the mapped category doesn't return results
        categories_to_try = [category] if category else CATEGORIES
        
        for cat in categories_to_try:
            # Use top-headlines endpoint with category
            api_url = f"{NEWS_API_BASE_URL}/top-headlines/category/{cat}/{DEFAULT_COUNTRY}.json"
            logger.info(f"Trying API URL: {api_url}")
            
            # Make API request
            response = requests.get(api_url)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"API response status: {data.get('status')}, total results: {data.get('totalResults')}")
                    
                    if data.get('status') == 'ok' and data.get('articles'):
                        # Process articles with bias detection
                        for article in data.get('articles', []):
                            # Skip articles with missing essential data
                            if not article.get('title') or not article.get('description'):
                                continue
                                
                            # Filter by date if time_range is specified
                            if time_range:
                                try:
                                    published_date = datetime.strptime(article.get('publishedAt', ''), '%Y-%m-%dT%H:%M:%SZ')
                                    # For demo purposes, ignore the actual date since the API data is old
                                    # days_ago = (datetime.now() - published_date).days
                                    # if days_ago > int(time_range):
                                    #     continue
                                except (ValueError, TypeError):
                                    # Skip articles with invalid dates but don't fail
                                    pass
                            
                            processed_article = {
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'url': article.get('url', ''),
                                'source': article.get('source', {}).get('name', ''),
                                'image_url': article.get('urlToImage', ''),
                                'published_at': article.get('publishedAt', ''),
                                'categories': [cat],
                                # Add bias classification
                                'bias': detect_bias(article),
                                # Add reliability score
                                'reliability': get_source_reliability(article.get('source', {}).get('name', ''))
                            }
                            articles.append(processed_article)
                except Exception as e:
                    logger.error(f"Error processing API response: {str(e)}")
            else:
                logger.error(f"API request failed with status code: {response.status_code}")
            
            # If we have enough articles, stop trying more categories
            if len(articles) >= 5:
                break
        
        # If we still don't have articles, try the everything endpoint with each source
        if not articles:
            logger.info("No articles found from top-headlines, trying everything endpoint")
            for source in SOURCES:
                api_url = f"{NEWS_API_BASE_URL}/everything/{source}.json"
                logger.info(f"Trying API URL: {api_url}")
                
                # Make API request
                response = requests.get(api_url)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"API response status: {data.get('status')}, total results: {data.get('totalResults')}")
                        
                        if data.get('status') == 'ok' and data.get('articles'):
                            # Process articles with bias detection
                            for article in data.get('articles', []):
                                # Skip articles with missing essential data
                                if not article.get('title') or not article.get('description'):
                                    continue
                                    
                                # For demo purposes, ignore the actual date since the API data is old
                                processed_article = {
                                    'title': article.get('title', ''),
                                    'description': article.get('description', ''),
                                    'url': article.get('url', ''),
                                    'source': article.get('source', {}).get('name', ''),
                                    'image_url': article.get('urlToImage', ''),
                                    'published_at': article.get('publishedAt', ''),
                                    'categories': [category] if category else [],
                                    # Add bias classification
                                    'bias': detect_bias(article),
                                    # Add reliability score
                                    'reliability': get_source_reliability(article.get('source', {}).get('name', ''))
                                }
                                articles.append(processed_article)
                    except Exception as e:
                        logger.error(f"Error processing API response: {str(e)}")
                else:
                    logger.error(f"API request failed with status code: {response.status_code}")
                
                # If we have enough articles, stop trying more sources
                if len(articles) >= 10:
                    break
        
        # If we still have no articles, return a sample article for demonstration
        if not articles:
            logger.warning("No articles found from any source, using sample article")
            sample_article = {
                'title': 'Sample Article: Understanding Political Bias in Media',
                'description': 'This is a sample article to demonstrate the Spectrum News platform when no live articles are available.',
                'url': '#',
                'source': 'Spectrum News',
                'image_url': 'https://via.placeholder.com/300x200?text=Sample+Article',
                'published_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'categories': ['general'],
                'bias': POLITICAL_BIAS["CENTER"],
                'reliability': 90
            }
            articles.append(sample_article)
            
            # Add more sample articles with different biases
            sample_left = {
                'title': 'Sample: Progressive Policies and Social Justice',
                'description': 'This sample article demonstrates left-leaning content focusing on social programs and equality.',
                'url': '#',
                'source': 'Sample Progressive Source',
                'image_url': 'https://via.placeholder.com/300x200?text=Left+Leaning',
                'published_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'categories': ['general'],
                'bias': POLITICAL_BIAS["CENTER_LEFT"],
                'reliability': 85
            }
            articles.append(sample_left)
            
            sample_right = {
                'title': 'Sample: Free Market Solutions and Individual Liberty',
                'description': 'This sample article demonstrates right-leaning content focusing on economic freedom and traditional values.',
                'url': '#',
                'source': 'Sample Conservative Source',
                'image_url': 'https://via.placeholder.com/300x200?text=Right+Leaning',
                'published_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'categories': ['general'],
                'bias': POLITICAL_BIAS["CENTER_RIGHT"],
                'reliability': 85
            }
            articles.append(sample_right)
        
        logger.info(f"Returning {len(articles)} articles")
        
        # Group articles by bias for comparison
        grouped_articles = group_articles_by_bias(articles)
        
        return jsonify({
            "articles": articles,
            "grouped": grouped_articles
        })
    
    except Exception as e:
        logger.error(f"Error in get_news: {str(e)}")
        return jsonify({"error": str(e)}), 500

def map_topic_to_category(topic):
    """Map topic to API category."""
    topic_mapping = {
        'politics': 'general',
        'economy': 'business',
        'technology': 'technology',
        'climate': 'science',
        'health': 'health',
        'international': 'general',
        'sports': 'sports',
        'entertainment': 'entertainment'
    }
    
    return topic_mapping.get(topic.lower(), DEFAULT_CATEGORY)

def detect_bias(article):
    """
    Detect political bias in an article based on content analysis.
    This is a simplified implementation for the MVP.
    """
    # Extract text for analysis
    title = article.get('title', '').lower()
    description = article.get('description', '').lower()
    source_name = article.get('source', {}).get('name', '').lower()
    
    # Combined text for analysis
    text = f"{title} {description}"
    
    # Simple keyword-based bias detection for MVP
    # These would be expanded and refined in a production system
    
    # Left-leaning keywords
    left_keywords = [
        'progressive', 'liberal', 'workers rights', 'social justice',
        'equality', 'climate crisis', 'universal healthcare', 'regulation',
        'welfare', 'labor union', 'income inequality', 'systemic racism'
    ]
    
    # Right-leaning keywords
    right_keywords = [
        'conservative', 'traditional', 'free market', 'tax cuts',
        'deregulation', 'small government', 'fiscal responsibility',
        'individual liberty', 'second amendment', 'religious freedom',
        'border security', 'law and order'
    ]
    
    # Extreme language indicators
    extreme_indicators = [
        'radical', 'extreme', 'conspiracy', 'outrageous', 'shocking',
        'catastrophic', 'disaster', 'crisis', 'threat', 'danger',
        'enemy', 'destroy', 'evil', 'corrupt', 'tyranny', 'revolution'
    ]
    
    # Count keyword occurrences
    left_count = sum(1 for keyword in left_keywords if keyword in text)
    right_count = sum(1 for keyword in right_keywords if keyword in text)
    extreme_count = sum(1 for indicator in extreme_indicators if indicator in text)
    
    # Determine bias based on keyword counts
    bias_score = right_count - left_count  # Positive = right, Negative = left
    
    # Check for neutral mechanical style
    neutral_indicators = ['report', 'according to', 'officials said', 'data shows', 'statistics']
    neutral_count = sum(1 for indicator in neutral_indicators if indicator in text)
    
    # Source-based adjustments (pre-defined biases for well-known sources)
    source_bias_adjustment = 0
    if 'fox' in source_name or 'breitbart' in source_name:
        source_bias_adjustment = 2  # Right-leaning adjustment
    elif 'msnbc' in source_name or 'huffington' in source_name:
        source_bias_adjustment = -2  # Left-leaning adjustment
    elif 'reuters' in source_name or 'ap' in source_name or 'associated press' in source_name:
        return POLITICAL_BIAS["NEUTRAL"]  # These sources are typically neutral
    
    # Apply source adjustment
    bias_score += source_bias_adjustment
    
    # Determine final bias category
    if neutral_count >= 3 and extreme_count == 0:
        return POLITICAL_BIAS["NEUTRAL"]
    elif bias_score <= -4:
        return POLITICAL_BIAS["EXTREME_LEFT"] if extreme_count >= 2 else POLITICAL_BIAS["MODERATE_LEFT"]
    elif bias_score < 0:
        return POLITICAL_BIAS["CENTER_LEFT"]
    elif bias_score == 0:
        return POLITICAL_BIAS["CENTER"]
    elif bias_score <= 4:
        return POLITICAL_BIAS["CENTER_RIGHT"]
    else:
        return POLITICAL_BIAS["EXTREME_RIGHT"] if extreme_count >= 2 else POLITICAL_BIAS["MODERATE_RIGHT"]

def get_source_reliability(source):
    """
    Get reliability score for a news source.
    Uses pre-defined scores for known sources, default for unknown.
    """
    source_lower = source.lower()
    
    # Check for exact matches
    if source_lower in SOURCE_RELIABILITY:
        return SOURCE_RELIABILITY[source_lower]
    
    # Check for partial matches
    for known_source, reliability in SOURCE_RELIABILITY.items():
        if known_source in source_lower or source_lower in known_source:
            return reliability
    
    # Default reliability for unknown sources
    return DEFAULT_RELIABILITY

def group_articles_by_bias(articles):
    """
    Group articles by political bias for comparison.
    Returns a dictionary with bias categories as keys and lists of articles as values.
    """
    grouped = {
        "left": [],
        "center": [],
        "right": [],
        "neutral": []
    }
    
    for article in articles:
        bias = ar
(Content truncated due to size limit. Use line ranges to read in chunks)
