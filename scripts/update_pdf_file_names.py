#!/usr/bin/env -S uv run
import argparse
import csv
import datetime
import pathlib
import re
import shutil
from dataclasses import dataclass
from typing import Optional

import langdetect
import pdfplumber
import pytesseract
from googletrans import Translator
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)

console = Console()


@dataclass
class TitleExtractionResult:
    """Result of title extraction with metadata."""
    title: Optional[str]
    method: str
    score: float
    explanation: str
    original_text_sample: str = ""


def is_likely_title(text: str) -> bool:
    """Checks if text looks like a document title."""
    # Skip common non-title patterns
    skip_patterns = [
        r'^page\s+\d+',
        r'^\d+$',
        r'^\d+\s*of\s*\d+',
        r'^chapter\s+\d+',
        r'^section\s+\d+',
        r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # dates
        r'^[a-z]+@[a-z]+\.[a-z]+',  # emails
        r'^https?://',  # URLs
        r'^www\.',
        r'^abstract$',
        r'^introduction$',
        r'^conclusion$',
        r'^references$',
        r'^bibliography$'
    ]
    
    text_lower = text.lower().strip()
    
    # Skip if matches any skip pattern
    for pattern in skip_patterns:
        if re.search(pattern, text_lower):
            return False
    
    # Prefer longer titles (3+ words)
    word_count = len(text.split())
    if word_count < 3:
        return False
    
    # Skip very long texts (likely paragraphs)
    if len(text) > 200:
        return False
        
    # Skip texts that are mostly numbers or special characters
    alpha_ratio = sum(c.isalpha() for c in text) / len(text)
    if alpha_ratio < 0.5:
        return False
        
    return True


def extract_title_from_chars(page) -> TitleExtractionResult:
    """Extract title using font size and positioning analysis."""
    try:
        chars = page.chars
        if not chars:
            return None
            
        # Group chars by font size and get the largest
        font_sizes = {}
        for char in chars:
            size = char.get('size', 0)
            if size > 0:
                if size not in font_sizes:
                    font_sizes[size] = []
                font_sizes[size].append(char)
        
        if not font_sizes:
            return None
            
        # Sort by font size (descending)
        sorted_sizes = sorted(font_sizes.keys(), reverse=True)
        
        # Try largest font sizes first
        for size in sorted_sizes[:3]:  # Check top 3 font sizes
            chars_with_size = font_sizes[size]
            
            # Group chars into lines/words
            lines = {}
            for char in chars_with_size:
                y = round(char.get('y0', 0), 1)
                if y not in lines:
                    lines[y] = []
                lines[y].append(char)
            
            # Build text from each line
            for y_pos in sorted(lines.keys(), reverse=True):  # Top to bottom
                line_chars = sorted(lines[y_pos], key=lambda c: c.get('x0', 0))
                text = ''.join(c.get('text', '') for c in line_chars).strip()
                
                if text and is_likely_title(text):
                    score = min(0.9, 0.7 + (size / 20.0))  # Higher score for larger fonts
                    return TitleExtractionResult(
                        title=text,
                        method="font_analysis",
                        score=score,
                        explanation=f"Found via font analysis (size: {size:.1f})",
                        original_text_sample=text[:50]
                    )
                    
        return TitleExtractionResult(
            title=None,
            method="font_analysis", 
            score=0.0,
            explanation="No suitable title found via font analysis"
        )
    except Exception as e:
        return TitleExtractionResult(
            title=None,
            method="font_analysis",
            score=0.0,
            explanation=f"Font analysis failed: {str(e)}"
        )


