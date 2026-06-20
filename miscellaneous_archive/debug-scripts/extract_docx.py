#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from docx import Document

try:
    doc = Document('FYP Report.docx')
    
    # Extract all text from paragraphs
    text_content = []
    for para in doc.paragraphs:
        text_content.append(para.text)
    
    # Save to file with UTF-8 encoding
    with open('reports/FYP_extracted.md', 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(text_content))
    
    print("✓ Extraction complete: reports/FYP_extracted.md")
except Exception as e:
    print(f"✗ Error: {e}", file=sys.stderr)
    sys.exit(1)
