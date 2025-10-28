"""
Test Suite 1: Pathological URL Handling

Tests url_utilities.py with extreme edge cases that stress-test parsers.

Replaces: Basic URL parsing validation
Why Deeper: Current code assumes well-formed URLs, doesn't validate edge cases

Test Categories:
1. Extreme depth URLs (50+ levels)
2. Extreme length URLs (1000+ characters)
3. Malformed encoding
4. Recursive parameters
5. Path traversal attempts
6. Protocol confusion
7. Mixed encoding (UTF-8, Punycode)
8. Fragment bombs
9. Null bytes and control characters
10. Edge cases (empty strings, invalid ports, etc.)

Critical Findings:
- Line 47 in url_utilities.py: Bare `except Exception:` swallows all errors
- Line 78-85: No length validation for depth calculation
- Line 257: File extension extraction vulnerable to path traversal
- No URL length limits anywhere in the codebase
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.utils.url_utilities import (
    parse_url_components,
    get_path_depth,
    get_base_url,
    is_same_domain,
    is_internal_link,
    resolve_link,
    extract_fragment,
    count_fragments,
    classify_fragment,
    extract_file_extension,
    get_depth_distribution,
    extract_path_segments,
    get_query_param_count,
    get_path_length
)


# =============================================================================
# TIER 1: Critical Edge Cases - Extreme Depth
# =============================================================================

class TestExtremeDepth:
    """Test URLs with extreme path depth."""

    def test_depth_50_levels(self):
        """50-level deep URL should parse without error."""
        url = "https://example.com/" + "/".join([f"level{i}" for i in range(50)])
        depth = get_path_depth(url)
        assert depth == 50, f"Expected depth 50, got {depth}"

    def test_depth_100_levels(self):
        """100-level deep URL should parse without error."""
        url = "https://example.com/" + "/".join([f"l{i}" for i in range(100)])
        depth = get_path_depth(url)
        assert depth == 100, f"Expected depth 100, got {depth}"

    def test_depth_performance_regression(self):
        """Depth calculation should be O(n) not O(n²)."""
        import time

        # Test with increasing depths
        depths_to_test = [100, 500, 1000]
        times = []

        for depth_count in depths_to_test:
            url = "https://example.com/" + "/".join([f"l{i}" for i in range(depth_count)])

            start = time.perf_counter()
            for _ in range(100):  # Run 100 times for stable measurement
                get_path_depth(url)
            end = time.perf_counter()

            times.append((end - start) / 100)

        # Time should scale roughly linearly
        # If O(n²), time_1000 / time_100 ≈ 100
        # If O(n), time_1000 / time_100 ≈ 10
        ratio = times[2] / times[0]
        assert ratio < 20, f"Performance regression detected: ratio={ratio}"

    def test_parse_components_extreme_depth(self):
        """parse_url_components should handle extreme depth."""
        url = "https://example.com/" + "/".join([f"level{i}" for i in range(50)])
        components = parse_url_components(url)

        assert components['path_depth'] == 50
        assert len(components['path_segments']) == 50
        assert components['scheme'] == 'https'
        assert components['netloc'] == 'example.com'

    def test_extract_path_segments_extreme_depth(self):
        """extract_path_segments should handle extreme depth."""
        url = "https://example.com/" + "/".join([f"seg{i}" for i in range(100)])
        segments = extract_path_segments(url)

        assert len(segments) == 100
        assert segments[0] == 'seg0'
        assert segments[99] == 'seg99'


# =============================================================================
# TIER 1: Critical Edge Cases - Extreme Length
# =============================================================================

class TestExtremeLength:
    """Test URLs with extreme character length."""

    def test_length_1000_chars_path(self):
        """1000-character path should parse."""
        url = "https://example.com/" + "a" * 1000
        components = parse_url_components(url)

        assert components['scheme'] == 'https'
        assert len(components['path']) == 1001  # 1000 + leading /

    def test_length_10000_chars_path(self):
        """10,000-character path should parse."""
        url = "https://example.com/path/" + "x" * 10000
        path_length = get_path_length(url)

        assert path_length == 10006  # /path/ + 10000 chars

    def test_length_massive_query_string(self):
        """URL with 500 query parameters should parse."""
        url = "https://example.com/page?" + "&".join([f"param{i}=value{i}" for i in range(500)])
        param_count = get_query_param_count(url)

        assert param_count == 500

    def test_length_affects_depth_calculation(self):
        """Extreme length shouldn't affect depth accuracy."""
        # Create URL with 5 segments, each 1000 chars long
        segments = ["x" * 1000 for _ in range(5)]
        url = "https://example.com/" + "/".join(segments)

        depth = get_path_depth(url)
        assert depth == 5, f"Length affected depth: expected 5, got {depth}"

    def test_base_url_with_long_domain(self):
        """Very long domain name should parse."""
        # Max domain length is 253 chars, but test with 200
        long_domain = "subdomain." * 20 + "example.com"  # ~220 chars
        url = f"https://{long_domain}/path"

        base = get_base_url(url)
        assert base.startswith("https://")
        assert "example.com" in base


