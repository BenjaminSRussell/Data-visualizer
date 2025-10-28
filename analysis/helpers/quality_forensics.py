"""
Data Quality Forensics

Purpose: Deep-dive into why quality scores are low, not just that they're low.
data_quality_analyzer.py (lines 1-400) identifies duplication and inflation but
lacks root cause analysis.

Integration Points:
- Extends data_quality_analyzer.py with root cause analysis
- Line 85's fragment analysis shows 59.3% usage but doesn't distinguish between
  "SPA navigation fragments" (acceptable) vs "anchor link pollution" (problematic)
"""

from typing import Dict, List, Tuple, Set
from collections import Counter, defaultdict
from urllib.parse import urlparse, parse_qs
import re


def trace_duplication_source(data: List[Dict]) -> Dict:
    """
    Trace duplication to source patterns (CMS behavior, tracking implementations).

    Instead of just counting duplicates, this identifies WHY duplication occurs.

    Args:
        data: List of URL dictionaries

    Returns:
        Dictionary with duplication source analysis

    Example:
        {
            'duplication_sources': {
                'cms_pagination': {
                    'count': 150,
                    'pattern': '/page/{num}/',
                    'explanation': 'CMS generates paginated views'
                },
                'tracking_parameters': {
                    'count': 200,
                    'pattern': '?utm_*',
                    'explanation': 'Marketing tracking parameters'
                }
            }
        }
    """
    if not data:
        return {
            'duplication_sources': {},
            'available': False
        }

    duplication_sources = {}

    # 1. CMS Pagination patterns
    pagination_patterns = _detect_cms_pagination(data)
    if pagination_patterns['count'] > 0:
        duplication_sources['cms_pagination'] = pagination_patterns

    # 2. Session ID duplication
    session_patterns = _detect_session_id_duplication(data)
    if session_patterns['count'] > 0:
        duplication_sources['session_ids'] = session_patterns

    # 3. Tracking parameter duplication
    tracking_patterns = _detect_tracking_duplication(data)
    if tracking_patterns['count'] > 0:
        duplication_sources['tracking_parameters'] = tracking_patterns

    # 4. Fragment-based duplication (SPA vs anchor)
    fragment_patterns = _classify_fragment_duplication(data)
    if fragment_patterns['total_count'] > 0:
        duplication_sources['fragments'] = fragment_patterns

    # 5. Timestamp/cache-busting duplication
    cache_busting_patterns = _detect_cache_busting(data)
    if cache_busting_patterns['count'] > 0:
        duplication_sources['cache_busting'] = cache_busting_patterns

    # 6. Localization duplication
    localization_patterns = _detect_localization_duplication(data)
    if localization_patterns['count'] > 0:
        duplication_sources['localization'] = localization_patterns

    # Calculate total impact
    total_duplicates = sum(
        source.get('count', 0)
        for source in duplication_sources.values()
        if isinstance(source, dict)
    )

    # Categorize sources by fix difficulty
    fix_difficulty = {
        'easy': [],  # Can be fixed with URL normalization
        'medium': [],  # Requires configuration changes
        'hard': []  # Requires CMS/architecture changes
    }

    difficulty_map = {
        'tracking_parameters': 'easy',
        'cache_busting': 'easy',
        'session_ids': 'medium',
        'fragments': 'medium',
        'cms_pagination': 'hard',
        'localization': 'hard'
    }

    for source_name, difficulty in difficulty_map.items():
        if source_name in duplication_sources:
            fix_difficulty[difficulty].append({
                'source': source_name,
                'count': duplication_sources[source_name].get('count', 0)
            })

    return {
        'duplication_sources': duplication_sources,
        'total_duplicates': total_duplicates,
        'total_urls': len(data),
        'duplication_rate': (total_duplicates / len(data) * 100) if data else 0,
        'fix_difficulty': fix_difficulty,
        'available': True
    }


