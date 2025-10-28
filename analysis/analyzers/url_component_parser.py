"""
URL Component Parser - Deep Decomposition

Purpose: Extract EVERY component from URLs - scheme, auth, host, port, path,
         parameters, fragments, encoded values, file extensions, etc.

         This is the CANONICAL source for detailed component extraction.
"""

import re
from collections import Counter, defaultdict
from typing import Dict, List
from urllib.parse import parse_qs, unquote

# Use shared utilities for basic parsing (this module extends them)
from analysis.utils.url_utilities import (
    classify_fragment,
    extract_file_extension,
    get_path_depth,
    parse_url_components,
)


class URLComponentParser:
    """Parse and analyze every component of URLs."""

    def __init__(self):
        self.components = defaultdict(lambda: {
            'schemes': Counter(),
            'auth_users': Counter(),
            'hosts': Counter(),
            'ports': Counter(),
            'paths': [],
            'path_segments': Counter(),
            'path_depths': Counter(),
            'file_extensions': Counter(),
            'query_params': defaultdict(Counter),
            'fragments': Counter(),
            'encoded_components': [],
            'special_chars': Counter()
        })

        self.url_patterns = []

    def analyze(self, data: List[Dict]) -> Dict:
        """
        Perform comprehensive URL component analysis.

        Args:
            data: List of URL dictionaries from JSONL

        Returns:
            URL component analysis results
        """
        for item in data:
            url = item.get('url', '')
            if url:
                self._parse_url_components(url, item)

        results = {
            'scheme_analysis': self._analyze_schemes(),
            'authentication': self._analyze_auth(),
            'host_analysis': self._analyze_hosts(),
            'port_analysis': self._analyze_ports(),
            'path_analysis': self._analyze_paths(),
            'extension_analysis': self._analyze_extensions(),
            'parameter_analysis': self._analyze_parameters(),
            'fragment_analysis': self._analyze_fragments(),
            'encoding_analysis': self._analyze_encoding(),
            'special_character_analysis': self._analyze_special_chars(),
            'url_structure_patterns': self._identify_structure_patterns(),
            'data_extraction': self._extract_embedded_data()
        }

        return results

    def _parse_url_components(self, url: str, metadata: Dict):
        """Parse all components from a single URL."""

        try:
            # Use shared utility for basic parsing
            components = parse_url_components(url)

            # scheme
            self.components['all']['schemes'][components['scheme']] += 1

            # authentication
            if components['username']:
                self.components['all']['auth_users'][components['username']] += 1

            # host
            if components['hostname']:
                self.components['all']['hosts'][components['hostname'].lower()] += 1

            # port
            if components['port']:
                self.components['all']['ports'][components['port']] += 1

            # path analysis
            if components['path']:
                self._analyze_path_component(components['path'])

            # query parameters
            if components['query']:
                self._analyze_query_component(components['query'])

            # fragment
            if components['fragment']:
                self._analyze_fragment_component(components['fragment'])

            # detect encoding
            self._detect_encoding(url)

            # special characters
            self._count_special_chars(url)

            # store pattern
            self.url_patterns.append({
                'url': url,
                'has_auth': components['has_auth'],
                'has_port': components['has_port'],
                'has_query': components['has_query'],
                'has_fragment': components['has_fragment'],
                'path_segments': components['path_depth'],
                'scheme': components['scheme']
            })

        except Exception as e:
            pass

    def _analyze_path_component(self, path: str):
        """Analyze path components in detail."""

        # store full path
        self.components['all']['paths'].append(path)

        # Use shared utility for depth calculation
        depth = get_path_depth(path)
        self.components['all']['path_depths'][depth] += 1

        # path segments
        segments = [s for s in path.split('/') if s]
        for segment in segments:
            self.components['all']['path_segments'][segment] += 1

        # file extension using shared utility
        ext = extract_file_extension(path)
        if ext:
            self.components['all']['file_extensions'][ext] += 1

    def _analyze_query_component(self, query: str):
        """Analyze query string parameters."""

        try:
            params = parse_qs(query, keep_blank_values=True)

            for key, values in params.items():
                for value in values:
                    # store parameter value
                    self.components['all']['query_params'][key][value] += 1

        except Exception:
            pass

    def _analyze_fragment_component(self, fragment: str):
        """Analyze URL fragments."""

        # Use shared utility for fragment decoding
        decoded = unquote(fragment)
        self.components['all']['fragments'][decoded] += 1

    def _detect_encoding(self, url: str):
        """Detect various encoding schemes in URL."""

        encodings = []

        # url encoding (%xx)
        if '%' in url:
            percent_encoded = re.findall(r'%[0-9A-Fa-f]{2}', url)
            if percent_encoded:
                encodings.append({
                    'type': 'percent',
                    'count': len(percent_encoded),
                    'examples': percent_encoded[:5]
                })

        # base64 patterns (common in some urls)
        base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
        base64_matches = re.findall(base64_pattern, url)
        if base64_matches:
            encodings.append({
                'type': 'base64_candidate',
                'count': len(base64_matches),
                'examples': base64_matches[:3]
            })

        # punycode (internationalized domains)
        if 'xn--' in url.lower():
            encodings.append({
                'type': 'punycode',
                'detected': True
            })

        if encodings:
            self.components['all']['encoded_components'].extend(encodings)

    def _count_special_chars(self, url: str):
        """Count special characters in URL."""

        special_chars = set('!@#$%^&*()[]{}|\\:;"\'<>?~`')

        for char in url:
            if char in special_chars:
                self.components['all']['special_chars'][char] += 1

    def _analyze_schemes(self) -> Dict:
        """Analyze URL schemes."""

        schemes = self.components['all']['schemes']

        return {
            'total_schemes': len(schemes),
            'scheme_distribution': dict(schemes),
            'most_common': schemes.most_common(1)[0] if schemes else None,
            'insecure_count': schemes.get('http', 0),
            'secure_count': schemes.get('https', 0),
            'security_ratio': schemes.get('https', 0) / max(sum(schemes.values()), 1)
        }

    def _analyze_auth(self) -> Dict:
        """Analyze authentication in URLs."""

        auth_users = self.components['all']['auth_users']

        return {
            'urls_with_auth': sum(auth_users.values()),
            'unique_usernames': len(auth_users),
            'usernames': dict(auth_users.most_common(20)),
            'security_concern': sum(auth_users.values()) > 0  # auth in url is generally bad practice
        }

    def _analyze_hosts(self) -> Dict:
        """Analyze host components."""

        hosts = self.components['all']['hosts']

        # classify hosts
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        localhost_pattern = r'^(localhost|127\.0\.0\.1|::1)$'

        ip_addresses = []
        localhost_urls = []
        domain_names = []

        for host in hosts:
            if re.match(ip_pattern, host):
                ip_addresses.append(host)
            elif re.match(localhost_pattern, host):
                localhost_urls.append(host)
            else:
                domain_names.append(host)

        return {
            'total_unique_hosts': len(hosts),
            'host_distribution': dict(hosts.most_common(20)),
            'ip_addresses': ip_addresses,
            'localhost_count': len(localhost_urls),
            'domain_count': len(domain_names),
            'most_common_host': hosts.most_common(1)[0] if hosts else None
        }

    def _analyze_ports(self) -> Dict:
        """Analyze port usage."""

        ports = self.components['all']['ports']

        # common ports
        well_known = {
            80: 'HTTP',
            443: 'HTTPS',
            8080: 'HTTP Alternate',
            8443: 'HTTPS Alternate',
            3000: 'Development Server',
            5000: 'Development Server',
            8000: 'Development Server'
        }

        port_purposes = {}
        for port, count in ports.items():
            port_purposes[port] = {
                'count': count,
                'purpose': well_known.get(port, 'Custom/Unknown')
            }

        return {
            'urls_with_explicit_port': sum(ports.values()),
            'unique_ports': len(ports),
            'port_distribution': dict(ports),
            'port_purposes': port_purposes,
            'non_standard_ports': [p for p in ports if p not in [80, 443]]
        }

    def _analyze_paths(self) -> Dict:
        """Analyze path structures."""

        paths = self.components['all']['paths']
        segments = self.components['all']['path_segments']
        depths = self.components['all']['path_depths']

        # path characteristics
        total_paths = len(paths)
        empty_paths = sum(1 for p in paths if not p or p == '/')

        # trailing slashes
        trailing_slash = sum(1 for p in paths if p.endswith('/'))

        # leading slashes
        leading_slash = sum(1 for p in paths if p.startswith('/'))

        # average path length
        avg_length = sum(len(p) for p in paths) / total_paths if total_paths > 0 else 0

        return {
            'total_paths': total_paths,
            'empty_paths': empty_paths,
            'avg_path_length': avg_length,
            'trailing_slash_count': trailing_slash,
            'trailing_slash_percent': (trailing_slash / total_paths * 100) if total_paths > 0 else 0,
            'depth_distribution': dict(depths),
            'avg_depth': sum(d * c for d, c in depths.items()) / sum(depths.values()) if depths else 0,
            'max_depth': max(depths.keys()) if depths else 0,
            'top_path_segments': dict(segments.most_common(30)),
            'unique_segments': len(segments)
        }

    def _analyze_extensions(self) -> Dict:
        """Analyze file extensions."""

        extensions = self.components['all']['file_extensions']

        # categorize extensions
        categories = {
            'web': ['html', 'htm', 'php', 'asp', 'aspx', 'jsp', 'xhtml'],
            'style': ['css', 'scss', 'sass', 'less'],
            'script': ['js', 'ts', 'jsx', 'tsx', 'mjs'],
            'document': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'],
            'image': ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'ico'],
            'video': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'],
            'audio': ['mp3', 'wav', 'ogg', 'flac', 'aac'],
            'archive': ['zip', 'rar', 'tar', 'gz', '7z'],
            'data': ['json', 'xml', 'csv', 'yaml', 'yml'],
            'font': ['ttf', 'woff', 'woff2', 'eot', 'otf']
        }

        categorized = defaultdict(list)
        for ext, count in extensions.items():
            classified = False
            for category, ext_list in categories.items():
                if ext in ext_list:
                    categorized[category].append({'extension': ext, 'count': count})
                    classified = True
                    break

            if not classified:
                categorized['other'].append({'extension': ext, 'count': count})

        return {
            'total_with_extension': sum(extensions.values()),
            'unique_extensions': len(extensions),
            'extension_distribution': dict(extensions.most_common(20)),
            'categorized_extensions': dict(categorized),
            'most_common': extensions.most_common(1)[0] if extensions else None
        }

    def _analyze_parameters(self) -> Dict:
        """Analyze query parameters in detail."""

        params = self.components['all']['query_params']

        param_stats = {}
        for param_name, values in params.items():
            param_stats[param_name] = {
                'occurrences': sum(values.values()),
                'unique_values': len(values),
                'most_common_value': values.most_common(1)[0] if values else None,
                'sample_values': list(values.keys())[:10]
            }

        # sort by occurrence
        sorted_params = sorted(
            param_stats.items(),
            key=lambda x: x[1]['occurrences'],
            reverse=True
        )

        return {
            'total_unique_parameters': len(params),
            'parameter_statistics': dict(sorted_params[:30]),
            'parameters_by_frequency': [p[0] for p in sorted_params[:20]]
        }

    def _analyze_fragments(self) -> Dict:
        """Analyze URL fragments."""

        fragments = self.components['all']['fragments']

        # Classify fragments using shared utility
        anchors = []
        routes = []
        other = []

        for fragment in fragments:
            classification = classify_fragment(fragment)
            if classification == 'anchor':
                anchors.append(fragment)
            elif classification == 'route':
                routes.append(fragment)
            else:
                other.append(fragment)

        return {
            'total_urls_with_fragments': sum(fragments.values()),
            'unique_fragments': len(fragments),
            'fragment_distribution': dict(fragments.most_common(20)),
            'anchor_links': len(anchors),
            'client_side_routes': len(routes),
            'other_fragments': len(other),
            'top_fragments': list(fragments.keys())[:20]
        }

    def _analyze_encoding(self) -> Dict:
        """Analyze encoding patterns."""

        encoded = self.components['all']['encoded_components']

        encoding_summary = defaultdict(int)
        examples = defaultdict(list)

        for enc in encoded:
            enc_type = enc.get('type', 'unknown')
            encoding_summary[enc_type] += enc.get('count', 1)

            if 'examples' in enc:
                examples[enc_type].extend(enc['examples'][:3])

        return {
            'encoding_types_found': list(encoding_summary.keys()),
            'encoding_counts': dict(encoding_summary),
            'examples': dict(examples)
        }

    def _analyze_special_chars(self) -> Dict:
        """Analyze special character usage."""

        chars = self.components['all']['special_chars']

        return {
            'total_special_chars': sum(chars.values()),
            'unique_special_chars': len(chars),
            'character_distribution': dict(chars.most_common()),
            'unusual_chars': [c for c, count in chars.items() if c in '<>"|{}[]\\']
        }

    def _identify_structure_patterns(self) -> Dict:
        """Identify common URL structure patterns."""

        patterns = self.url_patterns

        structure_types = Counter()

        for pattern in patterns:
            # build structure signature
            sig_parts = []

            sig_parts.append(pattern['scheme'])

            if pattern['has_auth']:
                sig_parts.append('AUTH')

            sig_parts.append('HOST')

            if pattern['has_port']:
                sig_parts.append('PORT')

            sig_parts.append(f"PATH[{pattern['path_segments']}]")

            if pattern['has_query']:
                sig_parts.append('QUERY')

            if pattern['has_fragment']:
                sig_parts.append('FRAGMENT')

            signature = '://'.join([sig_parts[0]] + ['/'.join(sig_parts[1:])])
            structure_types[signature] += 1

        return {
            'total_structure_patterns': len(structure_types),
            'top_structures': dict(structure_types.most_common(20)),
            'urls_with_auth': sum(1 for p in patterns if p['has_auth']),
            'urls_with_port': sum(1 for p in patterns if p['has_port']),
            'urls_with_query': sum(1 for p in patterns if p['has_query']),
            'urls_with_fragment': sum(1 for p in patterns if p['has_fragment'])
        }

    def _extract_embedded_data(self) -> Dict:
        """Extract embedded data from URL components."""

        extracted = {
            'ids': Counter(),
            'dates': Counter(),
            'uuids': [],
            'tokens': [],
            'numeric_values': Counter()
        }

        # uuid pattern
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

        # date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # yyyy-mm-dd
            r'\d{4}/\d{2}/\d{2}',  # yyyy/mm/dd
            r'\d{2}-\d{2}-\d{4}',  # dd-mm-yyyy
        ]

        # id pattern (numeric)
        id_pattern = r'\b\d{6,}\b'

        for path in self.components['all']['paths']:
            # uuids
            uuids = re.findall(uuid_pattern, path, re.IGNORECASE)
            extracted['uuids'].extend(uuids)

            # dates
            for date_pattern in date_patterns:
                dates = re.findall(date_pattern, path)
                for date in dates:
                    extracted['dates'][date] += 1

            # ids
            ids = re.findall(id_pattern, path)
            for id_val in ids:
                extracted['ids'][id_val] += 1

        return {
            'uuid_count': len(extracted['uuids']),
            'unique_uuids': len(set(extracted['uuids'])),
            'date_count': sum(extracted['dates'].values()),
            'unique_dates': len(extracted['dates']),
            'top_dates': dict(extracted['dates'].most_common(10)),
            'numeric_id_count': sum(extracted['ids'].values()),
            'top_ids': dict(extracted['ids'].most_common(10))
        }


def execute(data: List[Dict]) -> Dict:
    """
    Main execution function for URL component parsing.

    Args:
        data: List of URL dictionaries from JSONL

    Returns:
        Component analysis results
    """
    parser = URLComponentParser()
    return parser.analyze(data)


def print_summary(results: Dict):
    """Print human-readable summary."""

    print("URL component analysis summary")

    # schemes
    schemes = results['scheme_analysis']
    print("Schemes:")
    print(f"Security ratio (HTTPS): {schemes['security_ratio']:.2%}")
    print(f"Distribution: {schemes['scheme_distribution']}")

    # extensions
    extensions = results['extension_analysis']
    print("File extensions:")
    print(f"Unique extensions: {extensions['unique_extensions']}")
    if extensions['most_common']:
        print(f"Most common: {extensions['most_common'][0]} ({extensions['most_common'][1]} times)")

    # parameters
    params = results['parameter_analysis']
    print("Query parameters:")
    print(f"Unique parameters: {params['total_unique_parameters']}")
