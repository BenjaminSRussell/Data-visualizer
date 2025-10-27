# URL Analysis System - Complete Documentation

## 🎯 Overview

A comprehensive URL analysis system that performs deep statistical, semantic, network, and pathway analysis on website crawl data. Built with multiple parallel analyzers to extract maximum insights from JSONL sitemap data.

## 📊 Analysis Results Summary (Site.jsonl - 6,163 URLs)

### Overall Scores
- **URL Health**: 66.5/100 (Grade: D)
- **URL Quality**: 79.7/100 (Grade: C+)
- **Overall Score**: 73.1/100

### Key Findings
1. **Site Type**: Educational institution (hartford.edu)
2. **Architecture**: DEEP (7 levels max)
3. **Dominant Category**: Educational (46% of pages)
4. **Average Depth**: 3.24 levels
5. **Network Density**: 0.006560 (relatively sparse)

### Major Issues Detected
- 🔴 **51.1% dead-end pages** (3,152 pages with no outbound links)
- 🔴 **405 disconnected components** (site not fully connected)
- 🟡 349 depth outliers
- 🟡 241 path length outliers
- 🟡 High number of self-links (10,194)

## 🔧 System Architecture

### Analysis Modules

```
analysis/
├── analyzers/
│   ├── statistical_analyzer.py       # Statistical metrics & distributions
│   ├── network_analyzer.py           # Graph theory & network metrics
│   └── semantic_path_analyzer.py     # Semantic understanding & NLP
├── mappers/
│   └── pathway_mapper.py             # Navigation flows & site architecture
└── pipeline/
    └── master_pipeline.py            # Orchestration & report generation
```

### 1. Statistical Analyzer

**Purpose**: Extract statistical insights and identify patterns

**Features**:
- Summary statistics (mean, median, std dev, quartiles)
- Distribution analysis (depth, path length, links)
- Correlation analysis (Pearson correlation)
- Anomaly detection (IQR method, z-scores)
- URL health scoring
- Temporal pattern analysis

**Key Metrics**:
```
Depth: 3.24 ± 1.05 (range: 0-7)
Path Length: 64.37 ± 33.47 chars
Avg Links per Page: 112.26
URL Health Score: 66.5/100
```

**Correlations Found**:
- Depth ↔ Link Count: weak negative (r=-0.184, p<0.001)
- Depth ↔ Path Length: weak negative (r=-0.145, p<0.001)

### 2. Network Analyzer

**Purpose**: Analyze URL relationships as a directed graph

**Features**:
- Network metrics (density, degree, reciprocity)
- Centrality analysis (degree, in-degree, out-degree, betweenness)
- Clustering coefficient
- Community detection
- Authority/Hub scoring (HITS algorithm)
- Link pattern analysis
- Bottleneck detection

**Key Metrics**:
```
Nodes: 6,163
Edges: 249,107
Density: 0.006560
Average Degree: 36.24
Reciprocity: 0.0200
Global Clustering: varies by community
```

**Most Central Pages**:
1. `/programs-of-study/default.aspx` (3,290 connections)
2. `/default.aspx` (3,251 connections)
3. `/news/default.aspx` (3,192 connections)

**Communities Detected**: 34 total
- Largest: `academics` (27.2%)
- Others: `directory`, `unotes`, `success-stories`, `news`

### 3. Semantic Path Analyzer

**Purpose**: Extract semantic meaning from URL structures

**Features**:
- Vocabulary analysis & token extraction
- N-gram analysis (bigrams, trigrams)
- Semantic categorization (educational, commerce, content, etc.)
- Action verb detection (CRUD operations)
- Template extraction & pattern recognition
- Content type prediction
- SEO quality assessment
- Parameter analysis

**Key Metrics**:
```
Total Tokens: 41,755
Unique Tokens: 3,706
Vocabulary Diversity: LOW (TTR)
URL Quality Score: 79.7/100
```

**Top Keywords**:
1. academics (2,842 occurrences)
2. schools (1,257)
3. colleges (1,256)
4. directory (1,083)
5. unotes (964)

**Content Categories**:
- Educational: 46.0%
- Information: 9.1%
- Content: 8.2%
- Administrative: 3.9%

### 4. Pathway Mapper

**Purpose**: Map navigation flows and site architecture

**Features**:
- Architecture classification (flat/deep/wide/balanced)
- Entry point identification
- Navigation hub detection
- Dead-end page analysis
- Common pathway extraction
- Depth flow analysis
- Connectivity analysis (BFS for components)
- Breadcrumb hierarchy assessment
- Page importance scoring

**Key Metrics**:
```
Architecture Type: DEEP
Max Depth: 7 levels
Avg Children per Parent: 3.39
Orphan Pages: 0
Dead-End Pages: 3,152 (51.1%)
```

**Entry Points**: 1,495 total
- Top entry: `/unotes/campus-news.aspx` (144 children)

**Navigation Hubs**: 590 total
- Top hub: `/default.aspx` (1,492 connections)

## 🚀 Usage

### Running the Full Analysis

```bash
# Navigate to project directory
cd "/Users/benjaminrussell/Desktop/Data visualizer"

# Run master pipeline
python3 analysis/pipeline/master_pipeline.py Site.jsonl analysis/results

# View insights
python3 analysis/view_insights.py analysis/results
```

