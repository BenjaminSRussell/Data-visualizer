"""
Shared test fixtures and configuration for all tests.

This module provides reusable test fixtures including:
- Database setup and teardown
- Sample URL datasets (normal, pathological, semantic groups)
- Test utilities and helpers
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Conditionally import database models (only if SQLAlchemy available and working)
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from analysis.database.models import Base
    SQLALCHEMY_AVAILABLE = True
except (ImportError, Exception) as e:
    SQLALCHEMY_AVAILABLE = False
    Base = None
    print(f"Warning: SQLAlchemy models not available: {e}")


@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create in-memory SQLite database for testing.
    Scope: session (created once per test session)
    """
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not available")

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """
    Create a fresh database session for each test.
    Scope: function (new session per test, ensures isolation)
    """
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not available")

    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_urls_normal():
    """Normal, well-formed URLs for baseline testing."""
    return [
        "https://example.com/",
        "https://example.com/about",
        "https://example.com/products",
        "https://example.com/blog/2023/post-1",
        "https://example.com/blog/2023/post-2",
        "https://example.com/blog/2024/post-1",
        "https://example.com/products/category/electronics",
        "https://example.com/products/category/books",
        "https://www.subdomain.example.com/page",
        "https://example.com/user/profile?id=123",
        "https://example.com/search?q=test&page=1",
        "https://example.com/page#section",
    ]


@pytest.fixture
def sample_urls_pathological():
    """
    Pathological URLs that stress-test parsers.

    Categories:
    - Extreme depth (50+ levels)
    - Extreme length (1000+ characters)
    - Malformed encoding
    - Recursive parameters
    - Path traversal attempts
    - Protocol confusion
    - Null bytes and control characters
    """
    return {
        'extreme_depth': [
            # 50 levels deep
            "https://example.com/" + "/".join([f"level{i}" for i in range(50)]),
            # 100 levels deep
            "https://example.com/" + "/".join([f"l{i}" for i in range(100)]),
        ],
        'extreme_length': [
            # 1000 character path
            "https://example.com/" + "a" * 1000,
            # 10,000 character path
            "https://example.com/path/" + "x" * 10000,
            # Very long query string
            "https://example.com/page?" + "&".join([f"param{i}=value{i}" for i in range(500)]),
        ],
        'malformed_encoding': [
            # Invalid percent encoding
            "https://example.com/%XX%YY/path",
            "https://example.com/%ZZ/page",
            "https://example.com/path%",  # Incomplete encoding
            # Double encoding
            "https://example.com/%2525/path",  # %25 = %, so %2525 = %25
        ],
        'recursive_params': [
            # Recursive query parameters (infinite redirect potential)
            "https://example.com/page?next=/page?next=/page",
            "https://example.com/redirect?url=https://example.com/redirect?url=https://example.com",
        ],
        'path_traversal': [
            # Path traversal attempts
            "https://example.com/../../../../etc/passwd",
            "https://example.com/..%2F..%2F..%2Fetc%2Fpasswd",  # URL-encoded
            "https://example.com/./././page",
            "https://example.com/dir/../../../etc/passwd",
        ],
        'mixed_encoding': [
            # UTF-8, Latin-1, emojis, special unicode
            "https://example.com/café/page",
            "https://example.com/日本語/ページ",
            "https://example.com/emoji/😀/page",
            "https://example.com/𝕌𝕟𝕚𝕔𝕠𝕕𝕖/page",  # Math alphanumeric symbols
            "https://example.com/Ωμέγα/page",  # Greek
        ],
        'protocol_confusion': [
            # Non-HTTP protocols (should be rejected or handled specially)
            "javascript:alert(1)//https://example.com",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd",
            "ftp://example.com/file",
        ],
        'punycode_domains': [
            # Internationalized domain names
            "https://xn--bcher-kva.example/page",  # bücher.example
            "https://xn--e1afmkfd.xn--p1ai/page",  # пример.рф
            "https://xn--bcher-kva.example/page#fragment",
        ],
        'fragment_bombs': [
            # Massive fragments
            "https://example.com#" + "A" * 10000,
            "https://example.com/page#" + "/".join([f"section{i}" for i in range(1000)]),
        ],
        'special_characters': [
            # Null bytes and control characters
            "https://example.com/\x00/page",
            "https://example.com/page\x01\x02\x03",
            # Spaces and special chars
            "https://example.com/path with spaces",
            "https://example.com/path|with|pipes",
            "https://example.com/path<with>brackets",
        ],
        'edge_cases': [
            # Empty components
            "",
            "https://",
            "https:///path",
            "https://example.com//double//slash",
            # Only fragment
            "#fragment",
            "/#fragment",
            # Port edge cases
            "https://example.com:99999/page",  # Invalid port
            "https://example.com:0/page",
            # Credentials in URL
            "https://user:pass@example.com/page",
            "https://user:pass@example.com:8080/page",
        ]
    }


