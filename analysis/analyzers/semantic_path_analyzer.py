"""
Semantic Path Analyzer - Advanced URL semantic understanding

Purpose: Extract deep semantic meaning from URL structures using
         NLP techniques, topic modeling, and pattern recognition
"""

import re
from collections import Counter, defaultdict
from typing import Dict, List
from urllib.parse import parse_qs

# Use shared utilities to eliminate redundancy
from analysis.utils.url_utilities import get_path_depth, parse_url_components


class SemanticPathAnalyzer:
    """Advanced semantic analysis of URL paths."""

    # extended stop words
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'www', 'com', 'org', 'net', 'html',
        'htm', 'php', 'aspx', 'jsp', 'default', 'index', 'home', 'main',
        'page', 'pages', 'site', 'sites', 'web'
    }

    # semantic categories
    SEMANTIC_PATTERNS = {
        'educational': ['course', 'class', 'student', 'faculty', 'academic', 'education', 'school', 'university', 'college', 'learning', 'study', 'degree', 'program', 'admission'],
        'commerce': ['shop', 'store', 'buy', 'cart', 'checkout', 'product', 'price', 'payment', 'order', 'purchase'],
        'content': ['blog', 'article', 'post', 'news', 'story', 'press', 'release', 'publication'],
        'user': ['profile', 'account', 'user', 'login', 'register', 'signup', 'dashboard', 'settings'],
        'information': ['about', 'info', 'contact', 'faq', 'help', 'support', 'guide', 'documentation'],
        'media': ['image', 'video', 'gallery', 'photo', 'media', 'download', 'file'],
        'search': ['search', 'find', 'query', 'results', 'browse', 'explore'],
        'community': ['forum', 'community', 'discussion', 'comment', 'social', 'share'],
        'administrative': ['admin', 'manage', 'dashboard', 'control', 'settings', 'config'],
        'events': ['event', 'calendar', 'schedule', 'date', 'conference', 'meeting']
    }

    # action verbs
    ACTION_VERBS = {
        'create': ['create', 'new', 'add', 'insert', 'post'],
        'read': ['view', 'show', 'display', 'get', 'fetch', 'read', 'list'],
        'update': ['edit', 'update', 'modify', 'change', 'revise'],
        'delete': ['delete', 'remove', 'destroy', 'cancel'],
        'search': ['search', 'find', 'query', 'filter', 'browse'],
        'auth': ['login', 'logout', 'signin', 'signout', 'register', 'signup']
    }

    def __init__(self):
        self.urls = []
        self.token_frequency = Counter()
        self.bigrams = Counter()
        self.trigrams = Counter()
        self.semantic_distribution = defaultdict(int)
        self.action_distribution = defaultdict(int)
        self.path_templates = Counter()

    def analyze(self, data: List[Dict]) -> Dict:
        """
        Perform semantic path analysis.

        Args:
            data: List of URL dictionaries from JSONL

        Returns:
            Semantic analysis results
        """
        # extract urls
        self.urls = [item.get('url', '') for item in data if item.get('url')]

        # process each url
        for item in data:
            self._process_url(item)

        results = {
            'vocabulary': self._analyze_vocabulary(),
            'semantic_categories': self._categorize_semantically(),
            'action_analysis': self._analyze_actions(),
            'ngram_analysis': self._analyze_ngrams(),
            'template_extraction': self._extract_templates(),
            'parameter_analysis': self._analyze_parameters(data),
            'content_type_prediction': self._predict_content_types(),
            'url_quality': self._assess_url_quality(),
            'seo_insights': self._generate_seo_insights()
        }

        return results

    def _process_url(self, item: Dict):
        """Process individual URL for semantic features."""

        url = item.get('url', '')
        if not url:
            return

        # Use shared utility for parsing
        components = parse_url_components(url)
        from urllib.parse import unquote
        path = unquote(components['path'])

        # tokenize path
        tokens = self._tokenize_path(path)

        # update frequency
        self.token_frequency.update(tokens)

        # generate n-grams
        if len(tokens) >= 2:
            for i in range(len(tokens) - 1):
                self.bigrams[(tokens[i], tokens[i + 1])] += 1

        if len(tokens) >= 3:
            for i in range(len(tokens) - 2):
                self.trigrams[(tokens[i], tokens[i + 1], tokens[i + 2])] += 1

        # semantic categorization
        for category, keywords in self.SEMANTIC_PATTERNS.items():
            if any(kw in token for token in tokens for kw in keywords):
                self.semantic_distribution[category] += 1

        # action detection
        for action, verbs in self.ACTION_VERBS.items():
            if any(verb in token for token in tokens for verb in verbs):
                self.action_distribution[action] += 1

        # template extraction
        template = self._extract_template(path)
        self.path_templates[template] += 1

    def _tokenize_path(self, path: str) -> List[str]:
        """Tokenize URL path into meaningful terms."""

        # split on common separators
        tokens = re.split(r'[/\-_.]', path.lower())

        # filter out empty, stop words, and file extensions
        tokens = [
            t for t in tokens
            if t and
            t not in self.STOP_WORDS and
            not t.isdigit() and
            len(t) > 1 and
            not re.match(r'^\d+$', t)
        ]

        # split camelcase and pascalcase
        expanded_tokens = []
        for token in tokens:
            # split on capital letters
            parts = re.findall(r'[a-z]+|[A-Z][a-z]*', token)
            if parts:
                expanded_tokens.extend([p.lower() for p in parts])
            else:
                expanded_tokens.append(token)

        return [t for t in expanded_tokens if t not in self.STOP_WORDS]

    def _extract_template(self, path: str) -> str:
        """Extract URL template by replacing dynamic parts."""

        # replace numbers with {num}
        template = re.sub(r'\d+', '{num}', path)

        # replace uuids with {uuid}
        template = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{uuid}',
            template,
            flags=re.IGNORECASE
        )

        # replace dates with {date}
        template = re.sub(r'\d{4}[-/]\d{2}[-/]\d{2}', '{date}', template)
        template = re.sub(r'\d{4}/\d{2}', '{year-month}', template)

        # replace long alphanumeric strings with {id}
        template = re.sub(r'[a-z0-9]{20,}', '{id}', template, flags=re.IGNORECASE)

        return template

    def _analyze_vocabulary(self) -> Dict:
        """Analyze vocabulary richness and distribution."""

        total_tokens = sum(self.token_frequency.values())
        unique_tokens = len(self.token_frequency)

        # vocabulary richness (type-token ratio)
        ttr = unique_tokens / total_tokens if total_tokens > 0 else 0

        return {
            'total_tokens': total_tokens,
            'unique_tokens': unique_tokens,
            'type_token_ratio': ttr,
            'top_tokens': dict(self.token_frequency.most_common(50)),
            'vocabulary_diversity': 'high' if ttr > 0.5 else 'medium' if ttr > 0.3 else 'low'
        }

    def _categorize_semantically(self) -> Dict:
        """Categorize URLs by semantic meaning."""

        total = sum(self.semantic_distribution.values())

        categories = {
            category: {
                'count': count,
                'percentage': (count / len(self.urls)) * 100 if self.urls else 0
            }
            for category, count in self.semantic_distribution.items()
        }

        # find dominant category
        if self.semantic_distribution:
            dominant = max(self.semantic_distribution.items(), key=lambda x: x[1])
            categories['dominant_category'] = {
                'name': dominant[0],
                'count': dominant[1]
            }

        return categories

    def _analyze_actions(self) -> Dict:
        """Analyze action verbs in URLs."""

        total_actions = sum(self.action_distribution.values())

        actions = {
            action: {
                'count': count,
                'percentage': (count / total_actions) * 100 if total_actions > 0 else 0
            }
            for action, count in self.action_distribution.items()
        }

        # crud distribution
        crud = {
            'create': actions.get('create', {}).get('count', 0),
            'read': actions.get('read', {}).get('count', 0),
            'update': actions.get('update', {}).get('count', 0),
            'delete': actions.get('delete', {}).get('count', 0)
        }

        actions['crud_distribution'] = crud

        return actions

    def _analyze_ngrams(self) -> Dict:
        """Analyze common n-gram patterns."""

        return {
            'top_bigrams': [
                {' '.join(bg): count}
                for bg, count in self.bigrams.most_common(20)
            ],
            'top_trigrams': [
                {' '.join(tg): count}
                for tg, count in self.trigrams.most_common(15)
            ],
            'bigram_diversity': len(self.bigrams),
            'trigram_diversity': len(self.trigrams)
        }

    def _extract_templates(self) -> Dict:
        """Extract common URL templates."""

        total_urls = len(self.urls)

        templates = [
            {
                'template': template,
                'count': count,
                'percentage': (count / total_urls) * 100 if total_urls > 0 else 0
            }
            for template, count in self.path_templates.most_common(30)
        ]

        # calculate template diversity
        unique_templates = len(self.path_templates)
        template_diversity = unique_templates / total_urls if total_urls > 0 else 0

        return {
            'top_templates': templates,
            'total_unique_templates': unique_templates,
            'template_diversity': template_diversity,
            'diversity_level': 'high' if template_diversity > 0.7 else 'medium' if template_diversity > 0.3 else 'low'
        }

    def _analyze_parameters(self, data: List[Dict]) -> Dict:
        """Analyze query parameters."""

        param_names = Counter()
        param_values = defaultdict(Counter)

        for item in data:
            url = item.get('url', '')
            # Use shared utility for parsing
            components = parse_url_components(url)

            if components['has_query']:
                params = parse_qs(components['query'])

                for key, values in params.items():
                    param_names[key] += 1

                    for value in values:
                        # store first 100 chars of value
                        param_values[key][value[:100]] += 1

        # Count parameterized URLs
        parameterized_count = sum(1 for item in data if parse_url_components(item.get('url', ''))['has_query'])

        return {
            'total_parameterized_urls': parameterized_count,
            'top_parameter_names': dict(param_names.most_common(20)),
            'common_parameters': {
                key: dict(values.most_common(10))
                for key, values in list(param_values.items())[:10]
            }
        }

    def _predict_content_types(self) -> Dict:
        """Predict content types based on URL patterns."""

        predictions = defaultdict(int)

        for url in self.urls:
            path_lower = url.lower()

            if any(x in path_lower for x in ['/api/', '/rest/', '/graphql']):
                predictions['API Endpoint'] += 1
            elif any(x in path_lower for x in ['/blog/', '/post/', '/article/', '/news/']):
                predictions['Blog/Article'] += 1
            elif any(x in path_lower for x in ['/product/', '/item/', '/shop/']):
                predictions['Product Page'] += 1
            elif any(x in path_lower for x in ['/user/', '/profile/', '/account/']):
                predictions['User Profile'] += 1
            elif any(x in path_lower for x in ['/admin/', '/dashboard/', '/manage/']):
                predictions['Admin Page'] += 1
            elif any(x in path_lower for x in ['/search', '/results', '/find']):
                predictions['Search Results'] += 1
            elif any(x in path_lower for x in ['/category/', '/tag/', '/archive/']):
                predictions['Category/Archive'] += 1
            elif any(x in path_lower for x in ['/about', '/contact', '/faq', '/help']):
                predictions['Information Page'] += 1
            else:
                predictions['General Content'] += 1

        total = len(self.urls)

        return {
            type_name: {
                'count': count,
                'percentage': (count / total) * 100 if total > 0 else 0
            }
            for type_name, count in predictions.items()
        }

    def _assess_url_quality(self) -> Dict:
        """Assess SEO and usability quality of URLs."""

        quality_metrics = {
            'too_long': 0,  # > 100 chars
            'too_short': 0,  # < 20 chars
            'optimal_length': 0,  # 20-100 chars
            'has_numbers': 0,
            'has_underscores': 0,
            'has_uppercase': 0,
            'too_deep': 0,  # > 5 levels
            'optimal_depth': 0,  # 2-4 levels
            'keyword_rich': 0
        }

        for url in self.urls:
            url_len = len(url)
            # Use shared utility for parsing (eliminates redundancy)
            components = parse_url_components(url)
            path = components['path']

            # length assessment
            if url_len > 100:
                quality_metrics['too_long'] += 1
            elif url_len < 20:
                quality_metrics['too_short'] += 1
            else:
                quality_metrics['optimal_length'] += 1

            # pattern checks
            if re.search(r'\d', path):
                quality_metrics['has_numbers'] += 1

            if '_' in path:
                quality_metrics['has_underscores'] += 1

            if re.search(r'[A-Z]', path):
                quality_metrics['has_uppercase'] += 1

            # depth check using shared utility (eliminates redundancy)
            depth = get_path_depth(url)
            if depth > 5:
                quality_metrics['too_deep'] += 1
            elif 2 <= depth <= 4:
                quality_metrics['optimal_depth'] += 1

            # keyword richness (at least 2 meaningful words)
            tokens = self._tokenize_path(path)
            if len(tokens) >= 2:
                quality_metrics['keyword_rich'] += 1

        # calculate quality score
        total = len(self.urls)
        if total > 0:
            quality_score = (
                (quality_metrics['optimal_length'] / total) * 30 +
                (quality_metrics['optimal_depth'] / total) * 30 +
                (quality_metrics['keyword_rich'] / total) * 40
            )
        else:
            quality_score = 0

        return {
            'metrics': quality_metrics,
            'quality_score': quality_score,
            'quality_grade': self._get_grade(quality_score)
        }

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _generate_seo_insights(self) -> Dict:
        """Generate SEO-specific insights."""

        insights = {
            'recommendations': [],
            'issues': [],
            'strengths': []
        }

        # analyze token frequency for keyword optimization
        top_keywords = self.token_frequency.most_common(10)

        if top_keywords:
            insights['strengths'].append(
                f"Top keyword: '{top_keywords[0][0]}' appears {top_keywords[0][1]} times"
            )

        # check url structure quality
        avg_url_length = sum(len(url) for url in self.urls) / len(self.urls) if self.urls else 0

        if avg_url_length > 100:
            insights['issues'].append("URLs are too long on average. Recommend shortening.")
            insights['recommendations'].append("Keep URLs under 100 characters for better SEO")

        # check for keyword stuffing
        if top_keywords and top_keywords[0][1] > len(self.urls) * 0.5:
            insights['issues'].append("Possible keyword stuffing detected")

        # check template diversity
        template_div = len(self.path_templates) / len(self.urls) if self.urls else 0
        if template_div < 0.1:
            insights['issues'].append("Low URL diversity - too many similar URLs")
        else:
            insights['strengths'].append("Good URL diversity")

        return insights


def execute(data: List[Dict]) -> Dict:
    """
    Main execution function for semantic path analysis.

    Args:
        data: List of URL dictionaries from JSONL

    Returns:
        Semantic analysis results
    """
    analyzer = SemanticPathAnalyzer()
    return analyzer.analyze(data)


def print_summary(results: Dict):
    """Print summary of semantic analysis."""

    print("Semantic path analysis summary")

    vocab = results['vocabulary']
    print(f"Total Tokens: {vocab['total_tokens']:,}")
    print(f"Unique Tokens: {vocab['unique_tokens']:,}")
    print(f"Diversity: {vocab['vocabulary_diversity'].upper()}")

    semantics = results['semantic_categories']
    if 'dominant_category' in semantics:
        dom = semantics['dominant_category']
        print(f"Dominant Category: {dom['name'].upper()} ({dom['count']} pages)")

    content = results['content_type_prediction']
    print("Top content types:")
    for ctype, data in sorted(content.items(), key=lambda x: x[1]['count'], reverse=True)[:3]:
        print(f"{ctype}: {data['percentage']:.1f}%")

    quality = results['url_quality']
    print(f"URL Quality Score: {quality['quality_score']:.1f}/100 (Grade: {quality['quality_grade']})")
