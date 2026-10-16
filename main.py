"""
WebP Batch & Single Image Compressor CLI Engine.
Entry point and CLI interface with rich terminal UI and robust error handling.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from converter.engine import ImageConversionError, convert_image_to_webp
from converter.validator import SUPPORTED_EXTENSIONS, is_supported_image, scan_images

# Enable UTF-8 encoding support on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()



def format_bytes(size: float) -> str:
    """Format bytes into readable human-friendly string (KB, MB, GB)."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(size) < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def bootstrap_directories(input_dir: Path, output_dir: Path) -> None:
    """Ensure default or targeted input and output directories exist."""
    try:
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        console.print(
            f"[bold red]Permission Error:[/bold red] Tidak memiliki izin untuk membuat/mengakses direktori: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


def parse_arguments() -> argparse.Namespace:
    """Build and parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="High-Performance CLI Image Converter & Compressor (PNG/JPEG/JPG/JPE to WebP)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=Path("input"),
        help="Path direktori input kustom",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("output"),
        help="Path direktori output kustom",
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        default=None,
        help="Path berkas tunggal yang akan dikonversi (menonaktifkan mode batch direktori)",
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=80,
        help="Faktor kualitas WebP (1-100)",
    )
    parser.add_argument(
        "-l", "--lossless",
        action="store_true",
        default=False,
        help="Aktifkan kompresi lossless WebP",
    )
    parser.add_argument(
        "-w", "--overwrite",
        action="store_true",
        default=True,
        help="Timpa berkas jika berkas output dengan nama yang sama sudah ada (aktif secara default)",
    )
    parser.add_argument(
        "--no-overwrite",
        dest="overwrite",
        action="store_false",
        help="Jangan timpa berkas jika berkas output dengan nama yang sama sudah ada (lewati)",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        default=False,
        help="Pindai subfolder secara rekursif dalam mode direktori",
    )
    parser.add_argument(
        "-m", "--method",
        type=int,
        default=6,
        choices=range(0, 7),
        help="Tingkat usaha kompresi WebP (0=tercepat, 6=kompresi terbaik/paling optimal)",
    )
    parser.add_argument(
        "-L", "--limit",
        type=int,
        default=None,
        help="Batasi jumlah maksimum berkas yang diproses setelah seluruh berkas diurutkan secara alfabetis (ASC)",
    )

    return parser.parse_args()


def resolve_destination(
    source_path: Path,
    input_base: Path,
    output_base: Path,
    is_single_file: bool,
    claimed_destinations: Dict[Path, Path],
    overwrite: bool,
) -> Tuple[Optional[Path], str]:
    """
    Determine target destination path, respecting subfolder structure (if recursive)
    and avoiding duplicate collisions within the same run.
    
    Returns:
        Tuple[target_path, status]: status can be 'PROCEED', 'SKIPPED'
    """
    if is_single_file:
        target_name = f"{source_path.stem}.webp"
        target_path = output_base / target_name
    else:
        try:
            rel_path = source_path.relative_to(input_base)
            target_rel = rel_path.with_suffix(".webp")
            target_path = output_base / target_rel
        except ValueError:
            target_path = output_base / f"{source_path.stem}.webp"

    # Collision check within batch (e.g., logo.png and logo.jpg)
    if target_path in claimed_destinations:
        prior_source = claimed_destinations[target_path]
        if not overwrite:
            # Add unique suffix based on original extension
            clean_ext = source_path.suffix.lstrip(".").lower()
            target_path = target_path.with_name(f"{target_path.stem}_{clean_ext}.webp")
            console.print(
                f"[yellow]⚠️ Benturan nama terdeteksi antara '{prior_source.name}' dan '{source_path.name}'. Dialihkan ke '{target_path.name}'[/yellow]"
            )

    claimed_destinations[target_path] = source_path

    # Overwrite check against filesystem
    if target_path.exists() and not overwrite:
        return target_path, "SKIPPED"

    return target_path, "PROCEED"


def display_summary_table(
    total_found: int,
    converted_count: int,
    skipped_count: int,
    failed_count: int,
    total_orig_size: int,
    total_new_size: int,
    elapsed_time: float,
    limit: Optional[int] = None,
) -> None:
    """Render the rich summary report table."""
    saved_bytes = total_orig_size - total_new_size
    saved_percent = (
        (saved_bytes / total_orig_size * 100) if total_orig_size > 0 else 0.0
    )

    table = Table(title="📊 Ringkasan Konversi WebP", show_header=True, header_style="bold cyan")
    table.add_column("Metrik", style="bold")
    table.add_column("Nilai", justify="right")

    table.add_row("Total Berkas Ditemukan", str(total_found))
    if limit is not None and limit > 0:
        table.add_row("Batas Eksekusi (--limit)", f"[cyan]{min(limit, total_found)} berkas[/cyan]")
    table.add_row("Berhasil Dikonversi", f"[green]{converted_count}[/green]")
    table.add_row("Dilewati (Sudah Ada)", f"[yellow]{skipped_count}[/yellow]")
    table.add_row("Gagal Diproses", f"[red]{failed_count}[/red]" if failed_count > 0 else "0")
    table.add_row("Ukuran Sebelum Kompresi", format_bytes(total_orig_size))
    table.add_row("Ukuran Sesudah Kompresi", format_bytes(total_new_size))
    
    saved_color = "green" if saved_bytes >= 0 else "yellow"
    table.add_row(
        "Penghematan Ruang (Saved Space)",
        f"[{saved_color}]{format_bytes(saved_bytes)} ({saved_percent:.2f}%)[/{saved_color}]"
    )
    table.add_row("Durasi Eksekusi", f"{elapsed_time:.2f} detik")

    console.print()
    console.print(table)


def main() -> None:
    """Main execution function."""
    args = parse_arguments()
    start_time = time.time()

    # Step 6.3: Validasi permission & bootstrap
    try:
        if args.file is not None:
            if not args.file.exists():
                console.print(
                    f"[bold red]Error:[/bold red] Berkas input '{args.file}' tidak ditemukan.",
                    file=sys.stderr,
                )
                sys.exit(1)
            if not is_supported_image(args.file):
                console.print(
                    f"[bold red]Error:[/bold red] Ekstensi berkas '{args.file.suffix}' tidak didukung. Ekstensi yang didukung: {', '.join(SUPPORTED_EXTENSIONS)}",
                    file=sys.stderr,
                )
                sys.exit(1)
            args.output.mkdir(parents=True, exist_ok=True)
            files_to_process = [args.file]
            total_found = 1
        else:
            bootstrap_directories(args.input, args.output)
            # Scan files sorted ascending (ASC) and apply limit
            files_to_process, total_found = scan_images(
                args.input, recursive=args.recursive, limit=args.limit
            )

            # Step 6.2: Folder input kosong
            if not files_to_process:
                console.print(
                    Panel.fit(
                        f"[yellow]⚠️ Tidak ditemukan berkas gambar yang didukung ({', '.join(SUPPORTED_EXTENSIONS)}) pada folder '{args.input}'.[/yellow]\n"
                        f"Silakan letakkan berkas gambar Anda ke folder tersebut lalu jalankan kembali.",
                        title="[bold yellow]Informasi[/bold yellow]",
                        border_style="yellow"
                    )
                )
                sys.exit(0)

    except PermissionError as e:
        console.print(f"[bold red]Permission Error:[/bold red] {e}", file=sys.stderr)
        sys.exit(1)

    # Conversion Counters
    converted_count = 0
    skipped_count = 0
    failed_count = 0
    total_orig_size = 0
    total_new_size = 0
    claimed_destinations: Dict[Path, Path] = {}

    console.print(
        Panel.fit(
            f"[bold green]WebP Image Compressor Engine[/bold green]\n"
            f"Quality: [cyan]{args.quality}[/cyan] | Lossless: [cyan]{args.lossless}[/cyan] | Method: [cyan]{args.method}[/cyan] | Overwrite: [cyan]{args.overwrite}[/cyan]",
            border_style="green"
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("[cyan]Memproses gambar...", total=len(files_to_process))

        for file_path in files_to_process:
            progress.update(task_id, description=f"[cyan]Mengonversi: [bold]{file_path.name}[/bold]")

            dest_path, status = resolve_destination(
                source_path=file_path,
                input_base=args.input,
                output_base=args.output,
                is_single_file=(args.file is not None),
                claimed_destinations=claimed_destinations,
                overwrite=args.overwrite,
            )

            if status == "SKIPPED":
                skipped_count += 1
                progress.console.print(f"[yellow]⏩ Dilewati (sudah ada): {dest_path.name}[/yellow]")
                progress.advance(task_id)
                continue

            try:
                orig_bytes, new_bytes = convert_image_to_webp(
                    source_path=file_path,
                    destination_path=dest_path,
                    quality=args.quality,
                    lossless=args.lossless,
                    method=args.method,
                )
                converted_count += 1
                total_orig_size += orig_bytes
                total_new_size += new_bytes

            except PermissionError as e:
                failed_count += 1
                progress.console.print(f"[bold red]❌ Gagal (Akses Ditolak): {file_path.name} - {e}[/bold red]")
            except ImageConversionError as e:
                failed_count += 1
                progress.console.print(f"[bold red]❌ Gagal: {file_path.name} ({e})[/bold red]")
            except Exception as e:
                failed_count += 1
                progress.console.print(f"[bold red]❌ Gagal tak terduga: {file_path.name} ({e})[/bold red]")

            progress.advance(task_id)

    elapsed_time = time.time() - start_time
    display_summary_table(
        total_found=total_found,
        converted_count=converted_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        total_orig_size=total_orig_size,
        total_new_size=total_new_size,
        elapsed_time=elapsed_time,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
