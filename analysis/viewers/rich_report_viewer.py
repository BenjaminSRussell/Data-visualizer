"""
Rich Terminal Report Viewer - Beautiful, colorful, interactive reports
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box
from rich.syntax import Syntax
from rich.markdown import Markdown
import plotext as plt
from typing import Dict, List
import json


class RichReportViewer:
    """Create beautiful terminal reports using Rich library"""

    def __init__(self):
        self.console = Console()

    def show_header(self, title: str, subtitle: str = None):
        """Show formatted header"""
        text = Text()
        text.append(title, style="bold magenta")
        if subtitle:
            text.append(f"\n{subtitle}", style="dim")

        panel = Panel(text, box=box.DOUBLE, border_style="bright_blue")
        self.console.print(panel)

    def show_summary_stats(self, stats: Dict):
        """Show summary statistics in a beautiful table"""
        table = Table(title="Analysis Summary", box=box.ROUNDED, border_style="cyan")

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        table.add_column("Status", justify="center")

        for key, value in stats.items():
            # format value for display
            if isinstance(value, float):
                value_str = f"{value:.2f}"
            elif isinstance(value, int):
                value_str = f"{value:,}"
            else:
                value_str = str(value)

            # add status indicator
            if isinstance(value, (int, float)) and value > 0:
                status = "✓"
            else:
                status = "○"

            table.add_row(
                key.replace('_', ' ').title(),
                value_str,
                status
            )

        self.console.print(table)

    def show_scores(self, scores: Dict):
        """Show scores with color-coded bars"""
        self.console.print("\n[bold cyan]Quality Scores[/bold cyan]")

        for name, score in scores.items():
            # choose color based on score
            if score >= 80:
                color = "green"
                grade = "A"
            elif score >= 70:
                color = "yellow"
                grade = "B"
            elif score >= 60:
                color = "orange1"
                grade = "C"
            else:
                color = "red"
                grade = "D"

            # build progress bar
            bar_length = int(score / 2)  # scale to 50 chars
            bar = "█" * bar_length + "░" * (50 - bar_length)

            self.console.print(
                f"  [{color}]{name.replace('_', ' ').title():25s}[/{color}] "
                f"[{color}]{bar}[/{color}] "
                f"[bold {color}]{score:.1f}[/bold {color}] "
                f"[dim]({grade})[/dim]"
            )

    def show_alerts(self, alerts: List[str]):
        """Show alerts in a highlighted panel"""
        if not alerts:
            return

        alert_text = Text()
        for i, alert in enumerate(alerts, 1):
            alert_text.append(f"{i}. ", style="bold red")
            alert_text.append(f"{alert}\n", style="yellow")

        panel = Panel(
            alert_text,
            title="⚠️  Alerts",
            border_style="red",
            box=box.ROUNDED
        )
        self.console.print(panel)

    def show_recommendations(self, recommendations: List[str]):
        """Show recommendations"""
        if not recommendations:
            return

        rec_text = Text()
        for i, rec in enumerate(recommendations, 1):
            rec_text.append(f"→ ", style="bold green")
            rec_text.append(f"{rec}\n", style="white")

        panel = Panel(
            rec_text,
            title="💡 Recommendations",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)

    def show_batch_analysis(self, batches: List[Dict]):
        """Show batch analysis results"""
        table = Table(
            title="URL Batches Detected",
            box=box.ROUNDED,
            border_style="magenta"
        )

        table.add_column("Batch Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("URLs", justify="right", style="green")
        table.add_column("Pattern", style="dim")

        # sort batches by url count
        sorted_batches = sorted(batches, key=lambda x: x.get('total_urls', 0), reverse=True)

        for batch in sorted_batches[:20]:  # show top 20 batches
            table.add_row(
                batch.get('batch_name', 'Unknown'),
                batch.get('batch_type', 'Unknown'),
                f"{batch.get('total_urls', 0):,}",
                batch.get('pattern', '')[:40] + "..." if len(batch.get('pattern', '')) > 40 else batch.get('pattern', '')
            )

        self.console.print(table)

    def show_batch_tree(self, batches: List[Dict]):
        """Show batches as a tree structure"""
        tree = Tree("URL Batch Hierarchy")

        # group batches by type
        by_type = {}
        for batch in batches:
            batch_type = batch.get('batch_type', 'unknown')
            if batch_type not in by_type:
                by_type[batch_type] = []
            by_type[batch_type].append(batch)

        for batch_type, type_batches in by_type.items():
            type_branch = tree.add(f"[yellow]{batch_type}[/yellow] ({len(type_batches)} batches)")

            # list top batches
            for batch in sorted(type_batches, key=lambda x: x.get('total_urls', 0), reverse=True)[:5]:
                type_branch.add(
                    f"[green]{batch.get('batch_name', 'Unknown')}[/green] - "
                    f"[cyan]{batch.get('total_urls', 0):,} URLs[/cyan]"
                )

        self.console.print(tree)

    def show_url_distribution(self, distribution: Dict):
        """Show URL distribution as ASCII chart"""
        self.console.print("\n[bold cyan]URL Distribution[/bold cyan]\n")

        # use plotext for terminal plotting
        labels = list(distribution.keys())
        values = list(distribution.values())

        # convert labels to strings
        labels_str = [str(l) for l in labels]

        plt.clf()
        plt.bar(labels_str, values, color="cyan")
        plt.title("URL Distribution by Depth")
        plt.xlabel("Depth")
        plt.ylabel("Count")
        plt.theme("dark")
        plt.plotsize(60, 15)
        plt.show()
        print()  # add spacing

    def show_network_metrics(self, metrics: Dict):
        """Show network analysis metrics"""
        table = Table(
            title="Network Metrics",
            box=box.SIMPLE,
            border_style="blue"
        )

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta", justify="right")

        metrics_formatted = {
            'Nodes': f"{metrics.get('nodes', 0):,}",
            'Edges': f"{metrics.get('edges', 0):,}",
            'Density': f"{metrics.get('density', 0):.6f}",
            'Avg Degree': f"{metrics.get('average_degree', 0):.2f}",
            'Max In-Degree': f"{metrics.get('max_in_degree', 0):,}",
            'Max Out-Degree': f"{metrics.get('max_out_degree', 0):,}",
        }

        for metric, value in metrics_formatted.items():
            table.add_row(metric, value)

        self.console.print(table)

    def show_top_urls(self, urls: List[Dict], title: str, limit=10):
        """Show top URLs table"""
        table = Table(title=title, box=box.ROUNDED, border_style="green")

        table.add_column("#", style="dim", width=3)
        table.add_column("URL", style="cyan")
        table.add_column("Metric", justify="right", style="magenta")

        for i, url_data in enumerate(urls[:limit], 1):
            # capture the relevant metric value
            metric_value = None
            for key in ['degree', 'in_degree', 'out_degree', 'score']:
                if key in url_data:
                    metric_value = url_data[key]
                    break

            # truncate url if overly long
            url = url_data.get('url', 'Unknown')
            if len(url) > 60:
                url = url[:57] + "..."

            table.add_row(
                str(i),
                url,
                f"{metric_value:,}" if metric_value is not None else "N/A"
            )

        self.console.print(table)

    def show_progress(self, tasks: List[str]):
        """Show progress for multiple tasks"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=self.console
        ) as progress:

            for task_desc in tasks:
                task = progress.add_task(task_desc, total=100)
                # simulate progress while awaiting real updates
                progress.update(task, completed=100)

    def show_full_report(self, results: Dict):
        """Show complete analysis report"""
        self.console.clear()

        # render header section
        metadata = results.get('metadata', {})
        self.show_header(
            "Comprehensive URL Analysis Report",
            f"Analysis of {metadata.get('total_urls', 0):,} URLs"
        )

        # render summary statistics
        if 'insights' in results:
            insights = results['insights']

            # render score section
            if 'scores' in insights and insights['scores']:
                self.console.print()
                self.show_scores(insights['scores'])

            # build summary stats payload
            summary_stats = {
                'Total URLs': metadata.get('total_urls', 0),
                'Analysis Time': f"{metadata.get('total_execution_time', 0):.2f}s",
                'Modules Run': len([k for k in results.keys() if k not in ['metadata', 'insights']]),
            }
            self.console.print()
            self.show_summary_stats(summary_stats)

            # display alerts
            if insights.get('alerts'):
                self.console.print()
                self.show_alerts(insights['alerts'])

            # display recommendations
            if insights.get('recommendations'):
                self.console.print()
                self.show_recommendations(insights['recommendations'])

        # display network metrics
        if 'network' in results and 'network_metrics' in results['network']:
            self.console.print()
            self.show_network_metrics(results['network']['network_metrics'])

        # display top url tables
        if 'network' in results and 'centrality' in results['network']:
            centrality = results['network']['centrality']
            if 'top_by_degree' in centrality:
                self.console.print()
                self.show_top_urls(
                    centrality['top_by_degree'],
                    "Top URLs by Degree Centrality"
                )

        # render distribution chart
        if 'statistical' in results and 'distributions' in results['statistical']:
            dist = results['statistical']['distributions'].get('depth_distribution', {})
            if dist:
                self.show_url_distribution(dist)

        # show closing message
        self.console.print()
        self.console.print(
            Panel(
                "[green]✓ Analysis Complete![/green]\n"
                "[dim]Results saved to output directory[/dim]",
                border_style="green"
            )
        )


def main():
    """Demo the rich report viewer"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python rich_report_viewer.py <results.json>")
        sys.exit(1)

    # load results from file
    with open(sys.argv[1], 'r') as f:
        results = json.load(f)

    # create viewer and render report
    viewer = RichReportViewer()
    viewer.show_full_report(results)


if __name__ == '__main__':
    main()