def extract_title_from_positioned_text(page) -> TitleExtractionResult:
    """Extract title by analyzing text position (looking for centered, top text)."""
    try:
        # Get page dimensions
        page_width = page.width
        page_height = page.height
        
        # Extract text with bounding boxes
        words = page.extract_words()
        if not words:
            return None
            
        # Look for text in the top 30% of the page
        top_region_height = page_height * 0.7  # Y coordinates are from bottom in PDF
        top_words = [w for w in words if w['top'] >= top_region_height]
        
        if not top_words:
            return None
            
        # Group words by lines (similar y positions)
        lines = {}
        for word in top_words:
            y = round(word['top'], 1)
            if y not in lines:
                lines[y] = []
            lines[y].append(word)
            
        # Process each line from top to bottom
        for y_pos in sorted(lines.keys(), reverse=True):
            line_words = sorted(lines[y_pos], key=lambda w: w['x0'])
            text = ' '.join(w['text'] for w in line_words).strip()
            
            if text and is_likely_title(text):
                # Check if text is somewhat centered
                line_start = min(w['x0'] for w in line_words)
                line_end = max(w['x1'] for w in line_words)
                line_width = line_end - line_start
                line_center = line_start + (line_width / 2)
                page_center = page_width / 2
                
                # If text is within 25% of page center, prefer it
                center_tolerance = page_width * 0.25
                if abs(line_center - page_center) <= center_tolerance:
                    score = 0.8  # High score for centered text
                    return TitleExtractionResult(
                        title=text,
                        method="position_analysis_centered",
                        score=score,
                        explanation=f"Centered text in top region (y: {y_pos:.0f})",
                        original_text_sample=text[:50]
                    )
                    
        # If no centered text found, return first good title from top
        for y_pos in sorted(lines.keys(), reverse=True):
            line_words = sorted(lines[y_pos], key=lambda w: w['x0'])
            text = ' '.join(w['text'] for w in line_words).strip()
            
            if text and is_likely_title(text):
                score = 0.6  # Lower score for non-centered text
                return TitleExtractionResult(
                    title=text,
                    method="position_analysis_top",
                    score=score,
                    explanation=f"Top region text (y: {y_pos:.0f})",
                    original_text_sample=text[:50]
                )
                
        return TitleExtractionResult(
            title=None,
            method="position_analysis",
            score=0.0,
            explanation="No suitable title found via position analysis"
        )
    except Exception as e:
        return TitleExtractionResult(
            title=None,
            method="position_analysis",
            score=0.0,
            explanation=f"Position analysis failed: {str(e)}"
        )


def extract_title_fallback(text: str) -> TitleExtractionResult:
    """Fallback method: improved first-line extraction."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # Try to find a good title in the first few lines
    for i, line in enumerate(lines[:10]):  # Check first 10 lines
        if is_likely_title(line):
            if len(line) > 100:
                line = line[:100] + "..."
            score = max(0.1, 0.5 - (i * 0.05))  # Lower score for lines further down
            return TitleExtractionResult(
                title=line,
                method="fallback_validated",
                score=score,
                explanation=f"Validated title from line {i+1}",
                original_text_sample=line[:50]
            )
            
    # If no good title found, use first non-empty line as last resort
    if lines:
        title = lines[0]
        if len(title) > 100:
            title = title[:100] + "..."
        return TitleExtractionResult(
            title=title,
            method="fallback_first_line",
            score=0.1,
            explanation="Used first line as last resort",
            original_text_sample=title[:50]
        )
        
    return TitleExtractionResult(
        title=None,
        method="fallback",
        score=0.0,
        explanation="No text found for fallback extraction"
    )


def extract_title(page, text: str) -> TitleExtractionResult:
    """Main title extraction function using multiple methods."""
    results = []
    
    # Method 1: Font size analysis
    result1 = extract_title_from_chars(page)
    results.append(result1)
    if result1.title:
        console.print(f"[dim]Found title via font analysis:[/dim] '{result1.title}' (score: {result1.score:.2f})")
        return result1
        
    # Method 2: Position analysis
    result2 = extract_title_from_positioned_text(page)
    results.append(result2)
    if result2.title:
        console.print(f"[dim]Found title via position analysis:[/dim] '{result2.title}' (score: {result2.score:.2f})")
        return result2
        
    # Method 3: Improved first-line fallback
    result3 = extract_title_fallback(text)
    results.append(result3)
    if result3.title:
        console.print(f"[dim]Found title via fallback method:[/dim] '{result3.title}' (score: {result3.score:.2f})")
        return result3
        
    # Return the result with the highest score, even if title is None
    best_result = max(results, key=lambda r: r.score)
    return best_result


def format_filename(text: str) -> str:
    """Formats text into 'underline_format'."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text).strip()
    text = re.sub(r"\s+", " ", text).replace(" ", "_")
    return f"{text}.pdf"


