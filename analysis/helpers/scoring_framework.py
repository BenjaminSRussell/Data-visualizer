"""
Multi-Dimensional Scoring Framework

Purpose: Replace single-dimension scores with context-aware composite metrics.
Current scoring (e.g., url_health in statistical_analyzer.py:260-290) treats all
URLs equally. The 73.1 overall score (README line 9) obscures that entry pages
might score 90 while utility pages score 40.

Integration Points:
- Enhances scoring in statistical_analyzer.py and data_quality_analyzer.py
- Provides context-aware scoring that considers page importance and domain type
"""

from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import numpy as np
from urllib.parse import urlparse


# Domain-specific rubrics
DOMAIN_RUBRICS = {
    'ecommerce': {
        'weights': {
            'url_structure': 0.25,
            'parameter_quality': 0.20,
            'depth_appropriateness': 0.20,
            'internal_linking': 0.20,
            'mobile_friendliness': 0.15
        },
        'expectations': {
            'avg_depth': (2, 4),
            'max_params': 3,
            'fragment_tolerance': 0.05
        }
    },
    'content': {
        'weights': {
            'url_structure': 0.30,
            'seo_quality': 0.25,
            'depth_appropriateness': 0.20,
            'internal_linking': 0.15,
            'freshness': 0.10
        },
        'expectations': {
            'avg_depth': (2, 3),
            'max_params': 2,
            'fragment_tolerance': 0.10
        }
    },
    'saas': {
        'weights': {
            'url_structure': 0.20,
            'parameter_quality': 0.15,
            'depth_appropriateness': 0.15,
            'internal_linking': 0.20,
            'spa_compatibility': 0.30
        },
        'expectations': {
            'avg_depth': (1, 3),
            'max_params': 5,
            'fragment_tolerance': 0.40  # SPAs use fragments heavily
        }
    },
    'documentation': {
        'weights': {
            'url_structure': 0.35,
            'depth_appropriateness': 0.25,
            'internal_linking': 0.25,
            'breadcrumb_quality': 0.15
        },
        'expectations': {
            'avg_depth': (3, 5),
            'max_params': 1,
            'fragment_tolerance': 0.20
        }
    }
}


# Page importance classification
PAGE_IMPORTANCE_INDICATORS = {
    'entry_point': {
        'patterns': [r'^/$', r'^/index', r'^/home'],
        'depth_range': (0, 1),
        'weight_multiplier': 2.0
    },
    'high_value': {
        'patterns': [r'/product/', r'/pricing', r'/contact', r'/about'],
        'depth_range': (0, 2),
        'weight_multiplier': 1.5
    },
    'navigation': {
        'patterns': [r'/category/', r'/browse', r'/search'],
        'depth_range': (1, 2),
        'weight_multiplier': 1.3
    },
    'content': {
        'patterns': [r'/blog/', r'/article/', r'/post/'],
        'depth_range': (2, 4),
        'weight_multiplier': 1.0
    },
    'utility': {
        'patterns': [r'/api/', r'/assets/', r'/static/', r'/admin/'],
        'depth_range': (1, 5),
        'weight_multiplier': 0.5
    }
}


