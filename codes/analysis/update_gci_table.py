#!/usr/bin/env python3
"""Update the GCI table in main.tex with actual mesh independence results."""
import json
import sys
from pathlib import Path

def main():
    results_file = Path(__file__).parent.parent / 'results' / 'openfoam_results.json'
    tex_file = Path(__file__).parent.parent.parent / 'manuscript' / 'main.tex'

    if not results_file.exists():
        print("ERROR: openfoam_results.json not found. Run postprocess_openfoam.py first.")
        return

    with open(results_file) as f:
        results = json.load(f)

    gci = results.get('gci', {})
    mesh_results = results.get('mesh_independence', [])

    if not gci:
        print("ERROR: No GCI data in results file.")
        return

    # Extract values for each quantity (handle both 2-level and 3-level)
    rows = []

    def fmt_vals(vals, fmt_str):
        """Format values, padding to 3 entries if needed."""
        while len(vals) < 3:
            vals.append(None)
        return [fmt_str.format(v) if v is not None else '---' for v in vals]

    # Row 1: u*_upstream (simulated)
    q = gci.get('ustar_upstream', {})
    if q:
        vals = q.get('values', [])
        gci_pct = q.get('gci_fine_pct', 0)
        fv = fmt_vals(list(vals), '{:.4f}')
        rows.append((r'$u_{*,\text{ref}}$ [m/s]', fv[0], fv[1], fv[2],
                     f'{gci_pct:.1f}'))

    # Row 2: Shelter efficiency
    q = gci.get('shelter_efficiency', {})
    if q:
        vals = q.get('values', [])
        gci_pct = q.get('gci_fine_pct', 0)
        fv = fmt_vals(list(vals), '{:.3f}')
        rows.append(('Shelter efficiency', fv[0], fv[1], fv[2],
                     f'{gci_pct:.1f}'))

    # Row 3: u* amplification max
    q = gci.get('ustar_amp_max', {})
    if q:
        vals = q.get('values', [])
        gci_pct = q.get('gci_fine_pct', 0)
        fv = fmt_vals(list(vals), '{:.3f}')
        rows.append((r'$u_*/u_{*,\text{ref}}$ (max)', fv[0], fv[1], fv[2],
                     f'{gci_pct:.1f}'))

    if not rows:
        print("ERROR: Could not extract GCI quantities.")
        return

    # Build the LaTeX table body
    table_lines = []
    for name, c, m, f, gci_val in rows:
        table_lines.append(f'    {name} & {c} & {m} & {f} & {gci_val} \\\\')

    table_body = '\n'.join(table_lines)

    # Read the tex file and replace the placeholder table
    tex = tex_file.read_text()

    # Find and replace the placeholder rows
    old_rows = (
        r'    $u_{*,\text{ref}}$ [m/s]           & ---   & ---  & ---  & --- \\' + '\n'
        r'    Shelter efficiency                  & ---   & ---  & ---  & --- \\' + '\n'
        r'    $u_*/u_{*,\text{ref}}$ (max)       & ---   & ---  & ---  & --- \\'
    )

    if old_rows in tex:
        tex = tex.replace(old_rows, table_body)
        tex_file.write_text(tex)
        print("GCI table updated in main.tex")
        for row in rows:
            print(f"  {row[0]}: {row[1]} / {row[2]} / {row[3]} | GCI={row[4]}%")
    else:
        print("WARNING: Could not find placeholder rows in main.tex")
        print("Table body would be:")
        print(table_body)


if __name__ == '__main__':
    main()