def identify_quality_degradation_points(data: List[Dict]) -> Dict:
    """
    Identify quality degradation points in the crawl.

    Finds where in the site structure quality issues begin to appear.

    Args:
        data: List of URL dictionaries with depth and quality metrics

    Returns:
        Dictionary with degradation point analysis

    Example:
        {
            'degradation_points': [
                {
                    'location': '/api/',
                    'depth': 3,
                    'quality_drop': 35,  # percentage drop
                    'primary_issue': 'parameter_pollution'
                }
            ]
        }
    """
    if not data:
        return {
            'degradation_points': [],
            'available': False
        }

    # Group by path prefix and depth
    quality_by_location = defaultdict(lambda: {
        'urls': [],
        'issues': Counter()
    })

    for item in data:
        url = item.get('url', '')
        if not url:
            continue

        # Extract location (first path segment)
        parsed = urlparse(url)
        segments = [s for s in parsed.path.split('/') if s]
        location = '/' + segments[0] + '/' if segments else '/'

        depth = item.get('depth', 0)
        location_key = f"{location}@depth{depth}"

        quality_by_location[location_key]['urls'].append(url)

        # Assess issues
        issues = _assess_url_quality_issues(url, parsed)
        quality_by_location[location_key]['issues'].update(issues)

    # Calculate quality scores
    location_scores = {}

    for location_key, data_point in quality_by_location.items():
        url_count = len(data_point['urls'])
        issues = data_point['issues']

        # Calculate quality score (0-100)
        total_issue_count = sum(issues.values())
        quality_score = max(0, 100 - (total_issue_count / url_count) * 20)

        location_scores[location_key] = {
            'location': location_key,
            'url_count': url_count,
            'quality_score': quality_score,
            'issues': dict(issues),
            'primary_issue': issues.most_common(1)[0][0] if issues else None
        }

    # Find degradation points (locations with low quality)
    degradation_threshold = 60
    degradation_points = [
        loc_data for loc_data in location_scores.values()
        if loc_data['quality_score'] < degradation_threshold
    ]

    # Sort by quality score (worst first)
    degradation_points.sort(key=lambda x: x['quality_score'])

    # Calculate overall quality trend by depth
    quality_by_depth = defaultdict(list)
    for location_key, loc_data in location_scores.items():
        depth = int(location_key.split('@depth')[1])
        quality_by_depth[depth].append(loc_data['quality_score'])

    avg_quality_by_depth = {
        depth: round(sum(scores) / len(scores), 2)
        for depth, scores in quality_by_depth.items()
    }

    return {
        'degradation_points': degradation_points[:10],  # Top 10 worst
        'total_degradation_points': len(degradation_points),
        'avg_quality_by_depth': avg_quality_by_depth,
        'quality_trend': _analyze_quality_trend(avg_quality_by_depth),
        'available': True
    }


