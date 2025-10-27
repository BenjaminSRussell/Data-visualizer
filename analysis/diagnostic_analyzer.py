"""
Diagnostic Analyzer - Identify specific problems and test normalization improvements
"""

import json
from collections import Counter, defaultdict
from urllib.parse import urlparse, parse_qs
from datetime import datetime


class DiagnosticAnalyzer:
    """Analyze what's actually wrong with the data and validate improvements"""

    def __init__(self, jsonl_file):
        self.jsonl_file = jsonl_file
        self.urls = []
        self.load_data()

    def load_data(self):
        """Load URL data"""
        print(f"Loading {self.jsonl_file}...")
        with open(self.jsonl_file, 'r') as f:
            for line in f:
                self.urls.append(json.loads(line))
        print(f"✓ Loaded {len(self.urls):,} URLs\n")

    def diagnose_all(self):
        """Run all diagnostic tests"""
        print("="*80)
        print("DIAGNOSTIC ANALYSIS - Identifying Specific Problems")
        print("="*80 + "\n")

        self.diagnose_duplicates()
        self.diagnose_missing_data()
        self.diagnose_fragments()
        self.diagnose_depth_issues()
        self.diagnose_link_patterns()
        self.diagnose_temporal_patterns()
        self.diagnose_path_semantics()

    def diagnose_duplicates(self):
        """Identify duplicate URLs with only fragment differences"""
        print("1. DUPLICATE URL PROBLEM")
        print("-" * 80)

        base_urls = defaultdict(list)
        for u in self.urls:
            parsed = urlparse(u['url'])
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                base += f"?{parsed.query}"
            base_urls[base].append(u)

        duplicates = {base: urls for base, urls in base_urls.items() if len(urls) > 1}

        print(f"   Total URLs: {len(self.urls):,}")
        print(f"   Unique base URLs: {len(base_urls):,}")
        print(f"   Base URLs with fragments: {len(duplicates):,}")
        print(f"   Wasted URLs from fragments: {len(self.urls) - len(base_urls):,}")
        print(f"   Data inflation: {(len(self.urls) - len(base_urls)) / len(self.urls) * 100:.1f}%")

        # show worst offenders
        worst = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        print(f"\n   Worst duplicate URLs:")
        for base, urls in worst:
            fragments = [urlparse(u['url']).fragment for u in urls]
            unique_frags = list(set(fragments))[:5]
            print(f"      {len(urls)} versions: {base[:60]}...")
            print(f"         Fragments: {', '.join(unique_frags)}")

        # impact analysis
        unique_with_data = sum(1 for urls in base_urls.values()
                               if any(u.get('content_type') for u in urls))
        print(f"\n   IMPROVEMENT: Normalizing would reduce dataset to {len(base_urls):,} URLs")
        print(f"      ({unique_with_data:,} with actual content)")
        print()

    def diagnose_missing_data(self):
        """Identify URLs with missing critical data"""
        print("2. MISSING DATA PROBLEM")
        print("-" * 80)

        no_content_type = sum(1 for u in self.urls if not u.get('content_type'))
        no_status = sum(1 for u in self.urls if not u.get('status_code'))
        no_title = sum(1 for u in self.urls if not u.get('title'))
        no_links = sum(1 for u in self.urls if not u.get('links') or len(u['links']) == 0)

        print(f"   URLs missing content_type: {no_content_type:,} ({no_content_type/len(self.urls)*100:.1f}%)")
        print(f"   URLs missing status_code: {no_status:,} ({no_status/len(self.urls)*100:.1f}%)")
        print(f"   URLs missing title: {no_title:,} ({no_title/len(self.urls)*100:.1f}%)")
        print(f"   URLs missing links: {no_links:,} ({no_links/len(self.urls)*100:.1f}%)")

        # check if missing data correlates with fragments
        fragment_urls = [u for u in self.urls if urlparse(u['url']).fragment]
        frag_no_content = sum(1 for u in fragment_urls if not u.get('content_type'))

        print(f"\n   Fragment URLs: {len(fragment_urls):,}")
        print(f"   Fragment URLs without content: {frag_no_content:,} ({frag_no_content/len(fragment_urls)*100:.1f}%)")
        print(f"\n   ISSUE: Fragment-only URLs were likely not crawled, just discovered")
        print()

    def diagnose_fragments(self):
        """Analyze fragment usage patterns"""
        print("3. FRAGMENT PATTERN ANALYSIS")
        print("-" * 80)

        fragments = Counter()
        fragment_purposes = {
            'navigation': ['main-content', 'topMobile', 'skip-nav'],
            'section': ['overview', 'about-', 'admission-', 'requirements'],
            'accessibility': ['main-content', 'skip-'],
            'tabs': ['tab-', 'panel-']
        }

        for u in self.urls:
            frag = urlparse(u['url']).fragment
            if frag:
                fragments[frag] += 1

        print(f"   URLs with fragments: {sum(fragments.values()):,}")
        print(f"   Unique fragments: {len(fragments):,}")

        # categorize fragments
        navigation_frags = sum(count for frag, count in fragments.items()
                              if any(frag.startswith(nav) for nav in ['main-content', 'topMobile']))
        print(f"   Navigation fragments: {navigation_frags:,} ({navigation_frags/sum(fragments.values())*100:.1f}%)")

        print(f"\n   Top fragments:")
        for frag, count in fragments.most_common(10):
            print(f"      #{frag}: {count:,}")

        print(f"\n   RECOMMENDATION: Normalize URLs by removing fragments")
        print(f"      This would eliminate {sum(fragments.values()):,} duplicate URLs")
        print()

    def diagnose_depth_issues(self):
        """Analyze depth calculation issues"""
        print("4. DEPTH ANALYSIS")
        print("-" * 80)

        depths = [u.get('depth', 0) for u in self.urls]
        depth_dist = Counter(depths)

        print(f"   Depth distribution:")
        for depth in sorted(depth_dist.keys()):
            print(f"      Depth {depth}: {depth_dist[depth]:,} URLs")

        # check if fragment urls have same depth as base
        base_with_frags = defaultdict(list)
        for u in self.urls:
            parsed = urlparse(u['url'])
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            base_with_frags[base].append(u)

        depth_inconsistencies = 0
        for base, urls in base_with_frags.items():
            if len(urls) > 1:
                depths_in_group = set(u.get('depth') for u in urls)
                if len(depths_in_group) > 1:
                    depth_inconsistencies += 1

        print(f"\n   URLs with inconsistent depths (same base, different fragments): {depth_inconsistencies}")
        print(f"   ISSUE: Fragment variations shouldn't affect depth")
        print()

    def diagnose_link_patterns(self):
        """Analyze linking patterns"""
        print("5. LINK PATTERN ANALYSIS")
        print("-" * 80)

        # parent-child relationships
        parents = Counter(u.get('parent_url') for u in self.urls if u.get('parent_url'))

        print(f"   URLs with parent data: {sum(1 for u in self.urls if u.get('parent_url')):,}")
        print(f"   Unique parent URLs: {len(parents):,}")

        print(f"\n   Top parent URLs (most children):")
        for parent, count in parents.most_common(5):
            print(f"      {count:,} children: {parent[:70]}...")

        # analyze if parents point to fragment vs base
        parent_has_fragment = sum(1 for p in parents.keys() if urlparse(p).fragment)
        print(f"\n   Parent URLs with fragments: {parent_has_fragment:,} ({parent_has_fragment/len(parents)*100:.1f}%)")

        print(f"\n   ISSUE: Parent URLs should reference base URL, not fragments")
        print()

    def diagnose_temporal_patterns(self):
        """Analyze discovery time patterns"""
        print("6. TEMPORAL PATTERN ANALYSIS")
        print("-" * 80)

        # group by discovery time
        discovery_times = [u.get('discovered_at') for u in self.urls if u.get('discovered_at')]

        if not discovery_times:
            print("   No temporal data available")
            print()
            return

        min_time = min(discovery_times)
        max_time = max(discovery_times)
        duration = max_time - min_time

        print(f"   First discovered: {datetime.fromtimestamp(min_time)}")
        print(f"   Last discovered: {datetime.fromtimestamp(max_time)}")
        print(f"   Total duration: {duration:.0f} seconds ({duration/60:.1f} minutes)")

        # bucket by minute
        by_minute = Counter()
        for ts in discovery_times:
            minute = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
            by_minute[minute] += 1

        print(f"\n   Discovery rate:")
        print(f"      Average: {len(discovery_times)/len(by_minute):.1f} URLs/minute")
        print(f"      Peak minute: {max(by_minute.values())} URLs")

        # show bursts
        bursts = [(minute, count) for minute, count in by_minute.items() if count > 100]
        print(f"   Bursts (>100 URLs/min): {len(bursts)}")

        print(f"\n   INSIGHT: Temporal batching can reveal crawler behavior")
        print()

    def diagnose_path_semantics(self):
        """Analyze semantic meaning of paths"""
        print("7. PATH SEMANTIC ANALYSIS")
        print("-" * 80)

        path_segments = defaultdict(Counter)

        for u in self.urls:
            path = urlparse(u['url']).path
            segments = [s for s in path.split('/') if s]

            for i, seg in enumerate(segments):
                path_segments[i][seg] += 1

        print(f"   Maximum path depth: {max(path_segments.keys()) if path_segments else 0}")

        for level in range(min(3, len(path_segments))):
            print(f"\n   Level {level} path segments (top 10):")
            for seg, count in path_segments[level].most_common(10):
                # try to infer meaning
                meaning = self._infer_segment_meaning(seg)
                print(f"      /{seg}: {count:,} {meaning}")

        print(f"\n   INSIGHT: Path hierarchy reveals site structure")
        print()

    def _infer_segment_meaning(self, segment):
        """Infer semantic meaning of path segment"""
        if segment in ['academics', 'programs', 'departments']:
            return '(academic content)'
        elif segment in ['news', 'unotes', 'press-releases']:
            return '(news/updates)'
        elif segment in ['directory', 'staff', 'faculty']:
            return '(people directory)'
        elif segment in ['about', 'info']:
            return '(informational)'
        elif segment.isdigit():
            return '(ID/year)'
        elif segment.startswith('ss-') or segment.startswith('ns-'):
            return '(story prefix)'
        return ''

    def generate_improvement_report(self):
        """Generate report on what would improve with normalization"""
        print("\n" + "="*80)
        print("IMPROVEMENT IMPACT ANALYSIS")
        print("="*80 + "\n")

        # calculate improvements
        base_urls = set()
        for u in self.urls:
            parsed = urlparse(u['url'])
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                base += f"?{parsed.query}"
            base_urls.add(base)

        print("IF WE NORMALIZE (remove fragments, deduplicate):")
        print(f"   Current URLs: {len(self.urls):,}")
        print(f"   After normalization: {len(base_urls):,}")
        print(f"   Reduction: {len(self.urls) - len(base_urls):,} URLs ({(len(self.urls) - len(base_urls))/len(self.urls)*100:.1f}%)")

        # data quality improvements
        unique_with_content = 0
        for u in self.urls:
            parsed = urlparse(u['url'])
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if u.get('content_type') and base in base_urls:
                unique_with_content += 1

        print(f"\n   URLs with actual content: {sum(1 for u in self.urls if u.get('content_type')):,}")
        print(f"   Unique URLs with content: {unique_with_content:,}")

        print(f"\nCONCLUSION:")
        print(f"   1. Normalization would reduce dataset by ~{(len(self.urls) - len(base_urls))/len(self.urls)*100:.0f}%")
        print(f"   2. This would improve analysis accuracy")
        print(f"   3. Focus should be on {len(base_urls):,} unique pages")
        print(f"   4. Need better domain/subdomain analysis (currently only {len(set(urlparse(u['url']).netloc for u in self.urls))} domains)")
        print(f"   5. Need temporal batch detection (crawl burst analysis)")
        print(f"   6. Need path hierarchy semantic analysis")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python diagnostic_analyzer.py <jsonl_file>")
        sys.exit(1)

    analyzer = DiagnosticAnalyzer(sys.argv[1])
    analyzer.diagnose_all()
    analyzer.generate_improvement_report()


if __name__ == '__main__':
    main()
