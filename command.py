"""
Translator Command - 字幕翻译工具

使用 Typer 构建的命令行界面，支持字幕翻译功能。
基于 SubtitleWorkflow 实现字幕文件的翻译处理。
"""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from translator.agents.workflow import SubtitleWorkflow

app = typer.Typer(help="Translator Command - 字幕翻译工具")
console = Console()


@app.command("file")
def trans_file(
    file: Path = typer.Argument(..., help="SRT文件"),
    out: Optional[Path] = typer.Option(None, "-o", help="输出路径"),
    src: str = typer.Option("en", "-s", help="源语言"),
    tgt: str = typer.Option("zh", "-t", help="目标语言"),
    tokens: int = typer.Option(2000, "-m", help="最大token数"),
):
    """翻译单个SRT文件"""
    if not file.exists():
        console.print(f"[bold red]错误:[/bold red] 文件{file}不存在")
        raise typer.Exit(1)

    # 如果未提供 out，则交由 workflow 生成输出路径（保存在输入同目录并添加后缀）
    if out is None:
        console.print(f"[bold green]开始:[/bold green] {file} -> (自动生成输出路径)")
    else:
        console.print(f"[bold green]开始:[/bold green] {file} -> {out}")

    asyncio.run(_trans_file(file, out, src, tgt, tokens))


async def _trans_file(
    in_path: Path, out_path: Optional[Path], src: str, tgt: str, tokens: int
):
    """处理单个文件"""
    wf = SubtitleWorkflow(max_tokens=tokens)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        console=console,
    ) as progress:
        task = progress.add_task("处理中", total=None)

        async for resp in wf.arun(
            input_path=str(in_path),
            output_path=str(out_path) if out_path is not None else None,
            source_lang=src,
            target_lang=tgt,
        ):
            if hasattr(resp, "content"):
                progress.update(task, description=resp.content)

            if getattr(resp, "error", None):
                console.print(f"[bold red]错误:[/bold red] {getattr(resp, 'error')}")
                raise typer.Exit(1)

    if out_path is None:
        generated = in_path.with_stem(f"{in_path.stem}_{tgt}")
        console.print(
            f"[bold green]完成:[/bold green] 输出已生成于 {generated}（输入同目录）"
        )
    else:
        console.print(f"[bold green]完成:[/bold green] {out_path}")


@app.command("dir")
def trans_dir(
    dir: Path = typer.Argument(..., help="SRT目录"),
    out_dir: Optional[Path] = typer.Option(None, "-o", help="输出目录"),
    src: str = typer.Option("en", "-s", help="源语言"),
    tgt: str = typer.Option("zh", "-t", help="目标语言"),
    tokens: int = typer.Option(2000, "-m", help="最大token数"),
):
    """批量翻译目录下的SRT文件"""
    if not dir.exists() or not dir.is_dir():
        console.print(f"[bold red]错误:[/bold red] {dir}不存在或非目录")
        raise typer.Exit(1)

    if out_dir and not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)

    asyncio.run(_trans_dir(dir, out_dir, src, tgt, tokens))


async def _trans_dir(
    in_dir: Path, out_dir: Optional[Path], src: str, tgt: str, tokens: int
):
    """处理目录中的所有文件"""
    files = list(in_dir.rglob("*.srt"))

    if not files:
        console.print(f"[bold yellow]警告:[/bold yellow] {in_dir}中无SRT文件")
        return

    console.print(f"[bold blue]找到{len(files)}个SRT文件[/bold blue]")

    for i, in_file in enumerate(files, 1):
        # 交由 workflow 生成具体输出文件；如果用户指定了 out_dir，传入该目录
        if out_dir:
            # ensure directory exists
            rel_path = in_file.relative_to(in_dir)
            (out_dir / rel_path).parent.mkdir(parents=True, exist_ok=True)
            out_file = out_dir
        else:
            out_file = None

        console.print(f"[{i}/{len(files)}] 处理: {in_file}")

        try:
            await _trans_file(
                in_path=in_file,
                out_path=out_file,
                src=src,
                tgt=tgt,
                tokens=tokens,
            )
        except Exception as e:
            console.print(f"[bold red]错误:[/bold red] {in_file}: {str(e)}")

    console.print("[bold green]全部完成![/bold green]")


if __name__ == "__main__":
    app()