def calculate_contextual_score(data: List[Dict], domain_type: Optional[str] = None) -> Dict:
    """
    Calculate context-aware composite score that weights URLs by importance.

    Addresses the issue that a 73.1 overall score obscures important details.

    Args:
        data: List of URL dictionaries
        domain_type: Type of domain ('ecommerce', 'content', 'saas', 'documentation')

    Returns:
        Dictionary with contextual scoring breakdown

    Example:
        {
            'overall_score': 73.1,
            'weighted_score': 82.5,  # Weighted by importance
            'score_by_importance': {
                'entry_point': 92.0,
                'high_value': 85.0,
                'content': 70.0,
                'utility': 45.0
            },
            'insights': [...]
        }
    """
    if not data:
        return {
            'overall_score': 0,
            'available': False
        }

    # Auto-detect domain type if not provided
    if domain_type is None:
        domain_type = _detect_domain_type(data)

    # Get rubric for domain
    rubric = DOMAIN_RUBRICS.get(domain_type, DOMAIN_RUBRICS['content'])

    # Classify URLs by importance
    url_classifications = {}
    for item in data:
        url = item.get('url', '')
        if not url:
            continue

        importance = _classify_page_importance(url, item.get('depth', 0))
        url_classifications[url] = importance

    # Calculate scores by importance category
    score_by_importance = {}
    url_count_by_importance = Counter(url_classifications.values())

    for importance_level in PAGE_IMPORTANCE_INDICATORS.keys():
        # Get URLs in this importance level
        urls_in_level = [
            item for item in data
            if url_classifications.get(item.get('url', '')) == importance_level
        ]

        if urls_in_level:
            level_score = _calculate_level_score(urls_in_level, rubric)
            score_by_importance[importance_level] = level_score
        else:
            score_by_importance[importance_level] = None

    # Calculate overall unweighted score
    all_scores = [s for s in score_by_importance.values() if s is not None]
    overall_score = np.mean(all_scores) if all_scores else 0

    # Calculate importance-weighted score
    weighted_score = 0
    total_weight = 0

    for importance_level, score in score_by_importance.items():
        if score is not None:
            count = url_count_by_importance[importance_level]
            multiplier = PAGE_IMPORTANCE_INDICATORS[importance_level]['weight_multiplier']
            weighted_score += score * count * multiplier
            total_weight += count * multiplier

    weighted_score = weighted_score / total_weight if total_weight > 0 else 0

    # Generate insights
    insights = _generate_contextual_insights(
        score_by_importance,
        url_count_by_importance,
        domain_type
    )

    return {
        'overall_score': round(overall_score, 2),
        'weighted_score': round(weighted_score, 2),
        'domain_type': domain_type,
        'score_by_importance': {k: round(v, 2) if v is not None else None for k, v in score_by_importance.items()},
        'url_count_by_importance': dict(url_count_by_importance),
        'insights': insights,
        'rubric_used': domain_type,
        'available': True
    }


def generate_comparative_scores(data: List[Dict], domain_type: str, benchmark_data: Optional[Dict] = None) -> Dict:
    """
    Generate comparative scores (this site vs typical sites in category).

    Args:
        data: List of URL dictionaries
        domain_type: Type of domain for comparison
        benchmark_data: Optional benchmark data (uses defaults if not provided)

    Returns:
        Dictionary with comparative analysis

    Example:
        {
            'your_score': 73.1,
            'benchmark_average': 68.5,
            'percentile': 65,  # Better than 65% of sites
            'comparison': {
                'url_structure': {'your': 80, 'benchmark': 75},
                'depth': {'your': 70, 'benchmark': 65}
            }
        }
    """
    if not data:
        return {
            'your_score': 0,
            'available': False
        }

    # Use default benchmarks if not provided
    if benchmark_data is None:
        benchmark_data = _get_default_benchmarks(domain_type)

    # Calculate your scores
    your_metrics = _calculate_detailed_metrics(data)

    # Compare each dimension
    comparison = {}
    dimension_scores = []

    for dimension, your_value in your_metrics.items():
        benchmark_value = benchmark_data.get(dimension, your_value)

        # Calculate relative score (0-100)
        if benchmark_value > 0:
            relative_score = (your_value / benchmark_value) * 100
        else:
            relative_score = 100

        # Cap at reasonable values
        relative_score = min(150, max(0, relative_score))

        comparison[dimension] = {
            'your_value': round(your_value, 2),
            'benchmark_value': round(benchmark_value, 2),
            'relative_score': round(relative_score, 2),
            'status': 'above' if your_value > benchmark_value else 'below' if your_value < benchmark_value else 'equal'
        }

        dimension_scores.append(relative_score)

    # Calculate overall percentile
    overall_relative = np.mean(dimension_scores) if dimension_scores else 50
    percentile = min(99, max(1, int(overall_relative)))

    # Calculate your overall score
    contextual_result = calculate_contextual_score(data, domain_type)
    your_score = contextual_result['weighted_score']

    return {
        'your_score': round(your_score, 2),
        'benchmark_average': benchmark_data.get('overall', 70.0),
        'percentile': percentile,
        'comparison': comparison,
        'strengths': [dim for dim, comp in comparison.items() if comp['status'] == 'above'],
        'weaknesses': [dim for dim, comp in comparison.items() if comp['status'] == 'below'],
        'domain_type': domain_type,
        'available': True
    }


