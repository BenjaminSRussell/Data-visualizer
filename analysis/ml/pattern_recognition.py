"""
Pattern Recognition - Identify URL patterns using MLX

Detects:
- Date patterns (YYYY/MM/DD)
- ID patterns (numeric sequences)
- Category patterns (repeated path structures)
- File type patterns
"""

import mlx.core as mx
import re
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
from urllib.parse import urlparse


class PatternRecognizer:
    """Recognize patterns in URLs using rule-based and ML approaches"""

    def __init__(self):
        self.patterns = {
            'date_year': re.compile(r'/(\d{4})(?:/|$)'),
            'date_month': re.compile(r'/(\d{2})(?:/|$)'),
            'numeric_id': re.compile(r'/(\d+)(?:/|\.|\?|$)'),
            'uuid': re.compile(r'/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'),
            'file_extension': re.compile(r'\.([a-z0-9]+)$', re.IGNORECASE),
            'prefix_pattern': re.compile(r'/([a-z]{2,3})-'),  # like ss-, ns-, etc.
        }

    def analyze_patterns(self, url_data: List[Dict]) -> Dict:
        """
        Analyze all patterns in URL dataset.

        Args:
            url_data: List of URL dictionaries

        Returns:
            Dictionary of pattern analysis results
        """
        print(f"\nAnalyzing patterns in {len(url_data):,} URLs...")

        results = {
            'temporal_patterns': self._find_temporal_patterns(url_data),
            'id_patterns': self._find_id_patterns(url_data),
            'structure_patterns': self._find_structure_patterns(url_data),
            'naming_conventions': self._find_naming_conventions(url_data),
            'file_patterns': self._find_file_patterns(url_data)
        }

        print(f"✓ Pattern analysis complete")

        return results

    def _find_temporal_patterns(self, url_data: List[Dict]) -> Dict:
        """Find date/time patterns in URLs"""
        years = []
        months = []
        year_month_combos = []

        for item in url_data:
            path = urlparse(item['url']).path

            # find years
            year_matches = self.patterns['date_year'].findall(path)
            for year_str in year_matches:
                year = int(year_str)
                if 2000 <= year <= 2030:  # valid range
                    years.append(year)

            # find months
            month_matches = self.patterns['date_month'].findall(path)
            for month_str in month_matches:
                month = int(month_str)
                if 1 <= month <= 12:
                    months.append(month)

            # find year/month combinations
            if year_matches and month_matches:
                year_month_combos.append(f"{year_matches[0]}-{month_matches[0]}")

        return {
            'has_temporal_patterns': len(years) > 0,
            'years_found': len(years),
            'unique_years': len(set(years)),
            'year_distribution': dict(Counter(years)),
            'month_distribution': dict(Counter(months)),
            'year_month_patterns': len(year_month_combos),
            'most_common_months': dict(Counter(months).most_common(5)) if months else {}
        }

    def _find_id_patterns(self, url_data: List[Dict]) -> Dict:
        """Find numeric ID patterns"""
        numeric_ids = []
        uuid_count = 0

        for item in url_data:
            path = urlparse(item['url']).path

            # find numeric ids
            id_matches = self.patterns['numeric_id'].findall(path)
            numeric_ids.extend([int(id_str) for id_str in id_matches if len(id_str) < 10])

            # find uuids
            if self.patterns['uuid'].search(path):
                uuid_count += 1

        return {
            'urls_with_numeric_ids': len([i for i in url_data if self.patterns['numeric_id'].search(urlparse(i['url']).path)]),
            'total_numeric_ids': len(numeric_ids),
            'unique_numeric_ids': len(set(numeric_ids)),
            'urls_with_uuids': uuid_count,
            'id_range': (min(numeric_ids), max(numeric_ids)) if numeric_ids else (None, None)
        }

    def _find_structure_patterns(self, url_data: List[Dict]) -> Dict:
        """Find structural patterns in URL paths"""
        path_structures = Counter()
        depth_structures = defaultdict(Counter)

        for item in url_data:
            path = urlparse(item['url']).path
            segments = [s for s in path.split('/') if s]

            # create structure pattern (replace specific values with placeholders)
            structure = []
            for seg in segments:
                if seg.isdigit():
                    structure.append('<NUM>')
                elif self.patterns['date_year'].match(seg):
                    structure.append('<YEAR>')
                elif self.patterns['uuid'].match(seg):
                    structure.append('<UUID>')
                elif '.' in seg:
                    structure.append('<FILE>')
                else:
                    structure.append(seg)

            structure_str = '/' + '/'.join(structure)
            path_structures[structure_str] += 1

            # track depth-specific structures
            depth = len(segments)
            depth_structures[depth][structure_str] += 1

        return {
            'unique_structures': len(path_structures),
            'most_common_structures': dict(path_structures.most_common(20)),
            'depth_structure_variety': {
                depth: len(structures)
                for depth, structures in depth_structures.items()
            }
        }

    def _find_naming_conventions(self, url_data: List[Dict]) -> Dict:
        """Find naming convention patterns"""
        prefixes = Counter()
        separators = Counter(['-', '_', '.'])

        for item in url_data:
            path = urlparse(item['url']).path

            # find prefixes like ss-, ns-, etc.
            prefix_matches = self.patterns['prefix_pattern'].findall(path)
            prefixes.update(prefix_matches)

            # count separator usage
            separators['-'] += path.count('-')
            separators['_'] += path.count('_')
            separators['.'] += path.count('.')

        return {
            'common_prefixes': dict(prefixes.most_common(10)),
            'separator_usage': dict(separators),
            'kebab_case_urls': sum(1 for item in url_data if '-' in urlparse(item['url']).path),
            'snake_case_urls': sum(1 for item in url_data if '_' in urlparse(item['url']).path)
        }

    def _find_file_patterns(self, url_data: List[Dict]) -> Dict:
        """Find file type patterns"""
        extensions = Counter()

        for item in url_data:
            path = urlparse(item['url']).path

            ext_match = self.patterns['file_extension'].search(path)
            if ext_match:
                ext = ext_match.group(1).lower()
                extensions[ext] += 1

        return {
            'urls_with_extensions': sum(extensions.values()),
            'unique_extensions': len(extensions),
            'extension_distribution': dict(extensions.most_common(20))
        }

    def find_url_template(self, urls: List[str]) -> str:
        """
        Find common template/pattern across multiple URLs.

        Args:
            urls: List of similar URLs

        Returns:
            Template string with placeholders
        """
        if not urls:
            return ""

        # parse all urls
        parsed_urls = [urlparse(url) for url in urls]

        # get common domain
        domains = set(p.netloc for p in parsed_urls)
        if len(domains) == 1:
            common_domain = list(domains)[0]
        else:
            common_domain = "<DOMAIN>"

        # find common path structure
        paths = [[s for s in p.path.split('/') if s] for p in parsed_urls]

        if not paths:
            return f"{common_domain}/"

        # find longest common prefix
        common_path = []
        max_depth = min(len(p) for p in paths)

        for i in range(max_depth):
            segments_at_i = [p[i] for p in paths]

            if len(set(segments_at_i)) == 1:
                # all same
                common_path.append(segments_at_i[0])
            else:
                # different - use placeholder
                if all(s.isdigit() for s in segments_at_i):
                    common_path.append('<NUM>')
                else:
                    common_path.append('<VAR>')

        template = f"{common_domain}/" + '/'.join(common_path)

        return template
