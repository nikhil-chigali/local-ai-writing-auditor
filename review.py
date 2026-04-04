from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="review",
    help="Local AI Writing Auditor — detect and rewrite AI writing tells using local Ollama models.",
    add_completion=False,
)


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
    raise NotImplementedError(
        f"Pipeline not implemented yet.\n"
        f"  file={file}\n"
        f"  model={model}\n"
        f"  mode={mode}\n"
        f"  output_json={output_json}"
    )


if __name__ == "__main__":
    app()