def decompose_score(data: List[Dict], url: Optional[str] = None) -> Dict:
    """
    Provide actionable score decomposition (which factors hurt most).

    Shows exactly what's pulling the score down and how to fix it.

    Args:
        data: List of URL dictionaries
        url: Specific URL to analyze (if None, analyzes overall)

    Returns:
        Dictionary with score decomposition

    Example:
        {
            'total_score': 73.1,
            'component_scores': {
                'url_structure': {'score': 85, 'weight': 0.3, 'contribution': 25.5},
                'depth': {'score': 60, 'weight': 0.2, 'contribution': 12.0},
                ...
            },
            'top_issues': [
                {'issue': 'excessive_depth', 'impact': -15, 'fix': 'Flatten hierarchy'},
                ...
            ]
        }
    """
    if not data:
        return {
            'total_score': 0,
            'available': False
        }

    # Filter to specific URL if requested
    if url:
        data = [item for item in data if item.get('url') == url]
        if not data:
            return {
                'total_score': 0,
                'error': 'URL not found',
                'available': False
            }

    # Calculate component scores
    components = {
        'url_structure': _score_url_structure(data),
        'depth_appropriateness': _score_depth(data),
        'parameter_quality': _score_parameters(data),
        'internal_linking': _score_linking(data),
        'seo_quality': _score_seo(data)
    }

    # Default weights (can be customized by domain)
    weights = {
        'url_structure': 0.25,
        'depth_appropriateness': 0.20,
        'parameter_quality': 0.20,
        'internal_linking': 0.20,
        'seo_quality': 0.15
    }

    # Calculate weighted total
    total_score = sum(
        components[comp]['score'] * weights[comp]
        for comp in components.keys()
    )

    # Build component breakdown
    component_scores = {}
    for comp, score_data in components.items():
        component_scores[comp] = {
            'score': round(score_data['score'], 2),
            'weight': weights[comp],
            'contribution': round(score_data['score'] * weights[comp], 2),
            'max_contribution': round(100 * weights[comp], 2),
            'issues': score_data.get('issues', [])
        }

    # Identify top issues by impact
    all_issues = []
    for comp, comp_data in component_scores.items():
        for issue in comp_data.get('issues', []):
            all_issues.append({
                'component': comp,
                'issue': issue['description'],
                'impact': round((100 - comp_data['score']) * weights[comp], 2),
                'fix': issue['fix']
            })

    # Sort by impact
    all_issues.sort(key=lambda x: x['impact'], reverse=True)

    return {
        'total_score': round(total_score, 2),
        'component_scores': component_scores,
        'top_issues': all_issues[:10],  # Top 10 issues
        'quick_wins': [issue for issue in all_issues if 'easy' in issue['fix'].lower()][:5],
        'available': True
    }


def apply_domain_rubric(data: List[Dict], domain_type: str, custom_weights: Optional[Dict] = None) -> Dict:
    """
    Apply domain-specific rubric with custom weight adjustments.

    Args:
        data: List of URL dictionaries
        domain_type: Type of domain
        custom_weights: Optional custom weight overrides

    Returns:
        Dictionary with rubric-based scoring

    Example:
        {
            'score': 78.5,
            'domain_type': 'ecommerce',
            'rubric_applied': {...},
            'meets_expectations': {
                'avg_depth': True,
                'max_params': False,
                ...
            }
        }
    """
    if not data:
        return {
            'score': 0,
            'available': False
        }

    # Get base rubric
    rubric = DOMAIN_RUBRICS.get(domain_type, DOMAIN_RUBRICS['content']).copy()

    # Apply custom weights if provided
    if custom_weights:
        rubric['weights'].update(custom_weights)
        # Renormalize weights
        total_weight = sum(rubric['weights'].values())
        rubric['weights'] = {k: v / total_weight for k, v in rubric['weights'].items()}

    # Calculate scores for each rubric component
    component_scores = {}
    for component in rubric['weights'].keys():
        if component == 'url_structure':
            component_scores[component] = _score_url_structure(data)['score']
        elif component == 'depth_appropriateness':
            component_scores[component] = _score_depth(data)['score']
        elif component == 'parameter_quality':
            component_scores[component] = _score_parameters(data)['score']
        elif component == 'internal_linking':
            component_scores[component] = _score_linking(data)['score']
        elif component == 'seo_quality':
            component_scores[component] = _score_seo(data)['score']
        else:
            # Default score for undefined components
            component_scores[component] = 75.0

    # Calculate weighted score
    weighted_score = sum(
        component_scores[comp] * rubric['weights'][comp]
        for comp in component_scores.keys()
    )

    # Check expectations
    metrics = _calculate_detailed_metrics(data)
    expectations = rubric['expectations']

    meets_expectations = {}
    for expectation, value in expectations.items():
        if expectation == 'avg_depth':
            min_d, max_d = value
            actual = metrics.get('avg_depth', 0)
            meets_expectations[expectation] = min_d <= actual <= max_d
        elif expectation == 'max_params':
            actual = metrics.get('avg_param_count', 0)
            meets_expectations[expectation] = actual <= value
        elif expectation == 'fragment_tolerance':
            actual = metrics.get('fragment_rate', 0)
            meets_expectations[expectation] = actual <= value

    return {
        'score': round(weighted_score, 2),
        'domain_type': domain_type,
        'rubric_applied': rubric,
        'component_scores': {k: round(v, 2) for k, v in component_scores.items()},
        'meets_expectations': meets_expectations,
        'expectation_compliance_rate': sum(meets_expectations.values()) / len(meets_expectations) if meets_expectations else 0,
        'available': True
    }


