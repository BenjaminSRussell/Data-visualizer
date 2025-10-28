"""
Diagnostic Analyzer - Identify data quality problems
"""

import json
from collections import Counter, defaultdict
from datetime import datetime
from urllib.parse import urlparse


class DiagnosticAnalyzer:

    def __init__(self, jsonl_file):
        self.jsonl_file = jsonl_file
        self.urls = []
        self.load_data()

    def load_data(self):
        with open(self.jsonl_file, 'r') as f:
            for line in f:
                self.urls.append(json.loads(line))

    def diagnose_all(self):
        print("Diagnostic analysis")

        self.diagnose_duplicates()
        self.diagnose_missing_data()
        self.diagnose_fragments()
        self.diagnose_depth_issues()
        self.diagnose_link_patterns()
        self.diagnose_temporal_patterns()
        self.diagnose_path_semantics()

    def diagnose_duplicates(self):
        print("1. Duplicate URL analysis")

        base_urls = defaultdict(list)
        for u in self.urls:
            parsed = urlparse(u['url'])
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                base += f"?{parsed.query}"
            base_urls[base].append(u)

        duplicates = {base: urls for base, urls in base_urls.items() if len(urls) > 1}

        print(f"Total URLs: {len(self.urls):,}")
        print(f"Unique base URLs: {len(base_urls):,}")
        print(f"Wasted URLs from fragments: {len(self.urls) - len(base_urls):,}")
        print(f"Data inflation: {(len(self.urls) - len(base_urls)) / len(self.urls) * 100:.1f}%")

        worst = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:3]
        if worst:
            print("Top duplicate URLs:")
            for base, urls in worst:
                print(f"{len(urls)} versions: {base[:60]}")

    def diagnose_missing_data(self):
        print("2. Missing data analysis")

        no_content_type = sum(1 for u in self.urls if not u.get('content_type'))
        no_status = sum(1 for u in self.urls if not u.get('status_code'))
        no_title = sum(1 for u in self.urls if not u.get('title'))

        print(f"Missing content_type: {no_content_type:,} ({no_content_type/len(self.urls)*100:.1f}%)")
        print(f"Missing status_code: {no_status:,} ({no_status/len(self.urls)*100:.1f}%)")
        print(f"Missing title: {no_title:,} ({no_title/len(self.urls)*100:.1f}%)")

    def diagnose_fragments(self):
        print("3. Fragment analysis")

        fragments = Counter()
        for u in self.urls:
            frag = urlparse(u['url']).fragment
            if frag:
                fragments[frag] += 1

        print(f"URLs with fragments: {sum(fragments.values()):,}")
        print(f"Unique fragments: {len(fragments):,}")

        if fragments:
            print("Top 5 fragments:")
            for frag, count in fragments.most_common(5):
                print(f"#{frag}: {count:,}")

    def diagnose_depth_issues(self):
        print("4. Depth analysis")

        depths = [u.get('depth', 0) for u in self.urls]
        depth_dist = Counter(depths)

        print("Depth distribution:")
        for depth in sorted(depth_dist.keys())[:10]:
            print(f"Depth {depth}: {depth_dist[depth]:,} URLs")

    def diagnose_link_patterns(self):
        print("5. Link pattern analysis")

        parents = Counter(u.get('parent_url') for u in self.urls if u.get('parent_url'))
        print(f"URLs with parent data: {sum(1 for u in self.urls if u.get('parent_url')):,}")
        print(f"Unique parent URLs: {len(parents):,}")

        if parents:
            print("Top parent URLs:")
            for parent, count in parents.most_common(3):
                print(f"{count:,} children: {parent[:60]}")

    def diagnose_temporal_patterns(self):
        print("6. Temporal pattern analysis")

        discovery_times = [u.get('discovered_at') for u in self.urls if u.get('discovered_at')]

        if not discovery_times:
            print("No temporal data available")
            return

        min_time = min(discovery_times)
        max_time = max(discovery_times)
        duration = max_time - min_time

        print(f"First discovered: {datetime.fromtimestamp(min_time)}")
        print(f"Last discovered: {datetime.fromtimestamp(max_time)}")
        print(f"Total duration: {duration/60:.1f} minutes")

    def diagnose_path_semantics(self):
        print("7. Path semantic analysis")

        path_segments = defaultdict(Counter)

        for u in self.urls:
            path = urlparse(u['url']).path
            segments = [s for s in path.split('/') if s]

            for i, seg in enumerate(segments):
                path_segments[i][seg] += 1

        print(f"Maximum path depth: {max(path_segments.keys()) if path_segments else 0}")

        for level in range(min(2, len(path_segments))):
            print(f"Level {level} top 5 segments:")
            for seg, count in path_segments[level].most_common(5):
                print(f"/{seg}: {count:,}")

    def generate_improvement_report(self):
        print("Improvement impact analysis")

        base_urls = set()
        for u in self.urls:
            parsed = urlparse(u['url'])
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                base += f"?{parsed.query}"
            base_urls.add(base)

        print("Normalization impact:")
        print(f"Current URLs: {len(self.urls):,}")
        print(f"After normalization: {len(base_urls):,}")
        print(f"Reduction: {len(self.urls) - len(base_urls):,} URLs ({(len(self.urls) - len(base_urls))/len(self.urls)*100:.1f}%)")

        print("Conclusion:")
        print(f"1. Normalization would reduce dataset by ~{(len(self.urls) - len(base_urls))/len(self.urls)*100:.0f}%")
        print(f"2. Focus should be on {len(base_urls):,} unique pages")
        print(f"3. Currently tracking {len(set(urlparse(u['url']).netloc for u in self.urls))} domains")


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
