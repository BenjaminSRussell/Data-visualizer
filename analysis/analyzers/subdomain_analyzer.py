"""
Subdomain & Domain Intelligence Analyzer

Purpose: Deep analysis of domain/subdomain structure, cross-domain linking,
         external dependencies, and domain-based clustering
"""

from collections import Counter, defaultdict
from typing import Dict, List
from urllib.parse import urlparse

try:
    import tldextract  # type: ignore
except ImportError:
    tldextract = None


class SubdomainAnalyzer:
    """Analyze subdomain patterns, cross-domain relationships, and domain intelligence."""

    def __init__(self):
        self.domains = defaultdict(lambda: {
            'urls': [],
            'subdomains': set(),
            'external_links': Counter(),
            'internal_links': 0,
            'depth_distribution': Counter(),
            'path_patterns': Counter()
        })
        self.subdomain_map = defaultdict(list)
        self.cross_domain_links = []
        self.url_data = {}

    def analyze(self, data: List[Dict]) -> Dict:
        """
        Perform comprehensive subdomain and domain analysis.

        Args:
            data: List of URL dictionaries from JSONL

        Returns:
            Domain/subdomain analysis results
        """
        self._process_urls(data)

        results = {
            'domain_overview': self._get_domain_overview(),
            'subdomain_analysis': self._analyze_subdomains(),
            'cross_domain_patterns': self._analyze_cross_domain(),
            'domain_clustering': self._cluster_by_domain(),
            'external_dependencies': self._analyze_external_deps(),
            'tld_analysis': self._analyze_tlds(),
            'domain_authority_estimate': self._estimate_domain_authority(),
            'subdomain_hierarchy': self._build_subdomain_hierarchy(),
            'domain_health': self._assess_domain_health()
        }

        return results

    def _process_urls(self, data: List[Dict]):
        """Process URLs and extract domain/subdomain information."""

        for item in data:
            url = item.get('url', '')
            if not url:
                continue

            self.url_data[url] = item

            try:
                # parse url
                parsed = urlparse(url)
                full_domain = parsed.netloc.lower()

                # extract domain components using tldextract
                extracted = tldextract.extract(url)
                domain = f"{extracted.domain}.{extracted.suffix}" if extracted.suffix else extracted.domain
                subdomain = extracted.subdomain or 'root'

                # store domain data
                domain_data = self.domains[domain]
                domain_data['urls'].append(url)
                domain_data['subdomains'].add(subdomain)
                domain_data['depth_distribution'][item.get('depth', 0)] += 1

                # extract path pattern
                path = parsed.path.strip('/')
                if path:
                    path_parts = path.split('/')
                    if len(path_parts) > 0:
                        domain_data['path_patterns'][path_parts[0]] += 1

                # map subdomain to urls
                self.subdomain_map[f"{subdomain}.{domain}"].append(url)

                # analyze links
                links = item.get('links', [])
                for link in links:
                    if link.startswith('http'):
                        link_parsed = urlparse(link)
                        link_domain = link_parsed.netloc.lower()

                        if link_domain == full_domain:
                            domain_data['internal_links'] += 1
                        else:
                            domain_data['external_links'][link_domain] += 1
                            self.cross_domain_links.append({
                                'source': url,
                                'target': link,
                                'source_domain': full_domain,
                                'target_domain': link_domain
                            })

            except Exception as e:
                continue

    def _get_domain_overview(self) -> Dict:
        """Get overview of all domains."""

        total_urls = sum(len(data['urls']) for data in self.domains.values())

        overview = {
            'total_domains': len(self.domains),
            'total_subdomains': len(self.subdomain_map),
            'total_urls': total_urls,
            'domains': {}
        }

        top_domains = []
        for domain, data in self.domains.items():
            domain_info = {
                'url_count': len(data['urls']),
                'subdomain_count': len(data['subdomains']),
                'subdomains': sorted(list(data['subdomains'])),
                'internal_links': data['internal_links'],
                'external_links_count': sum(data['external_links'].values()),
                'unique_external_domains': len(data['external_links']),
                'avg_depth': sum(d * c for d, c in data['depth_distribution'].items()) / sum(data['depth_distribution'].values()) if data['depth_distribution'] else 0,
                'top_paths': dict(data['path_patterns'].most_common(10))
            }
            overview['domains'][domain] = domain_info
            top_domains.append({
                'domain': domain,
                'url_count': len(data['urls']),
                'subdomain_count': len(data['subdomains'])
            })

        top_domains.sort(key=lambda x: x['url_count'], reverse=True)
        overview['top_domains'] = top_domains[:20]

        return overview

    def _analyze_subdomains(self) -> Dict:
        """Analyze subdomain patterns and distribution."""

        subdomain_analysis = {
            'total_unique_subdomains': len(self.subdomain_map),
            'subdomain_distribution': {},
            'subdomain_purposes': {},
            'multi_subdomain_urls': 0
        }

        # count subdomains per domain
        subdomain_counts = Counter()
        for full_subdomain, urls in self.subdomain_map.items():
            subdomain_counts[full_subdomain] = len(urls)

        subdomain_analysis['subdomain_distribution'] = dict(subdomain_counts.most_common(20))

        # classify subdomain purposes
        purposes = {
            'api': ['api', 'rest', 'graphql', 'gateway'],
            'content': ['www', 'blog', 'news', 'content', 'cms'],
            'media': ['cdn', 'static', 'media', 'images', 'assets'],
            'user': ['user', 'account', 'profile', 'my', 'portal'],
            'admin': ['admin', 'manage', 'control', 'dashboard'],
            'staging': ['staging', 'dev', 'test', 'qa', 'beta'],
            'mobile': ['m', 'mobile', 'app'],
            'regional': ['us', 'eu', 'asia', 'uk', 'ca'],
            'service': ['mail', 'smtp', 'ftp', 'auth', 'sso']
        }

        for full_subdomain in self.subdomain_map.keys():
            subdomain = full_subdomain.split('.')[0].lower()

            classified = False
            for purpose, keywords in purposes.items():
                if subdomain in keywords or any(kw in subdomain for kw in keywords):
                    if purpose not in subdomain_analysis['subdomain_purposes']:
                        subdomain_analysis['subdomain_purposes'][purpose] = []
                    subdomain_analysis['subdomain_purposes'][purpose].append(full_subdomain)
                    classified = True
                    break

            if not classified and subdomain != 'root':
                if 'other' not in subdomain_analysis['subdomain_purposes']:
                    subdomain_analysis['subdomain_purposes']['other'] = []
                subdomain_analysis['subdomain_purposes']['other'].append(full_subdomain)

        # count multi-level subdomains
        for full_subdomain in self.subdomain_map.keys():
            if full_subdomain.count('.') > 1:
                subdomain_analysis['multi_subdomain_urls'] += len(self.subdomain_map[full_subdomain])

        return subdomain_analysis

    def _analyze_cross_domain(self) -> Dict:
        """Analyze cross-domain linking patterns."""

        cross_domain = {
            'total_cross_domain_links': len(self.cross_domain_links),
            'unique_external_domains': len(set(link['target_domain'] for link in self.cross_domain_links)),
            'top_external_targets': Counter(),
            'domain_pairs': Counter(),
            'link_types': {
                'same_tld': 0,
                'different_tld': 0,
                'same_org_different_tld': 0
            }
        }

        for link in self.cross_domain_links:
            cross_domain['top_external_targets'][link['target_domain']] += 1

            # create domain pair
            pair = f"{link['source_domain']} -> {link['target_domain']}"
            cross_domain['domain_pairs'][pair] += 1

            # analyze tld patterns
            source_ext = tldextract.extract(link['source'])
            target_ext = tldextract.extract(link['target'])

            if source_ext.suffix == target_ext.suffix:
                cross_domain['link_types']['same_tld'] += 1
            else:
                cross_domain['link_types']['different_tld'] += 1

                if source_ext.domain == target_ext.domain:
                    cross_domain['link_types']['same_org_different_tld'] += 1

        cross_domain['top_external_targets'] = dict(cross_domain['top_external_targets'].most_common(20))
        cross_domain['top_domain_pairs'] = dict(cross_domain['domain_pairs'].most_common(10))

        return cross_domain

    def _cluster_by_domain(self) -> Dict:
        """Cluster URLs by domain characteristics."""

        clusters = {
            'by_size': {},
            'by_complexity': {},
            'by_external_ratio': {}
        }

        # size-based clustering
        for domain, data in self.domains.items():
            url_count = len(data['urls'])

            if url_count < 10:
                size_class = 'tiny'
            elif url_count < 100:
                size_class = 'small'
            elif url_count < 1000:
                size_class = 'medium'
            else:
                size_class = 'large'

            if size_class not in clusters['by_size']:
                clusters['by_size'][size_class] = []
            clusters['by_size'][size_class].append({
                'domain': domain,
                'url_count': url_count
            })

        # complexity clustering (based on subdomains)
        for domain, data in self.domains.items():
            subdomain_count = len(data['subdomains'])

            if subdomain_count == 1:
                complexity = 'simple'
            elif subdomain_count < 5:
                complexity = 'moderate'
            else:
                complexity = 'complex'

            if complexity not in clusters['by_complexity']:
                clusters['by_complexity'][complexity] = []
            clusters['by_complexity'][complexity].append({
                'domain': domain,
                'subdomain_count': subdomain_count
            })

        # external link ratio
        for domain, data in self.domains.items():
            total_links = data['internal_links'] + sum(data['external_links'].values())
            external_ratio = sum(data['external_links'].values()) / total_links if total_links > 0 else 0

            if external_ratio < 0.2:
                ratio_class = 'mostly_internal'
            elif external_ratio < 0.5:
                ratio_class = 'balanced'
            else:
                ratio_class = 'mostly_external'

            if ratio_class not in clusters['by_external_ratio']:
                clusters['by_external_ratio'][ratio_class] = []
            clusters['by_external_ratio'][ratio_class].append({
                'domain': domain,
                'external_ratio': external_ratio
            })

        return clusters

    def _analyze_external_deps(self) -> Dict:
        """Analyze external dependencies."""

        dependencies = {
            'by_category': defaultdict(list),
            'critical_dependencies': [],
            'third_party_services': Counter()
        }

        # service categories
        service_patterns = {
            'cdn': ['cloudflare', 'akamai', 'fastly', 'cloudfront'],
            'analytics': ['google-analytics', 'ga', 'analytics', 'mixpanel'],
            'social': ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube'],
            'ads': ['doubleclick', 'adsense', 'adwords', 'googlesyndication'],
            'auth': ['okta', 'auth0', 'azure', 'sso'],
            'payments': ['stripe', 'paypal', 'square'],
            'maps': ['maps.google', 'mapbox'],
            'fonts': ['fonts.google', 'typekit'],
            'video': ['youtube', 'vimeo', 'wistia']
        }

        for domain_data in self.domains.values():
            for ext_domain, count in domain_data['external_links'].items():
                # categorize
                categorized = False
                for category, patterns in service_patterns.items():
                    if any(pattern in ext_domain.lower() for pattern in patterns):
                        dependencies['by_category'][category].append({
                            'domain': ext_domain,
                            'link_count': count
                        })
                        categorized = True
                        break

                if not categorized:
                    dependencies['by_category']['other'].append({
                        'domain': ext_domain,
                        'link_count': count
                    })

                dependencies['third_party_services'][ext_domain] += count

        # identify critical dependencies (high usage)
        for domain, count in dependencies['third_party_services'].most_common(10):
            dependencies['critical_dependencies'].append({
                'domain': domain,
                'total_links': count,
                'criticality': 'high' if count > 100 else 'medium' if count > 20 else 'low'
            })

        dependencies['by_category'] = dict(dependencies['by_category'])

        return dependencies

    def _analyze_tlds(self) -> Dict:
        """Analyze top-level domain distribution."""

        tld_analysis = {
            'tld_distribution': Counter(),
            'domain_distribution': Counter(),
            'tld_insights': {}
        }

        for url in self.url_data.keys():
            extracted = tldextract.extract(url)

            if extracted.suffix:
                tld_analysis['tld_distribution'][extracted.suffix] += 1

            if extracted.domain:
                tld_analysis['domain_distribution'][extracted.domain] += 1

        tld_analysis['tld_distribution'] = dict(tld_analysis['tld_distribution'].most_common(20))
        tld_analysis['domain_distribution'] = dict(tld_analysis['domain_distribution'].most_common(20))

        # tld insights
        for tld in tld_analysis['tld_distribution'].keys():
            if tld in ['com', 'net', 'org']:
                category = 'generic'
            elif len(tld) == 2:
                category = 'country_code'
            elif tld in ['edu', 'gov', 'mil']:
                category = 'sponsored'
            else:
                category = 'new_gtld'

            tld_analysis['tld_insights'][tld] = category

        return tld_analysis

    def _estimate_domain_authority(self) -> Dict:
        """Estimate domain authority based on link patterns."""

        authority = {}

        for domain, data in self.domains.items():
            # simple authority score based on:
            # 1. internal link density
            # 2. external links received (if we had that data)
            # 3. url count
            # 4. subdomain complexity

            score = 0

            # url count factor
            url_count = len(data['urls'])
            score += min(url_count / 10, 50)

            # internal link density
            if url_count > 0:
                internal_density = data['internal_links'] / url_count
                score += min(internal_density * 10, 30)

            # subdomain diversity
            subdomain_diversity = len(data['subdomains'])
            score += min(subdomain_diversity * 2, 10)

            # depth distribution (prefer balanced)
            if data['depth_distribution']:
                avg_depth = sum(d * c for d, c in data['depth_distribution'].items()) / sum(data['depth_distribution'].values())
                if 2 <= avg_depth <= 4:
                    score += 10

            authority[domain] = {
                'estimated_authority': min(score, 100),
                'url_count': url_count,
                'internal_links': data['internal_links'],
                'subdomains': len(data['subdomains'])
            }

        return authority

    def _build_subdomain_hierarchy(self) -> Dict:
        """Build hierarchical subdomain structure."""

        hierarchy = defaultdict(lambda: defaultdict(list))

        for full_subdomain, urls in self.subdomain_map.items():
            parts = full_subdomain.split('.')

            if len(parts) >= 2:
                domain = '.'.join(parts[-2:])
                subdomain = '.'.join(parts[:-2]) if len(parts) > 2 else 'root'

                hierarchy[domain][subdomain].extend(urls)

        return dict(hierarchy)

    def _assess_domain_health(self) -> Dict:
        """Assess overall domain health."""

        health = {}

        for domain, data in self.domains.items():
            score = 100

            # penalty for too many external dependencies
            total_links = data['internal_links'] + sum(data['external_links'].values())
            external_ratio = 0
            if total_links > 0:
                external_ratio = sum(data['external_links'].values()) / total_links
                if external_ratio > 0.7:
                    score -= 20

            # bonus for good internal linking
            internal_density = 0
            if len(data['urls']) > 0:
                internal_density = data['internal_links'] / len(data['urls'])
                if internal_density < 1:
                    score -= 15

            # penalty for too many subdomains
            if len(data['subdomains']) > 10:
                score -= 10

            health[domain] = {
                'health_score': max(score, 0),
                'url_count': len(data['urls']),
                'issues': []
            }

            if external_ratio > 0.7:
                health[domain]['issues'].append('High external dependency ratio')
            if internal_density < 1:
                health[domain]['issues'].append('Low internal linking')
            if len(data['subdomains']) > 10:
                health[domain]['issues'].append('High subdomain complexity')

        return health