def map_parameter_pollution(data: List[Dict]) -> Dict:
    """
    Map parameter pollution to specific page templates.

    Identifies which page templates or sections have excessive parameter usage.

    Args:
        data: List of URL dictionaries

    Returns:
        Dictionary with parameter pollution mapping

    Example:
        {
            'polluted_templates': [
                {
                    'template': '/search',
                    'avg_param_count': 8.5,
                    'pollution_score': 85,
                    'common_params': ['sort', 'filter', 'page', ...]
                }
            ]
        }
    """
    if not data:
        return {
            'polluted_templates': [],
            'available': False
        }

    # Group by template (path without IDs)
    template_params = defaultdict(lambda: {
        'param_counts': [],
        'all_params': Counter(),
        'urls': []
    })

    for item in data:
        url = item.get('url', '')
        if not url:
            continue

        parsed = urlparse(url)

        # Extract template (path with IDs replaced)
        template = re.sub(r'/\d+', '/{id}', parsed.path)

        # Count parameters
        if parsed.query:
            params = parse_qs(parsed.query)
            param_count = len(params)

            template_params[template]['param_counts'].append(param_count)
            template_params[template]['all_params'].update(params.keys())
            template_params[template]['urls'].append(url)

    # Analyze each template
    polluted_templates = []

    for template, data_point in template_params.items():
        param_counts = data_point['param_counts']
        if not param_counts:
            continue

        avg_param_count = sum(param_counts) / len(param_counts)
        max_param_count = max(param_counts)

        # Calculate pollution score
        # Score based on: avg params, max params, and param diversity
        param_diversity = len(data_point['all_params'])
        pollution_score = min(100, (avg_param_count * 10) + (param_diversity * 2))

        # Classify pollution level
        if pollution_score > 70:
            pollution_level = 'high'
        elif pollution_score > 40:
            pollution_level = 'medium'
        else:
            pollution_level = 'low'

        # Identify tracking vs functional params
        tracking_params = [
            p for p in data_point['all_params'].keys()
            if p.startswith(('utm_', 'fbclid', 'gclid', '_ga', '_gl'))
        ]

        polluted_templates.append({
            'template': template,
            'url_count': len(data_point['urls']),
            'avg_param_count': round(avg_param_count, 2),
            'max_param_count': max_param_count,
            'param_diversity': param_diversity,
            'pollution_score': round(pollution_score, 2),
            'pollution_level': pollution_level,
            'common_params': [p for p, _ in data_point['all_params'].most_common(10)],
            'tracking_params': tracking_params,
            'tracking_param_ratio': len(tracking_params) / param_diversity if param_diversity > 0 else 0
        })

    # Sort by pollution score
    polluted_templates.sort(key=lambda x: x['pollution_score'], reverse=True)

    return {
        'polluted_templates': polluted_templates,
        'total_templates_analyzed': len(template_params),
        'highly_polluted_count': sum(1 for t in polluted_templates if t['pollution_level'] == 'high'),
        'recommendations': _generate_pollution_recommendations(polluted_templates),
        'available': True
    }


def detect_systematic_issues(data: List[Dict]) -> Dict:
    """
    Detect systematic vs random quality issues.

    Determines whether quality problems are widespread (systematic) or
    isolated (random), which affects remediation strategy.

    Args:
        data: List of URL dictionaries

    Returns:
        Dictionary with systematic issue detection

    Example:
        {
            'issue_type': 'systematic',
            'confidence': 0.85,
            'patterns': {
                'affects_all_depths': True,
                'affects_all_sections': False,
                'concentrated_in': ['/api/', '/legacy/']
            }
        }
    """
    if not data:
        return {
            'issue_type': None,
            'available': False
        }

    # Collect issues across multiple dimensions
    issues_by_depth = defaultdict(Counter)
    issues_by_section = defaultdict(Counter)
    issues_by_domain = defaultdict(Counter)

    for item in data:
        url = item.get('url', '')
        if not url:
            continue

        parsed = urlparse(url)
        depth = item.get('depth', 0)

        # Extract section
        segments = [s for s in parsed.path.split('/') if s]
        section = '/' + segments[0] + '/' if segments else '/'

        # Assess issues
        issues = _assess_url_quality_issues(url, parsed)

        # Record issues by dimension
        for issue in issues:
            issues_by_depth[depth][issue] += 1
            issues_by_section[section][issue] += 1
            issues_by_domain[parsed.netloc][issue] += 1

    # Analyze distribution
    # Systematic: issues appear consistently across all dimensions
    # Random: issues are concentrated in specific areas

    # Calculate spread metrics
    depth_spread = len(issues_by_depth) / max(1, max(issues_by_depth.keys(), default=1))
    section_spread = len(issues_by_section)

    # Count how many dimensions have issues
    dimensions_with_issues = 0
    if len(issues_by_depth) > 1:
        dimensions_with_issues += 1
    if len(issues_by_section) > 1:
        dimensions_with_issues += 1
    if len(issues_by_domain) > 1:
        dimensions_with_issues += 1

    # Determine if systematic
    is_systematic = dimensions_with_issues >= 2 and depth_spread > 0.5

    # Find concentrated areas (for random issues)
    concentrated_sections = []
    if not is_systematic:
        total_issues = sum(sum(counter.values()) for counter in issues_by_section.values())
        for section, issue_counter in issues_by_section.items():
            section_total = sum(issue_counter.values())
            if section_total > total_issues * 0.3:  # Section has >30% of issues
                concentrated_sections.append({
                    'section': section,
                    'issue_count': section_total,
                    'percentage': (section_total / total_issues * 100) if total_issues > 0 else 0
                })

    return {
        'issue_type': 'systematic' if is_systematic else 'random',
        'confidence': 0.8 if is_systematic else 0.7,
        'patterns': {
            'affects_all_depths': len(issues_by_depth) > 3,
            'affects_multiple_sections': len(issues_by_section) > 2,
            'depth_spread': round(depth_spread, 2),
            'section_count': len(issues_by_section),
            'concentrated_in': concentrated_sections
        },
        'remediation_strategy': 'global' if is_systematic else 'targeted',
        'recommendations': _generate_systematic_recommendations(is_systematic, concentrated_sections),
        'available': True
    }


