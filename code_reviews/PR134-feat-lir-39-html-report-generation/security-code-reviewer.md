# Security Code Review for PR #134

## Summary

This PR adds HTML report generation using Jinja2 templates with embedded Plotly visualizations. The implementation follows secure practices with autoescaping enabled for template rendering and uses Jinja2's `PackageLoader` which restricts template loading to the package directory. However, the use of the `| safe` filter in the template to render Plotly chart HTML bypasses the autoescape protection, which is intentional but warrants documentation.

## Findings

### Critical

No critical security vulnerabilities identified.

### High

No high severity issues identified.

### Medium

**M1: Intentional XSS bypass with `| safe` filter** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/templates/report.html.j2:453,462,471` - The template uses `{{ histogram_html | safe }}`, `{{ trajectory_html | safe }}`, and `{{ hand_frequency_html | safe }}` to render Plotly chart HTML without escaping. While this is necessary for the charts to function (Plotly's `to_html()` generates trusted HTML/JavaScript), it creates a trust boundary that should be documented. The chart HTML is generated programmatically from internal simulation data via Plotly's `Figure.to_html()` method, so the risk is minimal. However, if in the future user-controlled data is ever passed directly to chart titles or annotations, this could become exploitable.

**Recommendation**: Add a code comment in `export_html.py` near the chart generation explaining that the HTML is trusted output from Plotly and must never include unvalidated user input. Consider also auditing any future modifications to chart generation code.

**CWE Reference**: CWE-79 (Improper Neutralization of Input During Web Page Generation)

**M2: Path traversal potential in output path handling** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:731-732` - The `generate_html_report()` function accepts an arbitrary `output_path` parameter and creates parent directories with `output_path.parent.mkdir(parents=True, exist_ok=True)`. If the output path is constructed from user input without validation, this could allow writing files to unintended locations. While this is a local file writing operation (not remote), it could be exploited if the CLI eventually accepts untrusted output paths.

**Recommendation**: The CLI layer (when it integrates this feature) should validate that output paths are within expected directories or use path canonicalization to prevent directory traversal attacks.

**CWE Reference**: CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)

### Low

**L1: Fixed directory permissions** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:682,732` - The directory creation uses `mode=0o755` which is appropriate for most use cases. On shared systems, users may want more restrictive permissions (0o700). This is a minor consideration as the reports contain non-sensitive simulation data.

**L2: CDN dependency for non-self-contained reports** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:533` - When `self_contained=False`, the report relies on Plotly's CDN (`include_plotlyjs="cdn"`). This creates a minor external dependency. The default `self_contained=True` embeds the JavaScript, which is the secure default.

## Security Positives

1. **Jinja2 autoescape enabled**: Line 505 uses `select_autoescape(["html", "xml"])` which provides HTML escaping by default for template variables.

2. **PackageLoader for templates**: Line 504 uses `PackageLoader("let_it_ride.analytics", "templates")` which restricts template loading to the package's templates directory, preventing arbitrary template file inclusion.

3. **UTF-8 encoding enforced**: File operations explicitly specify `encoding="utf-8"` (lines 704, 738), preventing encoding-related vulnerabilities.

4. **Data comes from internal sources**: All data rendered in the template originates from simulation results and statistics calculations, not from external user input, significantly reducing injection risk.

5. **No use of dangerous functions**: No use of `eval()`, `exec()`, `pickle`, or `subprocess` in the new code.
