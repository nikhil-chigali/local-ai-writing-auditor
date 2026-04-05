import hashlib
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

app = typer.Typer(
    name="review",
    help="Local AI Writing Auditor — detect and rewrite AI writing tells using local Ollama models.",
    add_completion=False,
)
console = Console()


def _article_id(file: Path) -> str:
    """Stable short ID derived from filename."""
    return hashlib.md5(file.name.encode()).hexdigest()[:8]


def _print_issues(flagged_sentences) -> None:
    if not flagged_sentences:
        console.print("[green]No AI writing tells detected.[/green]")
        return
    for fs in flagged_sentences:
        active = {k: v for k, v in fs.labels.items() if v}
        label_str = "  ".join(
            f"[yellow]{cat}[/yellow]: {', '.join(patterns)}"
            for cat, patterns in active.items()
        )
        severity_color = {"high": "red", "medium": "yellow", "low": "cyan"}.get(fs.severity, "white")
        console.print(
            Panel(
                f"[italic]{fs.text}[/italic]\n{label_str}",
                title=f"[{severity_color}]{fs.severity.upper()}[/{severity_color}]  {fs.sentence_id}",
                border_style=severity_color,
            )
        )


def _print_what_changed(rewrites) -> None:
    if not rewrites:
        console.print("[dim]Nothing rewritten.[/dim]")
        return
    for r in rewrites:
        console.print(f"  [dim]{r.sentence_id}[/dim]  {r.change_summary}")


@app.command()
def review(
    file: Path = typer.Option(..., "--file", help="Path to article file (.md or .txt)", exists=True),
    model: str = typer.Option("mistral", "--model", help="Ollama model tag: mistral | llama3.2:3b | phi4"),
    mode: str = typer.Option(
        "rewrite",
        "--mode",
        help="Pipeline mode: 'rewrite' (detect + rewrite, two-pass) or 'detect-only' (audit report only)",
    ),
    output_json: Optional[Path] = typer.Option(None, "--output-json", help="Write full audit report to JSON file"),
) -> None:
    """Audit an article for AI writing tells and optionally rewrite them."""
    from src.agents.auditor import AuditorAgent
    from src.agents.rewriter import RewriterAgent

    text = file.read_text(encoding="utf-8")
    article_id = _article_id(file)

    console.print(Rule(f"[bold]AI Writing Auditor[/bold]  model={model}  mode={mode}"))

    # --- Pass 1: Audit ---
    console.print("\n[bold cyan]Running Pass 1 audit…[/bold cyan]")
    auditor = AuditorAgent(model=model)
    audit_report = auditor.run(text=text, article_id=article_id)

    console.print(Rule("[bold]Issues Found[/bold]"))
    console.print(f"Verdict: [bold]{audit_report.verdict}[/bold]  |  {audit_report.flag_count} flags  |  {audit_report.category_count} categories\n")
    _print_issues(audit_report.flagged_sentences)

    if mode == "detect-only":
        if output_json:
            output_json.write_text(audit_report.model_dump_json(indent=2), encoding="utf-8")
            console.print(f"\n[dim]Report written to {output_json}[/dim]")
        console.print(Rule("[dim]detect-only mode — skipping rewrite[/dim]"))
        return

    # --- Rewrite ---
    console.print(f"\n[bold cyan]Rewriting {len(audit_report.flagged_sentences)} flagged sentences…[/bold cyan]")
    rewriter = RewriterAgent(model=model)
    rewrite_report = rewriter.run(
        flagged_sentences=audit_report.flagged_sentences,
        article_id=article_id,
        original_text=text,
    )

    console.print(Rule("[bold]Rewritten Version[/bold]"))
    console.print(rewrite_report.full_rewritten_text)

    console.print(Rule("[bold]What Changed[/bold]"))
    _print_what_changed(rewrite_report.rewrites)

    # --- Pass 2: Re-audit rewritten text ---
    console.print("\n[bold cyan]Running Pass 2 audit on rewritten text…[/bold cyan]")
    pass2_report = auditor.run(text=rewrite_report.full_rewritten_text, article_id=f"{article_id}_pass2")

    console.print(Rule("[bold]Second-Pass Audit[/bold]"))
    if not pass2_report.flagged_sentences:
        console.print("[green]No surviving patterns detected. Rewrite is clean.[/green]")
    else:
        console.print(f"[yellow]{pass2_report.flag_count} pattern(s) survived the rewrite:[/yellow]\n")
        _print_issues(pass2_report.flagged_sentences)

    if output_json:
        import json
        combined = {
            "pass1": audit_report.model_dump(),
            "rewrite": rewrite_report.model_dump(),
            "pass2": pass2_report.model_dump(),
        }
        output_json.write_text(json.dumps(combined, indent=2), encoding="utf-8")
        console.print(f"\n[dim]Report written to {output_json}[/dim]")

    console.print(Rule())


if __name__ == "__main__":
    app()
