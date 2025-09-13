#!/usr/bin/env python3
"""Fix Pydantic v1 Config to v2 ConfigDict migration"""

import re
import os
import glob

def fix_config_in_file(filepath):
    """Fix Config class to ConfigDict in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix the pattern: model_config = ConfigDict(\n        """..."""\n\n        json_schema_extra = {
    pattern1 = re.compile(
        r'model_config = ConfigDict\(\n\s*"""[^"]*"""\n\n\s*json_schema_extra = \{',
        re.MULTILINE
    )
    content = pattern1.sub('model_config = ConfigDict(\n        json_schema_extra={', content)

    # Fix the closing pattern: }\n (but only for ConfigDict blocks)
    # Find all ConfigDict blocks and fix their closing
    pattern2 = re.compile(
        r'(model_config = ConfigDict\([^}]+\})\n([^)]*$)',
        re.MULTILINE | re.DOTALL
    )

    def replace_closing(match):
        config_block = match.group(1)
        remaining = match.group(2)

        # If remaining content doesn't start with ), add the closing
        if not remaining.strip().startswith(')'):
            return config_block + '\n    )\n' + remaining
        return match.group(0)

    content = pattern2.sub(replace_closing, content)

    # Simple fix for any remaining ConfigDict without proper closing
    lines = content.split('\n')
    fixed_lines = []
    in_config_dict = False
    config_dict_indent = 0

    for i, line in enumerate(lines):
        if 'model_config = ConfigDict(' in line:
            in_config_dict = True
            config_dict_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
        elif in_config_dict:
            # Look for the end of the json_schema_extra dict
            if line.strip() == '}' and len(line) - len(line.lstrip()) == config_dict_indent + 8:
                fixed_lines.append(line)
                # Add closing parenthesis if next line doesn't have it
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith(')'):
                    fixed_lines.append(' ' * config_dict_indent + ')')
                in_config_dict = False
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    fixed_content = '\n'.join(fixed_lines)

    # Write back if changed
    if content != fixed_content:
        with open(filepath, 'w') as f:
            f.write(fixed_content)
        print(f"Fixed: {filepath}")
    else:
        print(f"No changes needed: {filepath}")

def main():
    """Fix all model files"""
    model_files = glob.glob("src/scraper_core/models/*.py")
    for filepath in model_files:
        if not filepath.endswith("__init__.py"):
            fix_config_in_file(filepath)

if __name__ == "__main__":
    main()