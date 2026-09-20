"""Read-only inventory for the 2.34 Change proposal terminology upgrade.

Legacy CR IDs, directories, statuses, links and history need no rewrite.
Run against a stopped engagement mounted read-only; review the output locally.
"""
import argparse
from pathlib import Path

import items
import model as M


def inspect(engagement):
    root = Path(engagement)
    if not (root / "engagement.md").is_file():
        raise ValueError("Expected an engagement folder containing engagement.md")
    proposals, errors = [], []
    seen = set()
    for path in sorted((root / M.DIRS["CR"]).glob("*.md")):
        try:
            item = items.parse_item(path)
            if item["kind"] != "CR" or path.stem != item["id"] or item["id"] in seen:
                raise ValueError("invalid, duplicate or mismatched CR ID")
            seen.add(item["id"])
            if item["status"] not in M.STATES["CR"]:
                raise ValueError("unrecognised status: " + item["status"])
            proposals.append(item)
        except (KeyError, ValueError, OSError) as exc:
            errors.append(f"{path.name}: {exc}")
    return proposals, errors


def report(proposals, errors):
    lines = [f"Change proposal upgrade to model {M.MODEL_VERSION}",
             "Read-only: no item, link, history, saved view or engagement setting is changed.",
             f"{len(proposals)} existing CR records load as Change proposals. Keep their IDs and change-requests folder.",
             "Submitted and LIM Change requested remain valid stored statuses.", ""]
    for item in proposals:
        lines += [f"{item['id']} | {item['title']} | {item['status']}",
                  f"  Scope: {item.get('scope') or 'Not set'}; Phase: {item.get('phase') or 'Not set'}",
                  f"  Estimate: {item.get('estimate') or 'Not sized'}",
                  f"  Vendor ref: {item.get('vendor-ref') or 'Not recorded (may not exist yet)'}",
                  f"  Source: {item.get('source') or 'Missing'}",
                  "  Review: Source must link to the solution design/section. Check estimate basis (Indicative or Confirmed), source and date."]
    lines += ["", "Review missing facts in Rationalise using evidence. Do not infer approvals, estimates or vendor references.",
              "The separate ingester has not been ported by this upgrade; retain its existing declared version."]
    lines += ["ERROR: " + error for error in errors]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engagement")
    args = parser.parse_args()
    try:
        proposals, errors = inspect(args.engagement)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(report(proposals, errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
