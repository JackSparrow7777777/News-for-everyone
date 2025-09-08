// Main JavaScript for Spectrum News

document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentTopic = 'politics';
    let currentTimeRange = '7';
    let currentBias = null;
    let currentReliability = 70;
    let currentView = 'all';
    let articles = [];
    let selectedArticles = [];

    // Initialize the application
    init();

    function init() {
        // Fetch initial news data
        fetchNews();
        
        // Set up event listeners
        setupEventListeners();
    }

    function setupEventListeners() {
        // Topic selection
        document.querySelectorAll('.topics-list li').forEach(item => {
            item.addEventListener('click', function() {
                document.querySelectorAll('.topics-list li').forEach(i => i.classList.remove('active'));
                this.classList.add('active');
                currentTopic = this.getAttribute('data-topic');
                fetchNews();
            });
        });

        // Time range selection
        document.getElementById('time-range').addEventListener('change', function() {
            currentTimeRange = this.value;
            fetchNews();
        });

        // Bias filter
        document.querySelectorAll('.bias-option').forEach(option => {
            option.addEventListener('click', function() {
                const wasPreviouslySelected = this.classList.contains('active');
                
                document.querySelectorAll('.bias-option').forEach(opt => {
                    opt.classList.remove('active');
                });
                
                if (!wasPreviouslySelected) {
                    this.classList.add('active');
                    currentBias = this.getAttribute('data-bias');
                } else {
                    currentBias = null;
                }
                
                filterArticles();
            });
        });

        // Reliability slider
        document.getElementById('reliability-slider').addEventListener('input', function() {
            currentReliability = this.value;
            filterArticles();
        });

        // View options
        document.querySelectorAll('.view-option').forEach(option => {
            option.addEventListener('click', function() {
                document.querySelectorAll('.view-option').forEach(opt => {
                    opt.classList.remove('active');
                });
                this.classList.add('active');
                currentView = this.getAttribute('data-view');
                renderArticles();
            });
        });

        // Modal close buttons
        document.querySelectorAll('.close-modal').forEach(button => {
            button.addEventListener('click', function() {
                document.getElementById('article-modal').style.display = 'none';
                document.getElementById('comparison-modal').style.display = 'none';
            });
        });

        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === document.getElementById('article-modal')) {
                document.getElementById('article-modal').style.display = 'none';
            }
            if (event.target === document.getElementById('comparison-modal')) {
                document.getElementById('comparison-modal').style.display = 'none';
            }
        });
    }

    function fetchNews() {
        const newsContainer = document.getElementById('news-container');
        newsContainer.innerHTML = '<div class="loading">Loading news articles...</div>';

        // Build API URL with parameters
        const apiUrl = `/api/news?topic=${currentTopic}&time_range=${currentTimeRange}`;

        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                articles = data.articles;
                renderArticles();
            })
            .catch(error => {
                console.error('Error fetching news:', error);
                newsContainer.innerHTML = `<div class="error">Error loading news articles. Please try again later.</div>`;
            });
    }

    function filterArticles() {
        let filteredArticles = [...articles];

        // Filter by bias if selected
        if (currentBias) {
            filteredArticles = filteredArticles.filter(article => {
                const bias = article.bias.toLowerCase();
                
                switch(currentBias) {
                    case 'left':
                        return bias.includes('left');
                    case 'center-left':
                        return bias.includes('center left');
                    case 'center':
                        return bias === 'center';
                    case 'center-right':
                        return bias.includes('center right');
                    case 'right':
                        return bias.includes('right');
                    default:
                        return true;
                }
            });
        }

        // Filter by reliability
        filteredArticles = filteredArticles.filter(article => {
            return article.reliability >= currentReliability;
        });

        // Update the articles display
        renderFilteredArticles(filteredArticles);
    }

    function renderFilteredArticles(filteredArticles) {
        const newsContainer = document.getElementById('news-container');
        
        if (filteredArticles.length === 0) {
            newsContainer.innerHTML = '<div class="no-results">No articles match your filters. Try adjusting your criteria.</div>';
            return;
        }

        let html = '';
        
        filteredArticles.forEach(article => {
            html += createArticleCard(article);
        });
        
        newsContainer.innerHTML = html;
        
        // Add event listeners to the newly created article cards
        addArticleCardListeners();
    }

    function renderArticles() {
        const newsContainer = document.getElementById('news-container');
        
        if (articles.length === 0) {
            newsContainer.innerHTML = '<div class="no-results">No articles available. Try a different topic or time range.</div>';
            return;
        }

        let html = '';
        
        if (currentView === 'all') {
            // Show all articles
            articles.forEach(article => {
                html += createArticleCard(article);
            });
        } 
        else if (currentView === 'by-topic') {
            // Group articles by topic
            const topics = {};
            
            articles.forEach(article => {
                const categories = article.categories || [];
                categories.forEach(category => {
                    if (!topics[category]) {
                        topics[category] = [];
                    }
                    topics[category].push(article);
                });
            });
            
            for (const topic in topics) {
                html += `<div class="topic-section">
                    <h2 class="topic-title">${topic.charAt(0).toUpperCase() + topic.slice(1)}</h2>
                    <div class="topic-articles">`;
                
                topics[topic].forEach(article => {
                    html += createArticleCard(article);
                });
                
                html += `</div></div>`;
            }
        } 
        else if (currentView === 'compare') {
            // Show comparison view with selection options
            html += `<div class="comparison-view">
                <h2>Select articles to compare</h2>
                <p>Choose two articles from different perspectives to compare their coverage.</p>
                <div class="selection-container">`;
            
            articles.forEach(article => {
                html += createArticleCard(article, true);
            });
            
            html += `</div>
                <div class="comparison-actions">
                    <button id="compare-button" class="compare-button" disabled>Compare Selected Articles</button>
                </div>
            </div>`;
        }
        
        newsContainer.innerHTML = html;
        
        // Add event listeners to the newly created article cards
        addArticleCardListeners();
    }

    function createArticleCard(article, selectable = false) {
        // Determine bias badge class
        let biasBadgeClass = 'neutral-badge';
        if (article.bias.includes('Left')) {
            biasBadgeClass = article.bias.includes('Extreme') ? 'left-badge' : 
                            (article.bias.includes('Center') ? 'center-left-badge' : 'left-badge');
        } else if (article.bias.includes('Right')) {
            biasBadgeClass = article.bias.includes('Extreme') ? 'right-badge' : 
                            (article.bias.includes('Center') ? 'center-right-badge' : 'right-badge');
        } else if (article.bias === 'Center') {
            biasBadgeClass = 'center-badge';
        }

        // Format date
        const publishedDate = new Date(article.published_at);
        const formattedDate = publishedDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });

        // Create article card HTML
        return `
        <div class="article-card" data-id="${article.url}">
            <div class="article-source">
                <div class="source-logo"></div>
                <div class="source-info">
                    <div class="source-name">${article.source}</div>
                    <div class="source-meta">
                        <span class="reliability-badge">${article.reliability}% Reliable</span>
                        <span class="bias-badge ${biasBadgeClass}">${article.bias}</span>
                    </div>
                </div>
                ${selectable ? `<div class="article-select">
                    <input type="checkbox" class="select-article" data-id="${article.url}">
                </div>` : ''}
            </div>
            <div class="article-content">
                <h3 class="article-title">${article.title}</h3>
                <div class="article-meta">
                    <span class="article-date">${formattedDate}</span>
                </div>
                <p class="article-description">${article.description}</p>
                <div class="article-actions">
                    <button class="view-article" data-id="${article.url}">View Analysis</button>
                    <button class="read-full" data-url="${article.url}">Read Full Article</button>
                </div>
            </div>
        </div>`;
    }

    function addArticleCardListeners() {
        // View article analysis
        document.querySelectorAll('.view-article').forEach(button => {
            button.addEventListener('click', function() {
                const articleId = this.getAttribute('data-id');
                const article = articles.find(a => a.url === articleId);
                
                if (article) {
                    showArticleModal(article);
                }
            });
        });

        // Read full article
        document.querySelectorAll('.read-full').forEach(button => {
            button.addEventListener('click', function() {
                const url = this.getAttribute('data-url');
                window.open(url, '_blank');
            });
        });

        // Article selection for comparison
        document.querySelectorAll('.select-article').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const articleId = this.getAttribute('data-id');
                
                if (this.checked) {
                    if (selectedArticles.length < 2) {
                        selectedArticles.push(articleId);
                    } else {
                        this.checked = false;
                        alert('You can only select two articles for comparison.');
                    }
                } else {
                    const index = selectedArticles.indexOf(articleId);
                    if (index > -1) {
                        selectedArticles.splice(index, 1);
                    }
                }
                
                // Enable/disable compare button
                const compareButton = document.getElementById('compare-button');
                if (compareButton) {
                    compareButton.disabled = selectedArticles.length !== 2;
                }
            });
        });

        // Compare button
        const compareButton = document.getElementById('compare-button');
        if (compareButton) {
            compareButton.addEventListener('click', function() {
                if (selectedArticles.length === 2) {
                    compareArticles(selectedArticles[0], selectedArticles[1]);
                }
            });
        }
    }

    function showArticleModal(article) {
        const modalContent = document.getElementById('article-detail');
        
        // Format date
        const publishedDate = new Date(article.published_at);
        const formattedDate = publishedDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });

        // Create modal content
        modalContent.innerHTML = `
            <h2>${article.title}</h2>
            <div class="article-source-info">
                <span class="source">${article.source}</span>
                <span class="date">${formattedDate}</span>
            </div>
            <div class="article-bias-info">
                <div class="bias-indicator">
                    <span>Political Bias: </span>
                    <span class="bias-value">${article.bias}</span>
                </div>
                <div class="reliability-indicator">
                    <span>Source Reliability: </span>
                    <span class="reliability-value">${article.reliability}%</span>
                </div>
            </div>
            <div class="article-full-description">
                <p>${article.description}</p>
            </div>
            <div class="article-actions">
                <a href="${article.url}" target="_blank" class="read-original">Read Original Article</a>
            </div>
        `;
        
        // Show the modal
        document.getElementById('article-modal').style.display = 'block';
    }

    function compareArticles(articleId1, articleId2) {
        const article1 = articles.find(a => a.url === articleId1);
        const article2 = articles.find(a => a.url === articleId2);
        
        if (!article1 || !article2) {
            alert('Error loading articles for comparison.');
            return;
        }

        // Format dates
        const formatDate = (dateStr) => {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        };

        // Populate comparison modal
        const leftArticleHeader = document.querySelector('.left-article .article-header');
        const leftArticleContent = document.querySelector('.left-article .article-content');
        const rightArticleHeader = document.querySelector('.right-article .article-header');
        const rightArticleContent = document.querySelector('.right-article .article-content');
        
        leftArticleHeader.innerHTML = `
            <h3>${article1.title}</h3>
            <div class="article-source-meta">
                <span class="source">${article1.
(Content truncated due to size limit. Use line ranges to read in chunks)


live

Jump to live
