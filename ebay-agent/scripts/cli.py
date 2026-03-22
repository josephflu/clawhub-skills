#!/usr/bin/env python3
"""
ebay-agent CLI entry point.

Usage:
    uv run --project <skill_dir> python <skill_dir>/scripts/cli.py search "Sony 85mm lens"
    uv run --project <skill_dir> python <skill_dir>/scripts/cli.py value "iPhone 15 Pro"
    uv run --project <skill_dir> python <skill_dir>/scripts/cli.py prefs
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import argparse


def cmd_search(args):
    from search import search_items
    from preferences import UserPreferences
    from scoring import rank_results

    prefs = UserPreferences()
    try:
        items = search_items(args.query, prefs)
        ranked = rank_results(items, prefs)
        if not ranked:
            print("No results found.")
            return
        try:
            from rich.table import Table
            from rich.console import Console
            console = Console()
            table = Table(title=f"Search: {args.query}")
            table.add_column("Title", max_width=40)
            table.add_column("Price", justify="right")
            table.add_column("Condition")
            table.add_column("Score", justify="right")
            for item in ranked[:10]:
                table.add_row(
                    item.get("title", "")[:40],
                    f"${item.get('total_price', 0):.2f}",
                    item.get("condition", ""),
                    str(item.get("score", "")),
                )
            console.print(table)
        except ImportError:
            for item in ranked[:10]:
                print(f"{item.get('title', '')[:50]} | ${item.get('total_price', 0):.2f} | score={item.get('score', '')}")
    except Exception as e:
        print(f"Search failed: {e}")


def cmd_value(args):
    from valuation import get_valuation
    from preferences import UserPreferences

    prefs = UserPreferences()
    try:
        result = get_valuation(args.query, prefs)
        print(f"Valuation for '{args.query}':")
        for k, v in result.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"Valuation failed: {e}")


def cmd_prefs(args):
    from preferences import UserPreferences
    prefs = UserPreferences()
    print("Current preferences:")
    for k, v in vars(prefs).items():
        print(f"  {k}: {v}")


def main():
    parser = argparse.ArgumentParser(prog="ebay-agent", description="eBay search and valuation agent")
    subparsers = parser.add_subparsers(dest="command")

    p_search = subparsers.add_parser("search", help="Search eBay listings")
    p_search.add_argument("query", help="Search query")

    p_value = subparsers.add_parser("value", help="Get market valuation")
    p_value.add_argument("query", help="Item to value")

    subparsers.add_parser("prefs", help="Show current preferences")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args)
    elif args.command == "value":
        cmd_value(args)
    elif args.command == "prefs":
        cmd_prefs(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