# Helper functions

def _detect_cms_pagination(data: List[Dict]) -> Dict:
    """Detect CMS pagination patterns."""
    pagination_patterns = [
        r'/page/\d+',
        r'\?page=\d+',
        r'/p\d+',
        r'\?p=\d+'
    ]

    count = 0
    examples = []

    for item in data:
        url = item.get('url', '')
        if any(re.search(pattern, url) for pattern in pagination_patterns):
            count += 1
            if len(examples) < 5:
                examples.append(url)

    return {
        'count': count,
        'pattern': 'Pagination patterns (/page/{num}, ?page={num})',
        'explanation': 'CMS generates paginated views of content lists',
        'examples': examples,
        'recommended_fix': 'Canonical tags or URL normalization'
    }


def _detect_session_id_duplication(data: List[Dict]) -> Dict:
    """Detect session ID parameters."""
    session_patterns = ['sessionid', 'session', 'phpsessid', 'jsessionid', 'sid']

    count = 0
    examples = []

    for item in data:
        url = item.get('url', '')
        url_lower = url.lower()

        if any(pattern in url_lower for pattern in session_patterns):
            count += 1
            if len(examples) < 5:
                examples.append(url)

    return {
        'count': count,
        'pattern': 'Session ID parameters',
        'explanation': 'URLs contain session identifiers causing duplicate content',
        'examples': examples,
        'recommended_fix': 'Remove session IDs from URLs or use canonical tags'
    }


def _detect_tracking_duplication(data: List[Dict]) -> Dict:
    """Detect tracking parameter duplication."""
    tracking_params = ['utm_', 'fbclid', 'gclid', 'msclkid', '_ga', '_gl']

    count = 0
    param_distribution = Counter()

    for item in data:
        url = item.get('url', '')
        parsed = urlparse(url)

        if parsed.query:
            for param in tracking_params:
                if param in parsed.query.lower():
                    count += 1
                    param_distribution[param] += 1
                    break

    return {
        'count': count,
        'pattern': 'Marketing tracking parameters (utm_*, fbclid, gclid, etc.)',
        'explanation': 'Marketing campaigns add tracking parameters',
        'param_distribution': dict(param_distribution.most_common()),
        'recommended_fix': 'URL normalization to remove tracking parameters'
    }


def _classify_fragment_duplication(data: List[Dict]) -> Dict:
    """Classify fragment usage (SPA vs anchor)."""
    spa_fragments = 0
    anchor_fragments = 0
    other_fragments = 0

    for item in data:
        url = item.get('url', '')
        parsed = urlparse(url)

        if parsed.fragment:
            # SPA patterns: #!/, #/, contains slashes
            if parsed.fragment.startswith('/') or parsed.fragment.startswith('!/'):
                spa_fragments += 1
            # Anchor patterns: simple IDs
            elif re.match(r'^[a-zA-Z][\w-]*$', parsed.fragment):
                anchor_fragments += 1
            else:
                other_fragments += 1

    total = spa_fragments + anchor_fragments + other_fragments

    return {
        'total_count': total,
        'spa_navigation': {
            'count': spa_fragments,
            'percentage': (spa_fragments / total * 100) if total > 0 else 0,
            'acceptable': True
        },
        'anchor_links': {
            'count': anchor_fragments,
            'percentage': (anchor_fragments / total * 100) if total > 0 else 0,
            'acceptable': anchor_fragments < total * 0.3  # <30% is acceptable
        },
        'other': {
            'count': other_fragments,
            'percentage': (other_fragments / total * 100) if total > 0 else 0
        },
        'explanation': 'SPA navigation fragments are acceptable; excessive anchor fragments may cause duplication'
    }