@pytest.fixture
def sample_urls_semantic_groups():
    """
    URLs organized by semantic categories for consistency testing.

    Tests that semantically similar URLs cluster together and
    that tracking parameters don't affect semantic categorization.
    """
    return {
        'blog_posts': [
            "https://example.com/blog/2023/post-1",
            "https://example.com/blog/2023/post-2",
            "https://example.com/blog/2024/article-1",
            "https://example.com/articles/2023/story-1",
            "https://example.com/posts/2024/news-1",
        ],
        'user_management': [
            "https://example.com/user/profile",
            "https://example.com/account/settings",
            "https://example.com/member/info",
            "https://example.com/usr/dashboard",
        ],
        'product_pages': [
            "https://example.com/products/item-1",
            "https://example.com/shop/product/item-2",
            "https://example.com/store/items/item-3",
        ],
        'tracking_variants': {
            'base': "https://example.com/blog/post",
            'variants': [
                "https://example.com/blog/post?utm_source=google&utm_medium=cpc",
                "https://example.com/blog/post?fbclid=abc123&ref=twitter",
                "https://example.com/blog/post?gclid=xyz789&campaign=summer",
                "https://example.com/blog/post?ref=email&track=newsletter",
            ]
        },
        'abbreviation_variants': [
            "https://example.com/dept/sales",
            "https://example.com/department/sales",
            "https://example.com/dpt/sales",
        ],
        'multilingual': [
            "https://example.com/blog/article",
            "https://example.com/blog/artikel",  # German
            "https://example.com/blog/articulo",  # Spanish
        ]
    }


@pytest.fixture
def sample_graph_data_simple():
    """
    Simple graph for testing basic graph operations.

    Structure:
        A → B → C
        ↓       ↑
        D ------→

    Properties:
    - 4 nodes, 4 edges
    - 1 cycle (A→D→C, C connects to A via B)
    - A is hub (out-degree=2), C is authority (in-degree=2)
    """
    return [
        {
            'url': 'https://example.com/A',
            'depth': 0,
            'links': ['https://example.com/B', 'https://example.com/D']
        },
        {
            'url': 'https://example.com/B',
            'depth': 1,
            'links': ['https://example.com/C']
        },
        {
            'url': 'https://example.com/C',
            'depth': 2,
            'links': []
        },
        {
            'url': 'https://example.com/D',
            'depth': 1,
            'links': ['https://example.com/C']
        }
    ]


@pytest.fixture
def sample_graph_data_complex():
    """
    Complex graph for testing advanced graph operations.

    Structure:
    - 20 nodes organized in 3 communities
    - Community 1: /blog/* (8 nodes)
    - Community 2: /products/* (7 nodes)
    - Community 3: /about/* (5 nodes)
    - Cross-community links
    - Bidirectional links
    - Orphan nodes (no incoming links)
    """
    urls = []

    # Community 1: Blog
    blog_urls = [f'https://example.com/blog/post-{i}' for i in range(1, 9)]
    for i, url in enumerate(blog_urls):
        links = []
        # Link to next post in sequence
        if i < len(blog_urls) - 1:
            links.append(blog_urls[i + 1])
        # Link to homepage
        links.append('https://example.com/')
        # Some posts link to products
        if i % 3 == 0:
            links.append(f'https://example.com/products/item-{i}')

        urls.append({
            'url': url,
            'depth': 2,
            'links': links
        })

    # Community 2: Products
    product_urls = [f'https://example.com/products/item-{i}' for i in range(1, 8)]
    for i, url in enumerate(product_urls):
        links = []
        # Link to category page
        links.append('https://example.com/products')
        # Link to related products
        if i < len(product_urls) - 1:
            links.append(product_urls[i + 1])

        urls.append({
            'url': url,
            'depth': 2,
            'links': links
        })

    # Community 3: About pages
    about_urls = [
        'https://example.com/about',
        'https://example.com/about/team',
        'https://example.com/about/contact',
        'https://example.com/about/history',
        'https://example.com/about/careers'
    ]
    for i, url in enumerate(about_urls):
        links = ['https://example.com/']
        # Internal about links
        if i > 0:
            links.append(about_urls[0])  # All link back to main about page

        urls.append({
            'url': url,
            'depth': 1 if i == 0 else 2,
            'links': links
        })

    # Add homepage
    urls.append({
        'url': 'https://example.com/',
        'depth': 0,
        'links': [
            'https://example.com/blog/post-1',
            'https://example.com/products',
            'https://example.com/about'
        ]
    })

    # Add products category page
    urls.append({
        'url': 'https://example.com/products',
        'depth': 1,
        'links': product_urls[:3]
    })

    return urls


@pytest.fixture
def sample_graph_data_with_known_metrics():
    """
    Graph with known, hand-calculated metrics for validation.

    Structure:
        A ←→ B (bidirectional)
        ↓     ↓
        C ←→ D (bidirectional)

    Properties:
    - 4 nodes, 6 edges (3 bidirectional pairs)
    - Reciprocity: 1.0 (100% of edges are reciprocated)
    - Density: 6 / (4 * 3) = 0.5
    - All nodes have degree 3
    - Average clustering coefficient: 0.5
    """
    return [
        {
            'url': 'https://example.com/A',
            'depth': 0,
            'links': ['https://example.com/B', 'https://example.com/C']
        },
        {
            'url': 'https://example.com/B',
            'depth': 0,
            'links': ['https://example.com/A', 'https://example.com/D']
        },
        {
            'url': 'https://example.com/C',
            'depth': 1,
            'links': ['https://example.com/A', 'https://example.com/D']
        },
        {
            'url': 'https://example.com/D',
            'depth': 1,
            'links': ['https://example.com/B', 'https://example.com/C']
        }
    ]


# Test utilities

def create_url_list(count, pattern="https://example.com/page-{}"):
    """Helper: Generate list of URLs."""
    return [pattern.format(i) for i in range(count)]


def create_jsonl_data(urls, include_links=True):
    """Helper: Convert URL list to JSONL-style data."""
    data = []
    for i, url in enumerate(urls):
        item = {
            'url': url,
            'depth': i % 5,  # Vary depth
            'links': [] if not include_links else [urls[(i + 1) % len(urls)]]
        }
        data.append(item)
    return data
