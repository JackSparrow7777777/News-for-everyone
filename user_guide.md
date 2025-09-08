# Spectrum News - User Guide

## Overview
Spectrum News is a news aggregation website that classifies articles across the political spectrum and offers balanced analysis. This guide will help you understand how to use the platform effectively.

## Getting Started

### Running the Application
1. Navigate to the project directory: `cd /home/ubuntu/spectrum_news`
2. Activate the virtual environment: `source venv/bin/activate`
3. Run the Flask application: `python src/main.py`
4. Access the website at: `http://localhost:5000`

### API Key Configuration
The application uses TheNewsAPI.com for news aggregation. A demo API key is included in the `.env` file for testing purposes. For production use, you should:

1. Register for an account at [TheNewsAPI.com](https://www.thenewsapi.com/)
2. Obtain your API key
3. Update the `.env` file with your key: `NEWS_API_KEY=your_api_key_here`

## Features

### Political Bias Classification
Articles are classified into the following categories:
- **Extreme Left/Right**: Articles with inflammatory language, citations of extreme communities, or conspiracy theories
- **Moderate Left/Right**: Articles with subtle favorable language toward left/right positions
- **Center Left/Right**: Articles with balanced presentation but with slight leaning
- **Center**: Articles with balanced presentation of both perspectives
- **Mechanically Neutral**: Rigid, report-style writing focused on facts and numbers

### Source Reliability
Sources are rated on a scale of 0-100% based on:
- Established reputation
- Transparency of methodology
- History of corrections
- Diversity of perspectives
- Citation practices

### Filtering Options
- **Political Bias**: Filter articles by their political leaning
- **Source Reliability**: Set minimum reliability threshold
- **Time Range**: Choose from past 24 hours to past 3 months
- **Topics**: Filter by categories like Politics, Economy, Technology, etc.

### View Options
- **All**: View all articles in a single feed
- **By Topic**: Group articles by their topics
- **Compare**: Select two articles to compare their coverage of the same event

## Using the Comparison Feature
1. Click on the "Compare" view option
2. Select two articles from different perspectives
3. Click the "Compare Selected Articles" button
4. Review the common facts and key differences between the articles

## Project Structure
- `src/main.py`: Main Flask application
- `src/templates/`: HTML templates
- `src/static/`: CSS, JavaScript, and image files
- `design_docs/`: Design documentation
- `validation_report.md`: Validation results

## Future Enhancements
Future versions of Spectrum News may include:
- Machine learning for more accurate bias detection
- User accounts for personalized experiences
- Real-time updates for breaking news
- More detailed analytics on news coverage patterns

## Support
For any questions or issues, please refer to the documentation in the `design_docs/` directory or contact the development team.