# =============================================================================
# TIER 1: Critical Edge Cases - Malformed Encoding
# =============================================================================

class TestMalformedEncoding:
    """Test URLs with malformed percent encoding."""

    def test_invalid_percent_encoding_XX(self):
        """Invalid %XX encoding should not crash."""
        url = "https://example.com/%XX%YY/path"
        components = parse_url_components(url)

        # Should return something, even if malformed
        assert components is not None
        assert isinstance(components, dict)

    def test_invalid_percent_encoding_ZZ(self):
        """Invalid %ZZ encoding should not crash."""
        url = "https://example.com/%ZZ/page"
        depth = get_path_depth(url)

        assert depth >= 0  # Should return valid depth

    def test_incomplete_percent_encoding(self):
        """Incomplete encoding (path%) should not crash."""
        url = "https://example.com/path%"
        segments = extract_path_segments(url)

        assert isinstance(segments, list)

    def test_double_encoding(self):
        """%2525 (double-encoded %) should parse."""
        url = "https://example.com/%2525/path"
        components = parse_url_components(url)

        assert components['path_depth'] >= 1

    def test_fragment_with_invalid_encoding(self):
        """Fragment with invalid encoding should not crash."""
        url = "https://example.com/page#%XX%YY"
        fragment = extract_fragment(url)

        # Should return something (might be malformed, but shouldn't crash)
        assert fragment is not None or fragment is None  # Either is acceptable


# =============================================================================
# TIER 1: Critical Edge Cases - Recursive Parameters
# =============================================================================

class TestRecursiveParameters:
    """Test URLs with recursive/nested parameters."""

    def test_recursive_query_params(self):
        """Recursive next= parameters should parse."""
        url = "https://example.com/page?next=/page?next=/page"
        param_count = get_query_param_count(url)

        # Should count params, even if semantically recursive
        assert param_count >= 1

    def test_nested_redirect_urls(self):
        """Nested redirect URLs should parse."""
        url = "https://example.com/redirect?url=https://example.com/redirect?url=https://example.com"
        components = parse_url_components(url)

        assert components['scheme'] == 'https'
        assert components['has_query'] is True

    def test_depth_not_fooled_by_query_params(self):
        """Query params with slashes shouldn't affect depth."""
        url = "https://example.com/page?next=/a/b/c/d"
        depth = get_path_depth(url)

        # Depth should be 1 (/page), not affected by query
        assert depth == 1


# =============================================================================
# TIER 2: Real-World Attacks - Path Traversal
# =============================================================================

class TestPathTraversal:
    """Test path traversal attempts."""

    def test_path_traversal_basic(self):
        """Basic path traversal with ../../../../"""
        url = "https://example.com/../../../../etc/passwd"
        components = parse_url_components(url)

        # Should parse segments as-is (normalization is separate concern)
        assert components is not None

    def test_path_traversal_encoded(self):
        """URL-encoded path traversal."""
        url = "https://example.com/..%2F..%2F..%2Fetc%2Fpasswd"
        depth = get_path_depth(url)

        assert depth >= 0

    def test_path_traversal_mixed_dots(self):
        """Mixed ./ and ../ sequences."""
        url = "https://example.com/./././page"
        segments = extract_path_segments(url)

        # Should include '.' segments (normalization is separate)
        assert isinstance(segments, list)

    def test_path_traversal_depth_calculation(self):
        """Path traversal shouldn't cause negative depth."""
        url = "https://example.com/dir/../../../etc/passwd"
        depth = get_path_depth(url)

        # Depth counts segments, not normalized path
        assert depth >= 0


