import json
import enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule


class Mode(str, enum.Enum):
    rewrite = "rewrite"
    detect_only = "detect-only"


app = typer.Typer(
    name="review",
    help="Local AI Writing Auditor — detect and rewrite AI writing tells using local Ollama models.",
    add_completion=False,
)
console = Console()


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
    mode: Mode = typer.Option(
        Mode.rewrite,
        "--mode",
        help="Pipeline mode: 'rewrite' (detect + rewrite, two-pass) or 'detect-only' (audit report only)",
    ),
    output_json: Optional[Path] = typer.Option(None, "--output-json", help="Write full audit report to JSON file"),
) -> None:
    """Audit an article for AI writing tells and optionally rewrite them."""
    from src.pipeline import run_detect_only, run_full_pipeline

    text = file.read_text(encoding="utf-8")

    console.print(Rule(f"[bold]AI Writing Auditor[/bold]  model={model}  mode={mode}"))

    if mode == Mode.detect_only:
        console.print("\n[bold cyan]Running Pass 1 audit…[/bold cyan]")
        result = run_detect_only(text=text, model=model)

        console.print(Rule("[bold]Issues Found[/bold]"))
        console.print(
            f"Verdict: [bold]{result.pass1.verdict}[/bold]  |  "
            f"{result.pass1.flag_count} flags  |  {result.pass1.category_count} categories\n"
        )
        _print_issues(result.pass1.flagged_sentences)

        if output_json:
            output_json.write_text(result.pass1.model_dump_json(indent=2), encoding="utf-8")
            console.print(f"\n[dim]Report written to {output_json}[/dim]")

        console.print(Rule("[dim]detect-only mode — skipping rewrite[/dim]"))
        return

    # Full pipeline
    console.print("\n[bold cyan]Running Pass 1 audit…[/bold cyan]")
    result = run_full_pipeline(text=text, model=model)

    console.print(Rule("[bold]Issues Found[/bold]"))
    console.print(
        f"Verdict: [bold]{result.pass1.verdict}[/bold]  |  "
        f"{result.pass1.flag_count} flags  |  {result.pass1.category_count} categories\n"
    )
    _print_issues(result.pass1.flagged_sentences)

    console.print(Rule("[bold]Rewritten Version[/bold]"))
    console.print(result.rewrite.full_rewritten_text)

    console.print(Rule("[bold]What Changed[/bold]"))
    _print_what_changed(result.rewrite.rewrites)

    console.print(Rule("[bold]Second-Pass Audit[/bold]"))
    if not result.pass2.flagged_sentences:
        console.print("[green]No surviving patterns detected. Rewrite is clean.[/green]")
    else:
        console.print(f"[yellow]{result.pass2.flag_count} pattern(s) survived the rewrite:[/yellow]\n")
        _print_issues(result.pass2.flagged_sentences)

    if output_json:
        combined = {
            "pass1": result.pass1.model_dump(),
            "rewrite": result.rewrite.model_dump(),
            "pass2": result.pass2.model_dump(),
        }
        output_json.write_text(json.dumps(combined, indent=2), encoding="utf-8")
        console.print(f"\n[dim]Report written to {output_json}[/dim]")

    console.print(Rule())


if __name__ == "__main__":
    app()