### Output Files

After running the pipeline, you'll get:

```
analysis/results/
├── analysis_results.json           # Complete combined results
├── statistical_results.json        # Statistical analysis data
├── network_results.json           # Network analysis data
├── semantic_path_results.json     # Semantic analysis data
├── pathway_results.json           # Pathway analysis data
└── analysis_report.txt            # Human-readable summary
```

### Command Line Options

```bash
# Basic usage
python3 analysis/pipeline/master_pipeline.py <input.jsonl> <output_dir>

# Example
python3 analysis/pipeline/master_pipeline.py Site.jsonl my_analysis

# View results
python3 analysis/view_insights.py my_analysis
```

## 📈 Performance

**Processing Speed** (6,163 URLs):
- Statistical Analysis: 2.34s
- Semantic Analysis: 0.88s
- Pathway Mapping: 4.91s
- Network Analysis: 10.71s
- **Total**: 10.72s (parallel execution)

**Scalability**:
- Handles 6,000+ URLs efficiently
- Parallel execution of all 4 analyzers
- Memory efficient (streaming JSONL)

## 🎨 Key Insights for hartford.edu

### Strengths ✅
1. **Zero orphan pages** - all pages connected to tree
2. **Strong educational categorization** - clear content focus
3. **Good URL quality** (79.7/100) - readable, well-structured URLs
4. **Deep architecture** - supports complex content hierarchy

### Issues ⚠️
1. **High dead-end rate (51.1%)** - many pages lack navigation links
2. **Low network density** - pages poorly interconnected
3. **Fragmented site** - 405 disconnected components
4. **Fragment overuse** - 59.3% of URLs have fragments (affects SEO)

### Recommendations 💡
1. **Add internal links**: Reduce dead-end pages by adding related content links
2. **Improve navigation**: Add breadcrumbs and contextual navigation to deep pages
3. **Consolidate fragments**: Many fragment links could be separate pages
4. **Connect components**: Link the 405 disconnected sections together
5. **Optimize hub pages**: Leverage high-authority pages for better linking

## 🔬 Analysis Methodology

### Statistical Analysis
- **Descriptive Statistics**: NumPy/SciPy for calculations
- **Normality Testing**: Shapiro-Wilk test
- **Correlation**: Pearson correlation coefficient
- **Outlier Detection**: IQR method (1.5 × IQR)

### Network Analysis
- **Graph Structure**: Directed graph (adjacency list)
- **Centrality**: Degree, in-degree, out-degree
- **Community Detection**: Path-based clustering
- **HITS Algorithm**: Authority/Hub scores (1 iteration)

### Semantic Analysis
- **Tokenization**: Multi-method (split on `/`, `-`, `_`, `.`)
- **Stop Words**: Custom list for URLs
- **N-grams**: Sliding window (bigrams, trigrams)
- **Categorization**: Pattern matching with keyword dictionaries

### Pathway Analysis
- **Architecture**: Rule-based classification
- **Components**: BFS traversal
- **Importance**: Multi-factor scoring (depth, links, children)

## 📊 Data Format

### Input (JSONL)
```json
{
  "url": "https://example.com/page",
  "depth": 3,
  "parent_url": "https://example.com/parent",
  "discovered_at": 1761322549,
  "status_code": 200,
  "content_type": "text/html; charset=utf-8",
  "title": "Page Title",
  "links": ["link1", "link2", ...]
}
```

### Output (JSON)
Structured results with:
- Metadata (timestamp, execution time)
- Individual analyzer results
- Combined insights
- Alerts & recommendations

## 🔮 Future Enhancements

### Potential Additions
1. **Machine Learning Classification**: Use zero-shot or fine-tuned models
2. **Temporal Analysis**: Track changes over time with multiple crawls
3. **Comparative Analysis**: Before/after comparisons
4. **Interactive Dashboard**: React-based visualization
5. **SEO Scoring**: Comprehensive SEO audit
6. **Accessibility Analysis**: WCAG compliance checking
7. **Performance Metrics**: Page speed, Core Web Vitals correlation

### Visualization Ideas
1. Hierarchical tree map (D3.js)
2. Sunburst diagram (pathway visualization)
3. Network graph (force-directed layout)
4. Sankey diagram (user flow)
5. Heatmaps (depth × content type)

## 🛠️ Dependencies

```
numpy>=1.20.0
scipy>=1.7.0
```

All other modules use Python standard library.

## 📝 Notes

- **Memory Usage**: ~500MB for 6K URLs
- **Thread Safety**: All analyzers are thread-safe
- **Error Handling**: Graceful degradation on parse errors
- **URL Normalization**: Handles relative/absolute URLs, fragments, parameters

## 🏆 Analysis Completeness

- ✅ Statistical Analysis
- ✅ Network Analysis
- ✅ Semantic Analysis
- ✅ Pathway Analysis
- ✅ Master Pipeline
- ✅ Automated Insights
- ✅ Report Generation
- ✅ Insights Viewer

## 📞 Support

For questions or issues, refer to the individual analyzer source code - each module is well-documented with docstrings and comments.

---

**Last Updated**: 2025-10-27
**Analysis Version**: 1.0
**Dataset**: Site.jsonl (hartford.edu, 6,163 URLs)