# =============================================================================
# TIER 2: Real-World Attacks - Mixed Encoding
# =============================================================================

class TestMixedEncoding:
    """Test URLs with various character encodings."""

    def test_utf8_encoding_cafe(self):
        """UTF-8 encoded café should parse."""
        url = "https://example.com/café/page"
        components = parse_url_components(url)

        assert components is not None
        assert components['path_depth'] >= 1

    def test_japanese_characters(self):
        """Japanese characters should parse."""
        url = "https://example.com/日本語/ページ"
        depth = get_path_depth(url)

        assert depth == 2

    def test_emoji_in_path(self):
        """Emoji in path should parse."""
        url = "https://example.com/emoji/😀/page"
        segments = extract_path_segments(url)

        assert len(segments) == 3
        assert '😀' in segments[1]

    def test_unicode_math_symbols(self):
        """Unicode math symbols should parse."""
        url = "https://example.com/𝕌𝕟𝕚𝕔𝕠𝕕𝕖/page"
        components = parse_url_components(url)

        assert components['path_depth'] == 2

    def test_greek_characters(self):
        """Greek characters should parse."""
        url = "https://example.com/Ωμέγα/page"
        depth = get_path_depth(url)

        assert depth == 2


# =============================================================================
# TIER 2: Real-World Attacks - Protocol Confusion
# =============================================================================

class TestProtocolConfusion:
    """Test non-HTTP protocols and protocol confusion attacks."""

    def test_javascript_protocol(self):
        """javascript: protocol should be handled."""
        url = "javascript:alert(1)//https://example.com"
        components = parse_url_components(url)

        # Should parse, scheme will be 'javascript'
        assert components['scheme'] == 'javascript'

    def test_data_protocol(self):
        """data: protocol should be handled."""
        url = "data:text/html,<script>alert(1)</script>"
        components = parse_url_components(url)

        assert components['scheme'] == 'data'

    def test_file_protocol(self):
        """file:/// protocol should parse."""
        url = "file:///etc/passwd"
        components = parse_url_components(url)

        assert components['scheme'] == 'file'

    def test_ftp_protocol(self):
        """ftp:// protocol should parse."""
        url = "ftp://example.com/file"
        base_url = get_base_url(url)

        assert base_url.startswith('ftp://')


# =============================================================================
# TIER 2: Real-World Attacks - Punycode Domains
# =============================================================================

class TestPunycodeDomains:
    """Test internationalized domain names (IDN) with Punycode."""

    def test_punycode_domain_basic(self):
        """Punycode domain should parse."""
        url = "https://xn--bcher-kva.example/page"  # bücher.example
        components = parse_url_components(url)

        assert components['scheme'] == 'https'
        assert 'xn--bcher-kva' in components['netloc']

    def test_punycode_domain_russian(self):
        """Russian Punycode domain should parse."""
        url = "https://xn--e1afmkfd.xn--p1ai/page"  # пример.рф
        base_url = get_base_url(url)

        assert 'xn--e1afmkfd' in base_url

    def test_punycode_with_fragment(self):
        """Punycode domain with fragment should parse."""
        url = "https://xn--bcher-kva.example/page#fragment"
        fragment = extract_fragment(url)

        assert fragment == 'fragment'


# =============================================================================
# TIER 2: Real-World Attacks - Fragment Bombs
# =============================================================================

class TestFragmentBombs:
    """Test URLs with massive fragments."""

    def test_fragment_10000_chars(self):
        """10,000-character fragment should parse."""
        url = "https://example.com#" + "A" * 10000
        fragment = extract_fragment(url)

        assert len(fragment) == 10000

    def test_fragment_nested_paths(self):
        """Fragment with 1000 nested paths should parse."""
        url = "https://example.com/page#" + "/".join([f"section{i}" for i in range(1000)])
        fragment = extract_fragment(url)

        assert 'section0' in fragment
        assert 'section999' in fragment

    def test_classify_fragment_with_massive_input(self):
        """classify_fragment should handle massive fragments."""
        massive_fragment = "A" * 10000
        classification = classify_fragment(massive_fragment)

        # Should return a valid classification
        assert classification in ['anchor', 'route', 'other']


