"""Expose JUnit failures as Actions annotations without a third-party action."""

import sys
from pathlib import Path
from xml.etree import ElementTree


def escape(value):
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def main():
    path = Path(sys.argv[1])
    if not path.exists():
        print("::warning::pytest did not produce its JUnit report; inspect the preceding step.")
        return
    root = ElementTree.parse(path).getroot()
    for case in root.iter("testcase"):
        for problem in case:
            if problem.tag not in {"failure", "error"}:
                continue
            title = escape(f"{case.get('classname', '')}.{case.get('name', '')}")
            title = title.replace(":", "%3A").replace(",", "%2C")
            message = escape((problem.text or problem.get("message", ""))[:6000])
            print(f"::error title={title}::{message}")


if __name__ == "__main__":
    main()
