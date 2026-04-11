#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

import requests


def download_file(url: str, out_path: Path, overwrite: bool) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not overwrite:
        print(f"Skipping existing file (use --overwrite to replace): {out_path}")
        return

    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with out_path.open("wb") as file_obj:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file_obj.write(chunk)

    print(f"Downloaded: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download raw data files from provided URLs.")
    parser.add_argument("--qcew-url", type=str, default="")
    parser.add_argument("--qcew-out", type=Path, default=Path("data/raw/qcew_county.csv"))
    parser.add_argument("--ipeds-url", type=str, default="")
    parser.add_argument("--ipeds-out", type=Path, default=Path("data/raw/ipeds_institutions.csv"))
    parser.add_argument("--metro-url", type=str, default="")
    parser.add_argument("--metro-out", type=Path, default=Path("data/raw/metro_crosswalk.csv"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.qcew_url:
        download_file(args.qcew_url, args.qcew_out, args.overwrite)
    if args.ipeds_url:
        download_file(args.ipeds_url, args.ipeds_out, args.overwrite)
    if args.metro_url:
        download_file(args.metro_url, args.metro_out, args.overwrite)

    if not any([args.qcew_url, args.ipeds_url, args.metro_url]):
        print("No URLs were provided. Nothing downloaded.")


if __name__ == "__main__":
    main()
