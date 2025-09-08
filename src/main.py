import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import requests
import json
import re
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)

# News API configuration
NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'demo-api-key')  # Default to demo key for development
NEWS_API_BASE_URL = "https://api.thenewsapi.com/v1/news"

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
    "bbc": 94,
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
    
    # Calculate date range
    days = int(time_range)
    published_after = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Prepare API request
    params = {
        'api_token': NEWS_API_KEY,
        'language': 'en',
        'limit': 10,  # Limit results for MVP
    }
    
    if topic:
        params['categories'] = topic
    
    params['published_after'] = published_after
    
    try:
        # Make API request
        response = requests.get(f"{NEWS_API_BASE_URL}/all", params=params)
        data = response.json()
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch news", "details": data}), 500
        
        # Process articles with bias detection
        processed_articles = []
        for article in data.get('data', []):
            processed_article = {
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', ''),
                'image_url': article.get('image_url', ''),
                'published_at': article.get('published_at', ''),
                'categories': article.get('categories', []),
                # Add bias classification
                'bias': detect_bias(article),
                # Add reliability score
                'reliability': get_source_reliability(article.get('source', ''))
            }
            processed_articles.append(processed_article)
        
        # Group articles by bias for comparison
        grouped_articles = group_articles_by_bias(processed_articles)
        
        return jsonify({
            "articles": processed_articles,
            "grouped": grouped_articles
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def detect_bias(article):
    """
    Detect political bias in an article based on content analysis.
    This is a simplified implementation for the MVP.
    """
    # Extract text for analysis
    title = article.get('title', '').lower()
    description = article.get('description', '').lower()
    source = article.get('source', '').lower()
    
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
    if 'fox' in source or 'breitbart' in source:
        source_bias_adjustment = 2  # Right-leaning adjustment
    elif 'msnbc' in source or 'huffington' in source:
        source_bias_adjustment = -2  # Left-leaning adjustment
    elif 'reuters' in source or 'ap' in source or 'associated press' in source:
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
        bias = article.get('bias', '')
        
        if "Left" in bias:
            grouped["left"].append(article)
        elif "Right" in bias:
            grouped["right"].append(article)
        elif bias == POLITICAL_BIAS["CENTER"]:
            grouped["center"].append(article)
        elif bias == POLITICAL_BIAS["NEUTRAL"]:
            grouped["neutral"].append(article)
    
    return grouped

@app.route('/api/compare')
def compare_articles():
    """Compare two articles from different political perspectives."""
    article1_id = request.args.get('article1')
    article2_id = request.args.get('article2')
    
    # In a real implementation, we would fetch the full articles
    # For MVP, we'll return a placeholder response
    return jsonify({
        "comparison": {
            "common_facts": ["Placeholder for common facts between articles"],
            "differences": ["Placeholder for key differences between articles"],
            "bias_indicators": ["Placeholder for detected bias indicators"]
        }
    })

@app.route('/api/topics')
def get_topics():
    """Return available news topics."""
    topics = [
        {"id": "politics", "name": "Politics"},
        {"id": "economy", "name": "Economy"},
        {"id": "technology", "name": "Technology"},
        {"id": "climate", "name": "Climate"},
        {"id": "health", "name": "Health"},
        {"id": "international", "name": "International"}
    ]
    return jsonify({"topics": topics})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
