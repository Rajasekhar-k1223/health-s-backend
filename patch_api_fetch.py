import re

FILES = [
    r'd:/healthai-project/healt-s/sentinel-core-health/src/routes/documents.tsx',
    r'd:/healthai-project/healt-s/sentinel-core-health/src/routes/documents.index.tsx',
]

IMPORT_LINE = 'import { apiFetch } from "@/lib/api-fetch";\n'

for fpath in FILES:
    with open(fpath, encoding='utf-8') as f:
        content = f.read()

    # 1. Add apiFetch import after the first import line if not already present
    if 'api-fetch' not in content:
        first_import_end = content.index('\n') + 1
        content = content[:first_import_end] + IMPORT_LINE + content[first_import_end:]

    # 2. Replace fetch(`http://localhost:8000/... with apiFetch(`/...
    content = re.sub(
        r'\bfetch\(`http://localhost:8000(/[^`]*)`',
        r'apiFetch(`\1`',
        content
    )
    # Also handle fetch("http://localhost:8000/...
    content = re.sub(
        r'\bfetch\("http://localhost:8000(/[^"]*)"',
        r'apiFetch("\1"',
        content
    )

    # 3. Remove manual Authorization headers that apiFetch now handles
    #    Pattern: headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
    content = re.sub(
        r'\s*headers:\s*\{\s*Authorization:\s*`Bearer \$\{localStorage\.getItem\("access_token"\)\}`\s*\},\n',
        '\n',
        content
    )

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Patched: {fpath}')
