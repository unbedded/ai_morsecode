#!/usr/bin/env python3
"""yaml_to_py.py — Convert a YAML payload with a single 'py' string field into a .py file.

Usage:
  python tools/yaml_to_py.py input.yaml output.py
"""
import sys
import pathlib
import yaml  # requires PyYAML

def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python tools/yaml_to_py.py <input.yaml> <output.py>", file=sys.stderr)
        return 2
    in_path = pathlib.Path(sys.argv[1])
    out_path = pathlib.Path(sys.argv[2])
    if not in_path.exists():
        print(f"Input YAML not found: {in_path}", file=sys.stderr)
        return 1
    data = yaml.safe_load(in_path.read_text(encoding='utf-8')) or {}
    if 'py' not in data or not isinstance(data['py'], str):
        print("YAML must contain a 'py' string field.", file=sys.stderr)
        return 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(data['py'], encoding='utf-8')
    print(f"Wrote {out_path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