def execute(data: List[Dict]) -> Dict:
    """
    Main execution function for subdomain analysis.

    Args:
        data: List of URL dictionaries from JSONL

    Returns:
        Subdomain analysis results
    """
    # ensure tldextract availability or provide a basic fallback
    global tldextract
    if tldextract is None:
        class SimpleTLDExtractModule:
            @staticmethod
            def extract(url):
                from urllib.parse import urlparse

                parsed = urlparse(url)
                parts = parsed.netloc.split('.')

                class Result:
                    def __init__(self, domain_parts):
                        if len(domain_parts) >= 2:
                            self.suffix = domain_parts[-1]
                            self.domain = domain_parts[-2]
                            self.subdomain = '.'.join(domain_parts[:-2]) if len(domain_parts) > 2 else ''
                        else:
                            self.suffix = ''
                            self.domain = domain_parts[0] if domain_parts else ''
                            self.subdomain = ''

                return Result(parts)

        tldextract = SimpleTLDExtractModule

    analyzer = SubdomainAnalyzer()
    return analyzer.analyze(data)


def print_summary(results: Dict):
    """Print summary."""

    print("Subdomain and domain analysis summary")

    overview = results['domain_overview']
    print(f"Total Domains: {overview['total_domains']}")
    print(f"Total Subdomains: {overview['total_subdomains']}")

    subdomain = results['subdomain_analysis']
    print(f"Unique Subdomains: {subdomain['total_unique_subdomains']}")

    if 'subdomain_purposes' in subdomain:
        print("Purpose classification:")
        for purpose, subs in list(subdomain['subdomain_purposes'].items())[:5]:
            print(f"{purpose}: {len(subs)} subdomains")

    deps = results['external_dependencies']
    if deps['critical_dependencies']:
        print(f"Critical dependencies: {len(deps['critical_dependencies'])}")
        for dep in deps['critical_dependencies'][:3]:
            print(f"{dep['domain']}: {dep['total_links']} links")
