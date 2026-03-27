#!/usr/bin/env python3
"""
Embed processed_data.json and goaling_data.json into index.html.

Replaces the GSO_DATA and goaling data blocks in the HTML file.
"""

import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, '..', '..')
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')


def main():
    # Load data
    with open(os.path.join(DATA_DIR, 'processed_data.json')) as f:
        processed = json.load(f)
    with open(os.path.join(DATA_DIR, 'goaling_data.json')) as f:
        goaling = json.load(f)
    
    goaling_meta_path = os.path.join(DATA_DIR, 'goaling_meta.json')
    if os.path.exists(goaling_meta_path):
        with open(goaling_meta_path) as f:
            goaling_meta = json.load(f)
    else:
        goaling_meta = {"quarter": "Q1 FY2026", "daysElapsed": 86, "daysInQuarter": 90, "updated": "2026-03-27"}

    # Read index.html
    html_path = os.path.join(PROJECT_DIR, 'index.html')
    with open(html_path) as f:
        html = f.read()

    # Replace GSO_DATA blob
    # Pattern: const GSO_DATA = {...};
    old_match = re.search(r'const GSO_DATA = \{.*?\};\n', html, re.DOTALL)
    if old_match:
        new_data = 'const GSO_DATA = ' + json.dumps(processed, separators=(',', ':')) + ';\n'
        html = html[:old_match.start()] + new_data + html[old_match.end():]
        print(f"Replaced GSO_DATA: {len(old_match.group(0)):,} -> {len(new_data):,} bytes")
    else:
        print("ERROR: Could not find GSO_DATA block")
        return

    # Replace goaling data block
    # Match from GSO_DATA.goaling through the closing </script> tag
    goaling_match = re.search(
        r'(GSO_DATA\.goaling = \{.*?\})\n'
        r'(GSO_DATA\.goalingMeta = \{.*?\};\n)?'
        r'</script>',
        html, re.DOTALL
    )
    if goaling_match:
        new_goaling = 'GSO_DATA.goaling = ' + json.dumps(goaling, separators=(',', ':')) + '\n'
        new_goaling += 'GSO_DATA.goalingMeta = ' + json.dumps(goaling_meta, separators=(',', ':')) + ';\n'
        new_goaling += '</script>'
        html = html[:goaling_match.start()] + new_goaling + html[goaling_match.end():]
        print(f"Replaced goaling + meta block")
    else:
        print("WARNING: Could not find goaling block")

    # Write updated index.html
    with open(html_path, 'w') as f:
        f.write(html)
    
    print(f"\nUpdated index.html: {len(html):,} bytes ({len(html)/1024:.0f} KB)")
    print(f"Line count: {html.count(chr(10))}")


if __name__ == '__main__':
    main()