# Helper functions

def _detect_domain_type(data: List[Dict]) -> str:
    """Auto-detect domain type from URL patterns."""
    indicators = Counter()

    for item in data:
        url = item.get('url', '').lower()

        if any(pattern in url for pattern in ['/product/', '/cart/', '/shop/', '/checkout/']):
            indicators['ecommerce'] += 1
        if any(pattern in url for pattern in ['/blog/', '/article/', '/post/', '/news/']):
            indicators['content'] += 1
        if any(pattern in url for pattern in ['/docs/', '/documentation/', '/api/', '/guide/']):
            indicators['documentation'] += 1
        if any(pattern in url for pattern in ['/dashboard/', '/app/', '/workspace/']):
            indicators['saas'] += 1

    if indicators:
        return indicators.most_common(1)[0][0]
    return 'content'  # Default


def _classify_page_importance(url: str, depth: int) -> str:
    """Classify page importance."""
    import re

    for importance, indicators in PAGE_IMPORTANCE_INDICATORS.items():
        # Check patterns
        if any(re.search(pattern, url) for pattern in indicators['patterns']):
            # Check depth range
            min_d, max_d = indicators['depth_range']
            if min_d <= depth <= max_d:
                return importance

    return 'content'  # Default


def _calculate_level_score(urls: List[Dict], rubric: Dict) -> float:
    """Calculate score for a specific importance level."""
    # Simple implementation - can be enhanced
    scores = []

    for item in urls:
        url = item.get('url', '')
        parsed = urlparse(url)

        score = 100

        # Check URL length
        if len(url) > 100:
            score -= 10

        # Check parameters
        if parsed.query:
            param_count = len(parsed.query.split('&'))
            if param_count > 3:
                score -= param_count * 3

        # Check depth
        depth = item.get('depth', 0)
        if depth > 5:
            score -= (depth - 5) * 5

        scores.append(max(0, score))

    return np.mean(scores) if scores else 0


def _generate_contextual_insights(score_by_importance: Dict, url_counts: Counter, domain_type: str) -> List[str]:
    """Generate insights from contextual scoring."""
    insights = []

    # Check entry points
    entry_score = score_by_importance.get('entry_point')
    if entry_score and entry_score < 80:
        insights.append(f'CRITICAL: Entry point pages score only {entry_score:.1f}/100')

    # Check high-value pages
    high_value_score = score_by_importance.get('high_value')
    if high_value_score and high_value_score < 70:
        insights.append(f'WARNING: High-value pages score {high_value_score:.1f}/100')

    # Check if utility pages are pulling down average
    utility_score = score_by_importance.get('utility')
    if utility_score and utility_score < 50 and url_counts['utility'] > len(url_counts) * 0.2:
        insights.append('Utility pages (20%+ of site) are pulling down average score')

    return insights


