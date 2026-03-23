#!/usr/bin/env python3
"""
ebay-agent CLI entry point.

Usage:
    uv run --project <skill_dir> ebay-agent search "Sony 85mm lens"
    uv run --project <skill_dir> ebay-agent value "iPhone 15 Pro"
    uv run --project <skill_dir> ebay-agent prefs
"""

import argparse
import json


def cmd_search(args):
    from .search import search_items
    from .preferences import load_preferences
    from .scoring import rank_results

    prefs = load_preferences()
    if args.max_price:
        prefs.budget_default = args.max_price

    try:
        items = search_items(
            args.query,
            max_price=args.max_price,
            condition=args.condition,
            limit=args.limit,
        )
        if not items:
            print("No results found on eBay.")
            return
        ranked = rank_results(items, prefs)
        if not ranked:
            print(f"Found {len(items)} listings but all filtered out by preferences (min seller score: {prefs.min_seller_score}%, min condition: {prefs.min_condition}). Try: ebay-agent prefs")
            return

        # Apply sort override
        if args.sort == "price":
            ranked.sort(key=lambda x: x["total_price"])
        elif args.sort == "seller":
            ranked.sort(key=lambda x: float(x.get("seller_feedback_pct") or 0), reverse=True)

        if args.json:
            print(json.dumps(ranked[:args.limit], indent=2))
            return

        try:
            from rich.table import Table
            from rich.console import Console
            console = Console()
            table = Table(title=f"Search: {args.query}")
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", max_width=38)
            table.add_column("Price", justify="right")
            table.add_column("Condition")
            table.add_column("Score", justify="right")
            table.add_column("Link", style="dim blue")
            for i, item in enumerate(ranked[:args.limit], 1):
                url = item.get("item_url", "")
                table.add_row(
                    str(i),
                    item.get("title", "")[:38],
                    f"${item.get('total_price', 0):.2f}",
                    item.get("condition", ""),
                    str(item.get("score", "")),
                    f"[link={url}]view[/link]" if url else "",
                )
            console.print(table)
        except ImportError:
            for i, item in enumerate(ranked[:args.limit], 1):
                url = item.get("item_url", "")
                print(f"{i}. {item.get('title', '')[:50]} | ${item.get('total_price', 0):.2f} | {url}")
    except Exception as e:
        print(f"Search failed: {e}")


def cmd_value(args):
    from .valuation import get_valuation

    from .valuation import CONDITION_ADJUSTMENTS

    try:
        result = get_valuation(args.query, condition=args.condition, limit=args.limit)
        if result["count"] == 0:
            print(f"No results found for '{args.query}'.")
            return
        if args.json:
            print(json.dumps(result, indent=2))
            return
        adj_pct = CONDITION_ADJUSTMENTS.get(args.condition.lower(), 0.8)
        print(f"Valuation for '{args.query}' (condition: {args.condition}):")
        print(f"  Average:           ${result['avg']:.2f}")
        print(f"  Median:            ${result['median']:.2f}")
        print(f"  Range:             ${result['min']:.2f} - ${result['max']:.2f}")
        print(f"  Listings analyzed: {result['count']}")
        print(f"  Source:            {result['source']}")
        print(f"  Condition adj:     {args.condition} ({adj_pct:.0%} of avg = ${result['adjusted_avg']:.2f})")
        print(f"  Recommended price: ${result['recommended_price']:.2f}")
    except Exception as e:
        print(f"Valuation failed: {e}")


def cmd_prefs(args):
    from .preferences import load_preferences
    prefs = load_preferences()
    print("Current preferences:")
    for k, v in vars(prefs).items():
        print(f"  {k}: {v}")


def main():
    parser = argparse.ArgumentParser(prog="ebay-agent", description="eBay search and valuation agent")
    subparsers = parser.add_subparsers(dest="command")

    p_search = subparsers.add_parser("search", help="Search eBay listings")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--max-price", "-p", type=float, default=None, help="Maximum price in USD")
    p_search.add_argument("--condition", "-c", default=None, help="Condition: new, used, very_good, good, acceptable")
    p_search.add_argument("--limit", "-n", type=int, default=10, help="Number of results (default: 10)")
    p_search.add_argument("--sort", "-s", choices=["score", "price", "seller"], default="score", help="Sort order (default: score)")
    p_search.add_argument("--json", action="store_true", help="Output results as JSON")

    p_value = subparsers.add_parser("value", help="Get market valuation")
    p_value.add_argument("query", help="Item to value")
    p_value.add_argument("--condition", "-c", default="used", help="Condition (default: used)")
    p_value.add_argument("--limit", "-n", type=int, default=20, help="Listings to analyze (default: 20)")
    p_value.add_argument("--json", action="store_true", help="Output results as JSON")

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