def process_pdf(file_path: pathlib.Path) -> tuple[Optional[str], TitleExtractionResult]:
    """Extracts title, translates, and formats a new name."""
    console.print(f"[blue]Processing:[/blue] {file_path.name}")
    
    # Method 1: Use pdfplumber to extract text
    with pdfplumber.open(file_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text(x_tolerance=2, y_tolerance=2)
        
        if not text or len(text) < 10:
            # Method 2: If text extraction fails, use OCR on the first page
            console.print(f"[yellow]No text found in {file_path.name}, attempting OCR...[/yellow]")
            try:
                page_image = first_page.to_image(resolution=300)
                image_path = file_path.parent / "temp_ocr_image.png"
                page_image.save(image_path)
                text = pytesseract.image_to_string(str(image_path), lang="eng+heb")
                pathlib.Path(image_path).unlink()
            except Exception as e:
                console.print(f"[bold red]OCR failed for {file_path.name}:[/bold red] {e}")
                return None, TitleExtractionResult(
                    title=None,
                    method="ocr_failed",
                    score=0.0,
                    explanation=f"OCR failed: {str(e)}"
                )

    title_result = extract_title(first_page, text)
    if not title_result.title:
        console.print(f"[yellow]Could not extract a title from {file_path.name}.[/yellow]")
        return None, title_result
        
    title = title_result.title

    # Method 3: Check language and translate if needed
    try:
        detected_lang = langdetect.detect(title)
        if detected_lang == "he":
            console.print(f"[cyan]Translating Hebrew title from {file_path.name}:[/cyan] '{title}'")
            translator = Translator()
            translated_title = translator.translate(title, dest="en").text
            console.print(f"[cyan]Translated to:[/cyan] '{translated_title}'")
            title_result.explanation += f" | Translated from Hebrew"
            return format_filename(translated_title), title_result
        else:
            console.print(f"[magenta]Using English title from {file_path.name}:[/magenta] '{title}'")
            return format_filename(title), title_result
    except Exception as e:
        console.print(f"[bold red]Translation/Language detection failed for {file_path.name}:[/bold red] {e}")
        title_result.explanation += f" | Translation failed: {str(e)}"
        return format_filename(title), title_result


def copy_and_rename_file(old_path: pathlib.Path, new_name: str, output_path: pathlib.Path) -> None:
    """Copies the original file to the new location with the new name."""
    new_path = output_path / new_name
    console.print(f"[green]Renaming[/green] '{old_path.name}' -> '{new_name}'")
    shutil.copy2(old_path, new_path)


def write_processing_log(log_entries: list, output_path: pathlib.Path):
    """Write processing log to CSV file."""
    log_file = output_path / f"pdf_rename_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['original_name', 'transformed_name', 'score', 'method', 'explanation', 'status', 'original_text_sample']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for entry in log_entries:
            writer.writerow(entry)
    
    console.print(f"[bold blue]Log saved to:[/bold blue] {log_file}")


def main():
    parser = argparse.ArgumentParser(description="Rename PDF files based on their content")
    parser.add_argument("input_dir", help="Input directory containing PDF files")
    parser.add_argument("output_dir", help="Output directory for renamed PDF files")
    parser.add_argument("--num_files", type=int, default=5, 
                       help="Number of files to process (default: 5, -1 for all)")
    
    args = parser.parse_args()
    
    # Convert to pathlib paths
    input_path = pathlib.Path(args.input_dir)
    output_path = pathlib.Path(args.output_dir)
    
    # Validate input directory
    if not input_path.exists() or not input_path.is_dir():
        console.print("[bold red]Error:[/bold red] Input directory does not exist or is not a directory.")
        return 1
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find PDF files
    pdf_files = sorted(list(input_path.glob("*.pdf")))
    
    if not pdf_files:
        console.print("[bold red]Error:[/bold red] No PDF files found in input directory.")
        return 1
    
    # Apply file limit
    if args.num_files != -1:
        pdf_files = pdf_files[:args.num_files]
    
    console.print(f"[bold]Found {len(pdf_files)} PDF files to process[/bold]")
    console.print(f"[bold]Output directory:[/bold] {output_path}")
    
    # Process files with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[green]Processing files...", total=len(pdf_files))
        
        processed = 0
        skipped = 0
        log_entries = []
        
        for file_path in pdf_files:
            try:
                new_name, title_result = process_pdf(file_path)
                log_entry = {
                    'original_name': file_path.name,
                    'transformed_name': new_name or "SKIPPED",
                    'score': title_result.score,
                    'method': title_result.method,
                    'explanation': title_result.explanation,
                    'original_text_sample': title_result.original_text_sample,
                    'status': 'success' if new_name else 'skipped'
                }
                log_entries.append(log_entry)
                
                if new_name:
                    copy_and_rename_file(file_path, new_name, output_path)
                    processed += 1
                else:
                    console.print(f"[yellow]Skipped:[/yellow] Could not find a suitable title for '{file_path.name}'.")
                    skipped += 1
            except Exception as e:
                console.print(f"[bold red]Error processing {file_path.name}:[/bold red] {e}")
                log_entry = {
                    'original_name': file_path.name,
                    'transformed_name': "ERROR",
                    'score': 0.0,
                    'method': 'error',
                    'explanation': str(e),
                    'original_text_sample': '',
                    'status': 'error'
                }
                log_entries.append(log_entry)
                skipped += 1
            
            progress.advance(task)
            
        # Write processing log
        write_processing_log(log_entries, output_path)
    
    console.print(f"[bold green]Processing complete![/bold green] Processed: {processed}, Skipped: {skipped}")
    console.print(f"[bold]Renamed PDFs saved to:[/bold] {output_path}")
    console.print("[bold]Processing log saved to output directory[/bold]")
    return 0


if __name__ == "__main__":
    exit(main())