def _detect_cache_busting(data: List[Dict]) -> Dict:
    """Detect cache-busting parameters."""
    cache_patterns = [r'\?v=\d+', r'\?_=\d+', r'\?timestamp=\d+', r'\?cache=']

    count = 0
    for item in data:
        url = item.get('url', '')
        if any(re.search(pattern, url) for pattern in cache_patterns):
            count += 1

    return {
        'count': count,
        'pattern': 'Cache-busting parameters (?v=, ?timestamp=, etc.)',
        'explanation': 'Version or timestamp parameters added to bypass caching',
        'recommended_fix': 'Remove from canonical URLs'
    }


def _detect_localization_duplication(data: List[Dict]) -> Dict:
    """Detect localization-based duplication."""
    lang_patterns = [r'/en/', r'/en-us/', r'/fr/', r'/de/', r'\?lang=', r'\?locale=']

    count = 0
    for item in data:
        url = item.get('url', '')
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in lang_patterns):
            count += 1

    return {
        'count': count,
        'pattern': 'Language/locale parameters',
        'explanation': 'Multiple language versions of same content',
        'recommended_fix': 'Use hreflang tags and canonical URLs'
    }


def _assess_url_quality_issues(url: str, parsed) -> List[str]:
    """Assess quality issues for a single URL."""
    issues = []

    # Check URL length
    if len(url) > 100:
        issues.append('excessive_length')

    # Check parameter count
    if parsed.query:
        param_count = len(parse_qs(parsed.query))
        if param_count > 5:
            issues.append('parameter_pollution')

    # Check for session IDs
    if any(p in url.lower() for p in ['sessionid', 'jsessionid', 'phpsessid']):
        issues.append('session_id')

    # Check for fragments
    if parsed.fragment:
        issues.append('fragment_present')

    # Check depth
    depth = len([s for s in parsed.path.split('/') if s])
    if depth > 5:
        issues.append('excessive_depth')

    return issues


def _analyze_quality_trend(quality_by_depth: Dict[int, float]) -> str:
    """Analyze quality trend across depths."""
    if len(quality_by_depth) < 2:
        return 'insufficient_data'

    depths = sorted(quality_by_depth.keys())
    qualities = [quality_by_depth[d] for d in depths]

    # Check if quality is declining
    if qualities[-1] < qualities[0] - 20:
        return 'declining'
    elif qualities[-1] > qualities[0] + 20:
        return 'improving'
    else:
        return 'stable'


def _generate_pollution_recommendations(polluted_templates: List[Dict]) -> List[str]:
    """Generate recommendations for parameter pollution."""
    recommendations = []

    if not polluted_templates:
        return ['No significant parameter pollution detected.']

    high_pollution = [t for t in polluted_templates if t['pollution_level'] == 'high']

    if high_pollution:
        recommendations.append(f'{len(high_pollution)} templates have high parameter pollution.')
        recommendations.append('Review parameter usage and implement URL normalization.')

    # Check for tracking params
    high_tracking = [t for t in polluted_templates if t.get('tracking_param_ratio', 0) > 0.5]
    if high_tracking:
        recommendations.append('Remove tracking parameters from canonical URLs.')

    return recommendations


def _generate_systematic_recommendations(is_systematic: bool, concentrated_sections: List[Dict]) -> List[str]:
    """Generate recommendations based on issue type."""
    if is_systematic:
        return [
            'Issues are systematic across the site.',
            'Implement global fixes: URL normalization rules, canonical tags.',
            'Review CMS configuration and URL generation logic.'
        ]
    else:
        recs = ['Issues are concentrated in specific areas.']
        for section in concentrated_sections:
            recs.append(f"Focus on {section['section']} ({section['percentage']:.1f}% of issues)")
        return recs