def _get_default_benchmarks(domain_type: str) -> Dict:
    """Get default benchmark values for domain type."""
    benchmarks = {
        'ecommerce': {
            'overall': 72.0,
            'avg_depth': 3.2,
            'avg_param_count': 2.5,
            'fragment_rate': 0.08
        },
        'content': {
            'overall': 75.0,
            'avg_depth': 2.8,
            'avg_param_count': 1.2,
            'fragment_rate': 0.12
        },
        'saas': {
            'overall': 70.0,
            'avg_depth': 2.5,
            'avg_param_count': 3.5,
            'fragment_rate': 0.35
        },
        'documentation': {
            'overall': 78.0,
            'avg_depth': 4.0,
            'avg_param_count': 0.5,
            'fragment_rate': 0.15
        }
    }

    return benchmarks.get(domain_type, benchmarks['content'])


def _calculate_detailed_metrics(data: List[Dict]) -> Dict:
    """Calculate detailed metrics for comparison."""
    depths = [item.get('depth', 0) for item in data]
    urls = [item.get('url', '') for item in data if item.get('url')]

    param_counts = []
    fragment_count = 0

    for url in urls:
        parsed = urlparse(url)
        if parsed.query:
            param_counts.append(len(parsed.query.split('&')))
        if parsed.fragment:
            fragment_count += 1

    return {
        'avg_depth': np.mean(depths) if depths else 0,
        'avg_param_count': np.mean(param_counts) if param_counts else 0,
        'fragment_rate': fragment_count / len(urls) if urls else 0
    }


def _score_url_structure(data: List[Dict]) -> Dict:
    """Score URL structure quality."""
    score = 100
    issues = []

    urls = [item.get('url', '') for item in data if item.get('url')]

    # Check average URL length
    avg_length = np.mean([len(url) for url in urls]) if urls else 0
    if avg_length > 100:
        penalty = min(30, (avg_length - 100) / 10)
        score -= penalty
        issues.append({'description': 'URLs too long on average', 'fix': 'Shorten URL paths'})

    return {'score': max(0, score), 'issues': issues}


def _score_depth(data: List[Dict]) -> Dict:
    """Score depth appropriateness."""
    score = 100
    issues = []

    depths = [item.get('depth', 0) for item in data]
    avg_depth = np.mean(depths) if depths else 0

    # Optimal depth: 2-4
    if avg_depth > 4:
        penalty = (avg_depth - 4) * 10
        score -= penalty
        issues.append({'description': 'Site too deep on average', 'fix': 'Flatten hierarchy (easy)'})
    elif avg_depth < 2:
        penalty = (2 - avg_depth) * 5
        score -= penalty
        issues.append({'description': 'Site too shallow', 'fix': 'Consider adding categories'})

    return {'score': max(0, score), 'issues': issues}


def _score_parameters(data: List[Dict]) -> Dict:
    """Score parameter usage quality."""
    score = 100
    issues = []

    param_counts = []
    for item in data:
        url = item.get('url', '')
        if url:
            parsed = urlparse(url)
            if parsed.query:
                param_counts.append(len(parsed.query.split('&')))

    if param_counts:
        avg_params = np.mean(param_counts)
        if avg_params > 3:
            penalty = (avg_params - 3) * 8
            score -= penalty
            issues.append({'description': 'Excessive query parameters', 'fix': 'URL normalization (easy)'})

    return {'score': max(0, score), 'issues': issues}


def _score_linking(data: List[Dict]) -> Dict:
    """Score internal linking quality."""
    score = 100
    issues = []

    link_counts = [len(item.get('links', [])) for item in data]
    avg_links = np.mean(link_counts) if link_counts else 0

    # Check for dead ends
    dead_ends = sum(1 for lc in link_counts if lc == 0)
    dead_end_rate = dead_ends / len(link_counts) if link_counts else 0

    if dead_end_rate > 0.2:
        penalty = dead_end_rate * 50
        score -= penalty
        issues.append({'description': f'{dead_end_rate*100:.1f}% pages are dead ends', 'fix': 'Add internal links'})

    return {'score': max(0, score), 'issues': issues}


def _score_seo(data: List[Dict]) -> Dict:
    """Score SEO quality."""
    score = 100
    issues = []

    urls = [item.get('url', '') for item in data if item.get('url')]

    # Check for SEO-friendly characteristics
    uppercase_count = sum(1 for url in urls if any(c.isupper() for c in urlparse(url).path))
    if uppercase_count / len(urls) > 0.1 if urls else False:
        score -= 15
        issues.append({'description': 'URLs contain uppercase letters', 'fix': 'Use lowercase URLs (easy)'})

    return {'score': max(0, score), 'issues': issues}