# =============================================================================
# TIER 2: Real-World Attacks - Special Characters
# =============================================================================

class TestSpecialCharacters:
    """Test URLs with null bytes, control characters, and special chars."""

    def test_null_byte_in_path(self):
        """Null byte in path should not crash."""
        url = "https://example.com/\x00/page"
        components = parse_url_components(url)

        assert components is not None

    def test_control_characters(self):
        """Control characters should not crash."""
        url = "https://example.com/page\x01\x02\x03"
        depth = get_path_depth(url)

        assert depth >= 0

    def test_spaces_in_path(self):
        """Spaces in path should parse."""
        url = "https://example.com/path with spaces"
        segments = extract_path_segments(url)

        assert len(segments) == 1
        assert 'space' in segments[0]

    def test_pipes_in_path(self):
        """Pipe characters should parse."""
        url = "https://example.com/path|with|pipes"
        components = parse_url_components(url)

        assert components is not None

    def test_brackets_in_path(self):
        """< > brackets should parse."""
        url = "https://example.com/path<with>brackets"
        depth = get_path_depth(url)

        assert depth >= 0


# =============================================================================
# TIER 3: Edge Cases - Empty and Invalid Inputs
# =============================================================================

class TestEdgeCases:
    """Test edge cases like empty strings, invalid ports, etc."""

    def test_empty_string(self):
        """Empty string should not crash."""
        url = ""
        components = parse_url_components(url)

        # Should return default/empty components
        assert components is not None
        assert components['scheme'] == ''

    def test_just_protocol(self):
        """Just 'https://' should not crash."""
        url = "https://"
        depth = get_path_depth(url)

        assert depth == 0

    def test_triple_slash_path(self):
        """https:///path (triple slash) should parse."""
        url = "https:///path"
        components = parse_url_components(url)

        assert components is not None

    def test_double_slash_in_path(self):
        """Double slashes in path should parse."""
        url = "https://example.com//double//slash"
        segments = extract_path_segments(url)

        # Empty segments are filtered out
        assert isinstance(segments, list)

    def test_only_fragment(self):
        """Just '#fragment' should not crash."""
        url = "#fragment"
        components = parse_url_components(url)

        assert components is not None

    def test_slash_fragment(self):
        """'/#fragment' should parse."""
        url = "/#fragment"
        fragment = extract_fragment(url)

        assert fragment == 'fragment'

    def test_invalid_port_99999(self):
        """Invalid port 99999 should parse (validation is separate)."""
        url = "https://example.com:99999/page"
        components = parse_url_components(url)

        assert components['port'] == 99999

    def test_port_zero(self):
        """Port 0 should parse."""
        url = "https://example.com:0/page"
        components = parse_url_components(url)

        assert components['port'] == 0

    def test_credentials_in_url(self):
        """Username:password in URL should parse."""
        url = "https://user:pass@example.com/page"
        components = parse_url_components(url)

        assert components['username'] == 'user'
        assert components['password'] == 'pass'
        assert components['has_auth'] is True

    def test_credentials_with_port(self):
        """Username:password with port should parse."""
        url = "https://user:pass@example.com:8080/page"
        components = parse_url_components(url)

        assert components['username'] == 'user'
        assert components['port'] == 8080


# =============================================================================
# TIER 3: Function Integration Tests
# =============================================================================

