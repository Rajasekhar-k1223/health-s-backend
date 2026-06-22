import re
import glob
import os

SRC_DIR = r'd:/healthai-project/healt-s/sentinel-core-health/src/routes'
IMPORT_LINE = 'import { apiFetch } from "@/lib/api-fetch";\n'

files = glob.glob(os.path.join(SRC_DIR, '*.tsx'))
patched = 0

for fpath in files:
    with open(fpath, encoding='utf-8') as f:
        content = f.read()

    # Only touch files that have raw localhost fetch calls
    if 'fetch(`http://localhost:8000' not in content and 'fetch("http://localhost:8000' not in content:
        continue

    original = content

    # 1. Add apiFetch import after the first import line if not already present
    if 'api-fetch' not in content:
        first_import_end = content.index('\n') + 1
        content = content[:first_import_end] + IMPORT_LINE + content[first_import_end:]

    # 2. Replace backtick template literal calls
    content = re.sub(
        r'\bfetch\(`http://localhost:8000(/[^`]*)`',
        r'apiFetch(`\1`',
        content
    )
    # 3. Replace double-quote calls  
    content = re.sub(
        r'\bfetch\("http://localhost:8000(/[^"]*)"',
        r'apiFetch("\1"',
        content
    )

    # 4. Remove inline Authorization headers already replaced by apiFetch
    content = re.sub(
        r',?\s*headers:\s*\{\s*Authorization:\s*`Bearer \$\{localStorage\.getItem\("access_token"\)\}`\s*\}',
        '',
        content
    )
    # Also remove standalone Authorization in headers objects
    content = re.sub(
        r',?\s*Authorization:\s*`Bearer \$\{localStorage\.getItem\("access_token"\)\}`',
        '',
        content
    )

    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Patched: {os.path.basename(fpath)}')
        patched += 1

print(f'\nTotal files patched: {patched}')
