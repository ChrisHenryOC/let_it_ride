"""Integration tests for HTML report generation functionality.

Tests file creation, content validation, chart generation, template rendering,
responsive design elements, and various configuration options.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from let_it_ride.analytics.export_html import (
    HTMLExporter,
    HTMLReportConfig,
    HTMLReportGenerator,
    generate_html_report,
)
from let_it_ride.analytics.statistics import calculate_statistics_from_results
from let_it_ride.simulation.session import SessionOutcome, SessionResult, StopReason


@pytest.fixture
def sample_session_results() -> list[SessionResult]:
    """Create sample session results for testing.

    Includes all four stop reasons: WIN_LIMIT, LOSS_LIMIT, MAX_HANDS, INSUFFICIENT_FUNDS.
    """
    return [
        SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.WIN_LIMIT,
            hands_played=25,
            starting_bankroll=500.0,
            final_bankroll=600.0,
            session_profit=100.0,
            total_wagered=750.0,
            total_bonus_wagered=0.0,
            peak_bankroll=620.0,
            max_drawdown=50.0,
            max_drawdown_pct=0.08,
        ),
        SessionResult(
            outcome=SessionOutcome.LOSS,
            stop_reason=StopReason.LOSS_LIMIT,
            hands_played=40,
            starting_bankroll=500.0,
            final_bankroll=300.0,
            session_profit=-200.0,
            total_wagered=1200.0,
            total_bonus_wagered=0.0,
            peak_bankroll=550.0,
            max_drawdown=250.0,
            max_drawdown_pct=0.45,
        ),
        SessionResult(
            outcome=SessionOutcome.PUSH,
            stop_reason=StopReason.MAX_HANDS,
            hands_played=50,
            starting_bankroll=500.0,
            final_bankroll=500.0,
            session_profit=0.0,
            total_wagered=1500.0,
            total_bonus_wagered=0.0,
            peak_bankroll=580.0,
            max_drawdown=80.0,
            max_drawdown_pct=0.14,
        ),
        SessionResult(
            outcome=SessionOutcome.LOSS,
            stop_reason=StopReason.INSUFFICIENT_FUNDS,
            hands_played=5,
            starting_bankroll=500.0,
            final_bankroll=10.0,
            session_profit=-490.0,
            total_wagered=500.0,
            total_bonus_wagered=0.0,
            peak_bankroll=520.0,
            max_drawdown=510.0,
            max_drawdown_pct=0.98,
        ),
    ]


@pytest.fixture
def sample_simulation_results(sample_session_results: list[SessionResult]):
    """Create sample SimulationResults for testing."""
    from let_it_ride.config.models import (
        BankrollConfig,
        BettingSystemConfig,
        FullConfig,
        SimulationConfig,
        StopConditionsConfig,
        StrategyConfig,
    )
    from let_it_ride.simulation.controller import SimulationResults

    config = FullConfig(
        simulation=SimulationConfig(num_sessions=4, hands_per_session=50),
        bankroll=BankrollConfig(
            starting_amount=500.0,
            base_bet=5.0,
            stop_conditions=StopConditionsConfig(win_limit=100.0, loss_limit=200.0),
            betting_system=BettingSystemConfig(type="flat"),
        ),
        strategy=StrategyConfig(type="basic"),
    )
    return SimulationResults(
        config=config,
        session_results=sample_session_results,
        start_time=datetime(2025, 1, 15, 10, 30, 0),
        end_time=datetime(2025, 1, 15, 10, 35, 0),
        total_hands=120,
    )


@pytest.fixture
def sample_stats(sample_session_results: list[SessionResult]):
    """Create sample DetailedStatistics for testing."""
    return calculate_statistics_from_results(sample_session_results)


class TestHTMLReportConfig:
    """Tests for HTMLReportConfig dataclass."""

    def test_default_values(self) -> None:
        """Verify default configuration values."""
        config = HTMLReportConfig()

        assert config.title == "Let It Ride Simulation Report"
        assert config.include_charts is True
        assert config.chart_library == "plotly"
        assert config.include_config is True
        assert config.include_raw_data is False
        assert config.self_contained is True
        assert config.trajectory_sample_size == 10
        assert config.histogram_bins == "auto"

    def test_custom_values(self) -> None:
        """Verify custom configuration values are applied."""
        config = HTMLReportConfig(
            title="Custom Report",
            include_charts=False,
            include_config=False,
            include_raw_data=True,
            self_contained=False,
            trajectory_sample_size=20,
            histogram_bins=50,
        )

        assert config.title == "Custom Report"
        assert config.include_charts is False
        assert config.include_config is False
        assert config.include_raw_data is True
        assert config.self_contained is False
        assert config.trajectory_sample_size == 20
        assert config.histogram_bins == 50


class TestGenerateHtmlReport:
    """Tests for generate_html_report function."""

    def test_creates_file(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify HTML file is created."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)
        assert path.exists()

    def test_creates_parent_directories(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify parent directories are created if they don't exist."""
        path = tmp_path / "subdir" / "nested" / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)
        assert path.exists()

    def test_valid_html(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify output is valid HTML structure."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content
        assert "<head>" in content
        assert "</head>" in content
        assert "<body>" in content
        assert "</body>" in content

    def test_contains_title(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify HTML contains the report title."""
        path = tmp_path / "report.html"
        config = HTMLReportConfig(title="Test Report Title")
        generate_html_report(sample_simulation_results, sample_stats, path, config)

        content = path.read_text(encoding="utf-8")
        assert "Test Report Title" in content
        assert "<title>Test Report Title</title>" in content

    def test_contains_statistics(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify HTML contains key statistics."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        # Check for key metrics
        assert "Session Win Rate" in content
        assert "Expected Value" in content or "EV" in content
        assert "Total Sessions" in content
        assert "Total Hands" in content

    def test_contains_plotly_charts_by_default(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify HTML contains Plotly charts when include_charts=True (default)."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        # Plotly generates divs with specific IDs
        assert "histogram-chart" in content
        assert "trajectory-chart" in content
        assert "frequency-chart" in content

    def test_self_contained_includes_plotly_js(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify self-contained report includes Plotly JS inline."""
        path = tmp_path / "report.html"
        config = HTMLReportConfig(self_contained=True)
        generate_html_report(sample_simulation_results, sample_stats, path, config)

        content = path.read_text(encoding="utf-8")
        # Self-contained should have inline Plotly JS
        assert "Plotly" in content

    def test_no_charts_when_disabled(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify charts are excluded when include_charts=False."""
        path = tmp_path / "report.html"
        config = HTMLReportConfig(include_charts=False)
        generate_html_report(sample_simulation_results, sample_stats, path, config)

        content = path.read_text(encoding="utf-8")
        # Should not have chart containers
        assert "histogram-chart" not in content
        assert "trajectory-chart" not in content

    def test_contains_config_by_default(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify HTML contains configuration when include_config=True (default)."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        assert "Configuration" in content
        assert "Starting Amount" in content or "starting_amount" in content
        assert "Base Bet" in content or "base_bet" in content
        assert "basic" in content  # Strategy type

    def test_no_config_when_disabled(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify configuration is excluded when include_config=False."""
        path = tmp_path / "report.html"
        config = HTMLReportConfig(include_config=False)
        generate_html_report(sample_simulation_results, sample_stats, path, config)

        content = path.read_text(encoding="utf-8")
        # Config section header should not appear
        assert "Configuration Summary" not in content

    def test_raw_data_when_enabled(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify raw session data is included when include_raw_data=True."""
        path = tmp_path / "report.html"
        config = HTMLReportConfig(include_raw_data=True)
        generate_html_report(sample_simulation_results, sample_stats, path, config)

        content = path.read_text(encoding="utf-8")
        # Should have session details table
        assert "Session Details" in content
        # Should have table with outcome values
        assert "win" in content.lower()
        assert "loss" in content.lower()

    def test_no_raw_data_by_default(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify raw session data is excluded by default."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        assert "Session Details" not in content

    def test_responsive_design_elements(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify HTML contains responsive design elements."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        # Viewport meta tag for mobile
        assert "viewport" in content
        # Media queries for responsive design
        assert "@media" in content

    def test_print_styles(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify HTML contains print-friendly styles."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        assert "@media print" in content

    def test_utf8_encoding(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify HTML is properly UTF-8 encoded."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        assert 'charset="UTF-8"' in content or "charset=UTF-8" in content


class TestHTMLReportGenerator:
    """Tests for HTMLReportGenerator class."""

    def test_render_returns_string(
        self, sample_simulation_results, sample_stats
    ) -> None:
        """Verify render returns HTML as string."""
        generator = HTMLReportGenerator()
        html = generator.render(sample_simulation_results, sample_stats)

        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_render_with_custom_config(
        self, sample_simulation_results, sample_stats
    ) -> None:
        """Verify render respects custom configuration."""
        config = HTMLReportConfig(title="Custom Title", include_charts=False)
        generator = HTMLReportGenerator(config)
        html = generator.render(sample_simulation_results, sample_stats)

        assert "Custom Title" in html
        assert "histogram-chart" not in html

    def test_config_property(self) -> None:
        """Verify config property returns configuration."""
        config = HTMLReportConfig(title="Test")
        generator = HTMLReportGenerator(config)

        assert generator.config.title == "Test"

    def test_default_config(self) -> None:
        """Verify default configuration is used when none provided."""
        generator = HTMLReportGenerator()

        assert generator.config.title == "Let It Ride Simulation Report"


class TestHTMLExporter:
    """Tests for HTMLExporter class."""

    def test_creates_output_directory(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify output directory is created if it doesn't exist."""
        output_dir = tmp_path / "subdir" / "output"
        exporter = HTMLExporter(output_dir)

        exporter.export(sample_simulation_results, sample_stats)
        assert output_dir.exists()

    def test_exports_with_default_prefix(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify default prefix is 'simulation'."""
        exporter = HTMLExporter(tmp_path)
        path = exporter.export(sample_simulation_results, sample_stats)

        assert path.name == "simulation_report.html"

    def test_exports_with_custom_prefix(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify custom prefix is used in filename."""
        exporter = HTMLExporter(tmp_path, prefix="my_sim")
        path = exporter.export(sample_simulation_results, sample_stats)

        assert path.name == "my_sim_report.html"

    def test_config_propagates(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify config is applied to exports."""
        config = HTMLReportConfig(title="Exporter Test", include_charts=False)
        exporter = HTMLExporter(tmp_path, config=config)
        path = exporter.export(sample_simulation_results, sample_stats)

        content = path.read_text(encoding="utf-8")
        assert "Exporter Test" in content
        assert "histogram-chart" not in content

    def test_properties(self, tmp_path: Path) -> None:
        """Verify exporter properties are accessible."""
        config = HTMLReportConfig(title="Test")
        exporter = HTMLExporter(tmp_path, prefix="test", config=config)

        assert exporter.output_dir == tmp_path
        assert exporter.prefix == "test"
        assert exporter.config.title == "Test"

    def test_returns_path(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify export returns path to created file."""
        exporter = HTMLExporter(tmp_path)
        path = exporter.export(sample_simulation_results, sample_stats)

        assert isinstance(path, Path)
        assert path.exists()


class TestChartGeneration:
    """Tests for chart generation functionality."""

    def test_histogram_chart_data(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify histogram chart contains session profit data."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        # Histogram should be present
        assert (
            "Session Outcome Distribution" in content or "histogram" in content.lower()
        )

    def test_trajectory_chart_data(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify trajectory chart shows bankroll paths."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        # Trajectory chart should be present
        assert "Bankroll" in content

    def test_hand_frequency_chart(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify hand frequency chart is generated."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        # Hand frequency chart should be present
        assert "Hand Frequency" in content


class TestRiskMetricsDisplay:
    """Tests for risk metrics display."""

    def test_displays_loss_probabilities(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify loss probability metrics are displayed."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        assert "Risk" in content
        # Should show various loss probability metrics
        assert "Loss" in content or "loss" in content

    def test_displays_drawdown_stats(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify drawdown statistics are displayed."""
        path = tmp_path / "report.html"
        generate_html_report(sample_simulation_results, sample_stats, path)

        content = path.read_text(encoding="utf-8")
        assert "Drawdown" in content or "drawdown" in content


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_session(self, tmp_path: Path) -> None:
        """Verify report generation with single session."""
        from let_it_ride.config.models import FullConfig
        from let_it_ride.simulation.controller import SimulationResults

        session = SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.MAX_HANDS,
            hands_played=10,
            starting_bankroll=100.0,
            final_bankroll=110.0,
            session_profit=10.0,
            total_wagered=30.0,
            total_bonus_wagered=0.0,
            peak_bankroll=115.0,
            max_drawdown=5.0,
            max_drawdown_pct=0.05,
        )

        results = SimulationResults(
            config=FullConfig(),
            session_results=[session],
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            total_hands=10,
        )

        stats = calculate_statistics_from_results([session])
        path = tmp_path / "single_session.html"
        generate_html_report(results, stats, path)

        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_many_sessions(self, tmp_path: Path) -> None:
        """Verify report generation with many sessions."""
        from let_it_ride.config.models import FullConfig
        from let_it_ride.simulation.controller import SimulationResults

        num_sessions = 100
        sessions = [
            SessionResult(
                outcome=SessionOutcome.WIN if i % 3 == 0 else SessionOutcome.LOSS,
                stop_reason=StopReason.MAX_HANDS,
                hands_played=50 + (i % 10),
                starting_bankroll=500.0,
                final_bankroll=500.0 + (i % 200) - 100,
                session_profit=(i % 200) - 100,
                total_wagered=1500.0,
                total_bonus_wagered=0.0,
                peak_bankroll=600.0,
                max_drawdown=100.0,
                max_drawdown_pct=0.17,
            )
            for i in range(num_sessions)
        ]

        results = SimulationResults(
            config=FullConfig(),
            session_results=sessions,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            total_hands=sum(s.hands_played for s in sessions),
        )

        stats = calculate_statistics_from_results(sessions)
        path = tmp_path / "many_sessions.html"
        generate_html_report(results, stats, path)

        assert path.exists()

    def test_all_winning_sessions(self, tmp_path: Path) -> None:
        """Verify report generation when all sessions are wins."""
        from let_it_ride.config.models import FullConfig
        from let_it_ride.simulation.controller import SimulationResults

        sessions = [
            SessionResult(
                outcome=SessionOutcome.WIN,
                stop_reason=StopReason.WIN_LIMIT,
                hands_played=20 + i,
                starting_bankroll=500.0,
                final_bankroll=600.0 + i * 10,
                session_profit=100.0 + i * 10,
                total_wagered=600.0,
                total_bonus_wagered=0.0,
                peak_bankroll=610.0 + i * 10,
                max_drawdown=10.0,
                max_drawdown_pct=0.02,
            )
            for i in range(5)
        ]

        results = SimulationResults(
            config=FullConfig(),
            session_results=sessions,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            total_hands=sum(s.hands_played for s in sessions),
        )

        stats = calculate_statistics_from_results(sessions)
        path = tmp_path / "all_wins.html"
        generate_html_report(results, stats, path)

        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "100.00%" in content  # 100% win rate

    def test_all_losing_sessions(self, tmp_path: Path) -> None:
        """Verify report generation when all sessions are losses."""
        from let_it_ride.config.models import FullConfig
        from let_it_ride.simulation.controller import SimulationResults

        sessions = [
            SessionResult(
                outcome=SessionOutcome.LOSS,
                stop_reason=StopReason.LOSS_LIMIT,
                hands_played=30 + i,
                starting_bankroll=500.0,
                final_bankroll=300.0 - i * 10,
                session_profit=-200.0 - i * 10,
                total_wagered=900.0,
                total_bonus_wagered=0.0,
                peak_bankroll=520.0,
                max_drawdown=220.0 + i * 10,
                max_drawdown_pct=0.44 + i * 0.02,
            )
            for i in range(5)
        ]

        results = SimulationResults(
            config=FullConfig(),
            session_results=sessions,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            total_hands=sum(s.hands_played for s in sessions),
        )

        stats = calculate_statistics_from_results(sessions)
        path = tmp_path / "all_losses.html"
        generate_html_report(results, stats, path)

        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "0.00%" in content  # 0% win rate


class TestCDNMode:
    """Tests for CDN mode (self_contained=False)."""

    def test_cdn_mode_uses_external_plotly(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify CDN mode uses external Plotly.js instead of inline."""
        path = tmp_path / "cdn_report.html"
        config = HTMLReportConfig(self_contained=False)
        generate_html_report(sample_simulation_results, sample_stats, path, config)

        content = path.read_text(encoding="utf-8")
        # CDN mode should reference external Plotly
        assert "cdn.plot.ly" in content or "plotly" in content.lower()
        # Should still have chart containers
        assert "histogram-chart" in content

    def test_cdn_mode_smaller_file_size(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify CDN mode produces smaller file than self-contained."""
        cdn_path = tmp_path / "cdn_report.html"
        contained_path = tmp_path / "contained_report.html"

        cdn_config = HTMLReportConfig(self_contained=False)
        contained_config = HTMLReportConfig(self_contained=True)

        generate_html_report(
            sample_simulation_results, sample_stats, cdn_path, cdn_config
        )
        generate_html_report(
            sample_simulation_results, sample_stats, contained_path, contained_config
        )

        # CDN version should be much smaller (Plotly.js is ~3MB inline)
        cdn_size = cdn_path.stat().st_size
        contained_size = contained_path.stat().st_size
        assert cdn_size < contained_size


class TestConfigOptions:
    """Tests for configuration options (histogram_bins, trajectory_sample_size)."""

    def test_histogram_bins_integer(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify histogram_bins accepts integer value."""
        path = tmp_path / "report.html"
        config = HTMLReportConfig(histogram_bins=20)
        generate_html_report(sample_simulation_results, sample_stats, path, config)

        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "histogram-chart" in content

    def test_histogram_bins_auto(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify histogram_bins='auto' works correctly."""
        path = tmp_path / "report.html"
        config = HTMLReportConfig(histogram_bins="auto")
        generate_html_report(sample_simulation_results, sample_stats, path, config)

        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "histogram-chart" in content

    def test_trajectory_sample_size(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify trajectory_sample_size controls number of trajectories shown."""
        path = tmp_path / "report.html"
        # Use a sample size larger than available sessions
        config = HTMLReportConfig(trajectory_sample_size=2)
        generate_html_report(sample_simulation_results, sample_stats, path, config)

        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "trajectory-chart" in content
        # Title should reflect sample size
        assert "Sample of" in content

    def test_trajectory_sample_size_exceeds_sessions(
        self, tmp_path: Path, sample_simulation_results, sample_stats
    ) -> None:
        """Verify trajectory handles sample_size larger than session count."""
        path = tmp_path / "report.html"
        # 4 sessions in sample data, request 20
        config = HTMLReportConfig(trajectory_sample_size=20)
        generate_html_report(sample_simulation_results, sample_stats, path, config)

        assert path.exists()
        content = path.read_text(encoding="utf-8")
        # Should show all 4 sessions since we only have 4
        assert "Sample of 4" in content


class TestModuleExports:
    """Tests for module exports."""

    def test_exports_from_analytics_package(self) -> None:
        """Verify all exports are available from analytics package."""
        from let_it_ride.analytics import (
            HTMLExporter,
            HTMLReportConfig,
            HTMLReportGenerator,
            generate_html_report,
        )

        # Just verify they're importable
        assert HTMLExporter is not None
        assert HTMLReportConfig is not None
        assert HTMLReportGenerator is not None
        assert generate_html_report is not None