class TestFunctionIntegration:
    """Test interactions between multiple url_utilities functions."""

    def test_is_same_domain_with_ports(self):
        """is_same_domain should handle ports correctly."""
        url1 = "https://example.com:8080/page"
        url2 = "https://example.com:9090/other"

        # Same domain, different ports - should still be same domain
        assert is_same_domain(url1, url2)

    def test_is_internal_link_with_subdomains(self):
        """is_internal_link should handle subdomains."""
        source = "https://www.example.com/page"
        target1 = "https://www.example.com/other"
        target2 = "https://api.example.com/endpoint"

        assert is_internal_link(source, target1)  # Same subdomain
        assert not is_internal_link(source, target2)  # Different subdomain

    def test_resolve_link_with_pathological_source(self):
        """resolve_link should work with pathological source URLs."""
        source = "https://example.com/" + "/".join([f"level{i}" for i in range(50)])
        link = "../page"

        resolved = resolve_link(link, source)

        assert resolved is not None
        assert resolved.startswith('https://example.com')

    def test_count_fragments_with_mixed_urls(self, sample_urls_normal, sample_urls_pathological):
        """count_fragments should handle mix of normal and pathological URLs."""
        urls = sample_urls_normal + [sample_urls_pathological['fragment_bombs'][0]]

        result = count_fragments(urls)

        assert result['total_urls'] > 0
        assert result['urls_with_fragments'] >= 0
        assert result['fragment_percentage'] >= 0

    def test_get_depth_distribution_with_extreme_depths(self):
        """get_depth_distribution should handle extreme depth variance."""
        urls = [
            "https://example.com/a",  # depth 1
            "https://example.com/a/b",  # depth 2
            "https://example.com/" + "/".join([f"l{i}" for i in range(100)])  # depth 100
        ]

        dist = get_depth_distribution(urls)

        assert dist['min'] == 1
        assert dist['max'] == 100
        assert dist['average'] > 1

    def test_extract_file_extension_path_traversal(self):
        """extract_file_extension should not be fooled by path traversal."""
        url = "https://example.com/../../../../etc/passwd.txt"
        ext = extract_file_extension(url)

        assert ext == 'txt'

    def test_extract_file_extension_multiple_dots(self):
        """extract_file_extension should handle multiple dots."""
        url = "https://example.com/file.tar.gz"
        ext = extract_file_extension(url)

        # Should return last extension
        assert ext == 'gz'


# =============================================================================
# TIER 3: Stress Testing - Batch Operations
# =============================================================================

class TestStressBatch:
    """Stress test with large batches of pathological URLs."""

    def test_batch_1000_extreme_depth_urls(self):
        """Process 1000 URLs with extreme depth."""
        urls = [
            "https://example.com/" + "/".join([f"l{i}" for i in range(50)])
            for _ in range(1000)
        ]

        # Should complete without crashing
        depths = [get_path_depth(url) for url in urls]

        assert len(depths) == 1000
        assert all(d == 50 for d in depths)

    def test_batch_mixed_pathological_urls(self, sample_urls_pathological):
        """Process mixed pathological URLs in batch."""
        all_pathological = []
        for category in sample_urls_pathological.values():
            if isinstance(category, list):
                all_pathological.extend(category)

        # Process all without crashing
        results = []
        for url in all_pathological:
            try:
                components = parse_url_components(url)
                results.append(components)
            except Exception as e:
                pytest.fail(f"Failed to parse {url}: {e}")

        assert len(results) > 0


# =============================================================================
# TIER 3: Regression Tests - Known Bugs
# =============================================================================

class TestKnownBugs:
    """Tests for known bugs and edge cases from production."""

    def test_query_param_count_with_ampersand_in_value(self):
        """Query param with & in value should count correctly."""
        # If a parameter value contains &, it might be miscounted
        url = "https://example.com/page?q=a%26b&other=value"
        count = get_query_param_count(url)

        # Should count 2 params, not 3
        assert count == 2

    def test_fragment_route_classification(self):
        """Fragment that looks like route should be classified correctly."""
        fragments = [
            "/app/dashboard",  # route
            "#/app/dashboard",  # route
            "section-1",  # anchor
            "top",  # anchor
        ]

        classifications = [classify_fragment(f) for f in fragments]

        assert classifications[0] == 'route'
        assert classifications[1] == 'route'
        assert classifications[2] == 'anchor'
        assert classifications[3] == 'anchor'

    def test_resolve_link_fragment_only(self):
        """resolve_link with fragment-only should return None."""
        source = "https://example.com/page"
        link = "#section"

        resolved = resolve_link(link, source)

        # Fragment-only links should be filtered out (line 151 in url_utilities)
        assert resolved is None

    def test_resolve_link_protocol_relative(self):
        """Protocol-relative URL should resolve to https."""
        source = "https://example.com/page"
        link = "//cdn.example.com/resource"

        resolved = resolve_link(link, source)

        assert resolved == "https://cdn.example.com/resource"
