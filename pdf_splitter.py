#!/usr/bin/env python3
"""
PDF Book Splitter

Extracts text from a PDF book and splits it into sections of approximately 
4090 characters each, saving each section as a separate text file.

Usage:
    python pdf_splitter.py input.pdf [output_directory] [chars_per_section]

Requirements:
    pip install pdfplumber PyPDF2
"""

import os
import sys
import re
from pathlib import Path

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


def extract_text_with_pdfplumber(pdf_path):
    """Extract text from PDF using pdfplumber (preferred method)."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Extracting text from {total_pages} pages using pdfplumber...")
        
        for i, page in enumerate(pdf.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                if i % 10 == 0:
                    print(f"Processed {i}/{total_pages} pages...")
            except Exception as e:
                print(f"Warning: Failed to extract text from page {i}: {e}")
                continue
    
    return text


def extract_text_with_pypdf2(pdf_path):
    """Extract text from PDF using PyPDF2 (fallback method)."""
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        total_pages = len(pdf_reader.pages)
        print(f"Extracting text from {total_pages} pages using PyPDF2...")
        
        for i, page in enumerate(pdf_reader.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                if i % 10 == 0:
                    print(f"Processed {i}/{total_pages} pages...")
            except Exception as e:
                print(f"Warning: Failed to extract text from page {i}: {e}")
                continue
    
    return text


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using the best available method."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if PDFPLUMBER_AVAILABLE:
        return extract_text_with_pdfplumber(pdf_path)
    elif PYPDF2_AVAILABLE:
        return extract_text_with_pypdf2(pdf_path)
    else:
        raise ImportError("Neither pdfplumber nor PyPDF2 is available. Install with: pip install pdfplumber PyPDF2")


def clean_text(text):
    """Clean extracted text by normalizing whitespace."""
    # Replace multiple whitespace characters with single spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def split_text_into_sections(text, chars_per_section=4090):
    """
    Split text into sections of approximately chars_per_section characters each.
    Tries to break at sentence endings when possible. Allows up to 4096 characters 
    to ensure sections end at complete sentences.
    """
    sections = []
    current_section = ""
    max_chars = 4096  # Allow up to 4096 characters to end at sentence boundaries
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        # Check if adding this sentence would exceed the preferred limit
        potential_length = len(current_section) + len(sentence) + (1 if current_section else 0)
        
        if potential_length > chars_per_section and current_section:
            # If we're over the preferred limit but under the max, allow it to complete the sentence
            if potential_length <= max_chars:
                # Add sentence to current section to complete it
                if current_section:
                    current_section += " " + sentence
                else:
                    current_section = sentence
                # Save current section and start new one
                sections.append(current_section.strip())
                current_section = ""
            else:
                # If adding this sentence would exceed max limit, save current section
                sections.append(current_section.strip())
                current_section = sentence
        else:
            # Add sentence to current section
            if current_section:
                current_section += " " + sentence
            else:
                current_section = sentence
    
    # Add any remaining text as the final section
    if current_section:
        sections.append(current_section.strip())
    
    return sections


def save_sections_to_files(sections, output_dir, base_name):
    """Save each section to a separate text file."""
    os.makedirs(output_dir, exist_ok=True)
    
    total_sections = len(sections)
    digits = len(str(total_sections))
    
    for i, section in enumerate(sections, 1):
        filename = f"{base_name}_section_{str(i).zfill(digits)}.txt"
        file_path = os.path.join(output_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(section)
        
        char_count = len(section)
        print(f"Saved section {i}/{total_sections}: {filename} ({char_count} characters)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf_splitter.py input.pdf [output_directory] [chars_per_section]")
        print("Example: python pdf_splitter.py mybook.pdf ./sections 4090")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./sections"
    chars_per_section = int(sys.argv[3]) if len(sys.argv) > 3 else 4090
    
    # Get base name for output files
    base_name = Path(pdf_path).stem
    
    try:
        print(f"Processing PDF: {pdf_path}")
        print(f"Target characters per section: {chars_per_section}")
        print(f"Output directory: {output_dir}")
        print()
        
        # Extract text from PDF
        raw_text = extract_text_from_pdf(pdf_path)
        
        if not raw_text.strip():
            print("Error: No text extracted from PDF. The PDF might be image-based or corrupted.")
            sys.exit(1)
        
        # Clean the text
        cleaned_text = clean_text(raw_text)
        total_chars = len(cleaned_text)
        print(f"\nExtracted {total_chars} characters from PDF")
        
        # Split into sections
        print(f"Splitting into sections of ~{chars_per_section} characters...")
        sections = split_text_into_sections(cleaned_text, chars_per_section)
        
        print(f"Created {len(sections)} sections")
        print()
        
        # Save sections to files
        save_sections_to_files(sections, output_dir, base_name)
        
        print(f"\nCompleted! All sections saved to: {output_dir}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()