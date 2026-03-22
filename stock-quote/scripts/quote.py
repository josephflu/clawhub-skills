# /// script
# dependencies = ["rich", "httpx"]
# ///

"""
stock-quote: Real-time stock/ETF/crypto prices via Yahoo Finance.
Usage: uv run quote.py AAPL [MSFT GOOG ...] [--detail]
"""

import sys
import time
import argparse
import httpx
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text

console = Console()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}


def fetch_quote(ticker: str) -> dict | None:
    """Fetch quote data using Yahoo Finance v8 chart API (no auth required)."""
    url = (
        f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?interval=1d&range=5d&includePrePost=true"
    )
    try:
        r = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        r.raise_for_status()
        data = r.json()
        result = data.get("chart", {}).get("result")
        if not result:
            return None
        return result[0]
    except httpx.HTTPStatusError:
        return None
    except Exception:
        return None


def market_state(result: dict) -> str:
    """Determine market state from trading period timestamps."""
    meta = result.get("meta", {})
    tp = meta.get("currentTradingPeriod", {})
    now = time.time()
    regular = tp.get("regular", {})
    pre = tp.get("pre", {})
    post = tp.get("post", {})

    r_start = regular.get("start", 0)
    r_end = regular.get("end", 0)
    pre_start = pre.get("start", 0)
    pre_end = pre.get("end", 0)
    post_start = post.get("start", 0)
    post_end = post.get("end", 0)

    if r_start <= now <= r_end:
        return "REGULAR"
    elif pre_start <= now <= pre_end:
        return "PRE"
    elif post_start <= now <= post_end:
        return "POST"
    else:
        return "CLOSED"


def fmt_number(val, prefix="$", suffix=""):
    if val is None:
        return "N/A"
    if val >= 1e12:
        return f"{prefix}{val/1e12:.2f}T{suffix}"
    if val >= 1e9:
        return f"{prefix}{val/1e9:.2f}B{suffix}"
    if val >= 1e6:
        return f"{prefix}{val/1e6:.2f}M{suffix}"
    if val >= 1e3:
        return f"{prefix}{val/1e3:.1f}K{suffix}"
    return f"{prefix}{val:.2f}{suffix}"


def fmt_price(val):
    if val is None:
        return "N/A"
    if val >= 10000:
        return f"${val:,.0f}"
    if val >= 1000:
        return f"${val:,.2f}"
    return f"${val:.2f}"


def build_52w_bar(current, low, high, width=20):
    """Build a simple ASCII range bar."""
    if None in (current, low, high) or high == low:
        return "─" * width
    pct = max(0.0, min(1.0, (current - low) / (high - low)))
    pos = int(pct * width)
    bar = "─" * pos + "●" + "─" * (width - pos)
    return bar


def show_single(ticker: str, result: dict, detail: bool = False):
    meta = result.get("meta", {})

    name = meta.get("longName") or meta.get("shortName") or ticker
    exchange = meta.get("fullExchangeName", meta.get("exchangeName", ""))
    current = meta.get("regularMarketPrice")
    prev_close = meta.get("chartPreviousClose")
    volume = meta.get("regularMarketVolume")
    week52_high = meta.get("fiftyTwoWeekHigh")
    week52_low = meta.get("fiftyTwoWeekLow")
    day_high = meta.get("regularMarketDayHigh")
    day_low = meta.get("regularMarketDayLow")

    change = None
    change_pct = None
    if current is not None and prev_close is not None and prev_close != 0:
        change = current - prev_close
        change_pct = change / prev_close

    state = market_state(result)
    if state == "REGULAR":
        state_label = "[green]● Market Open[/green]"
    elif state == "PRE":
        state_label = "[yellow]● Pre-Market[/yellow]"
    elif state == "POST":
        state_label = "[cyan]● After-Hours[/cyan]"
    else:
        state_label = "[dim]● Market Closed[/dim]"

    # Price + change
    if change is not None and change >= 0:
        change_str = f"[green]▲ +{fmt_price(abs(change))[1:]} (+{change_pct*100:.2f}%)[/green]"
    elif change is not None:
        change_str = f"[red]▼ -{fmt_price(abs(change))[1:]} ({change_pct*100:.2f}%)[/red]"
    else:
        change_str = "[dim]N/A[/dim]"

    price_str = fmt_price(current)
    header = f"[bold]{name} ({ticker})[/bold]  [dim]{exchange}[/dim]"
    price_line = f"[bold white]{price_str}[/bold white]  {change_str}  {state_label}"

    # 52W range bar
    bar = build_52w_bar(current, week52_low, week52_high)
    range_line = f"52W  {fmt_price(week52_low)} [dim]{bar}[/dim] {fmt_price(week52_high)}"

    vol_str = fmt_number(volume, prefix="")
    vol_line = f"Volume  {vol_str}"

    lines = [price_line, "", range_line, vol_line]

    if detail and day_high is not None:
        lines.append(f"Day Range  {fmt_price(day_low)} – {fmt_price(day_high)}")
    if detail and prev_close is not None:
        lines.append(f"Prev Close  {fmt_price(prev_close)}")

    body = Text.from_markup("\n".join(lines))
    console.print(Panel(body, title=Text.from_markup(header), expand=False))


def show_table(tickers: list[str], quotes: dict):
    table = Table(
        title="📈 Stock Quotes",
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold white",
    )
    table.add_column("Ticker", style="bold cyan", no_wrap=True)
    table.add_column("Name", max_width=26)
    table.add_column("Price", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("% Change", justify="right")
    table.add_column("Volume", justify="right")
    table.add_column("Status", justify="center")

    for t in tickers:
        result = quotes.get(t)
        if result is None:
            table.add_row(t, "[red]Not found[/red]", "-", "-", "-", "-", "-")
            continue
        meta = result.get("meta", {})
        name = (meta.get("longName") or meta.get("shortName") or t)[:26]
        current = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose")
        volume = meta.get("regularMarketVolume")

        change = None
        change_pct = None
        if current is not None and prev_close is not None and prev_close != 0:
            change = current - prev_close
            change_pct = change / prev_close

        color = "green" if (change or 0) >= 0 else "red"
        arrow = "▲" if (change or 0) >= 0 else "▼"

        price_cell = fmt_price(current)
        change_cell = f"[{color}]{arrow} {fmt_price(abs(change or 0))[1:]}[/{color}]"
        pct_cell = f"[{color}]{(change_pct or 0)*100:+.2f}%[/{color}]"
        vol_cell = fmt_number(volume, prefix="")

        state = market_state(result)
        if state == "REGULAR":
            status = "[green]Open[/green]"
        elif state == "PRE":
            status = "[yellow]Pre[/yellow]"
        elif state == "POST":
            status = "[cyan]AH[/cyan]"
        else:
            status = "[dim]Closed[/dim]"

        table.add_row(t, name, price_cell, change_cell, pct_cell, vol_cell, status)

    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        description="Real-time stock/ETF/crypto quotes via Yahoo Finance"
    )
    parser.add_argument("tickers", nargs="+", help="Ticker symbols (e.g. AAPL BTC-USD)")
    parser.add_argument("--detail", action="store_true", help="Show extra detail")
    args = parser.parse_args()

    tickers = [t.upper() for t in args.tickers]

    if len(tickers) == 1:
        ticker = tickers[0]
        with console.status(f"Fetching {ticker}..."):
            result = fetch_quote(ticker)
        if result is None:
            console.print(f"[red]Ticker '{ticker}' not found or could not be fetched.[/red]")
            console.print("[dim]Tip: Crypto uses -USD suffix (e.g. BTC-USD)[/dim]")
            sys.exit(1)
        show_single(ticker, result, detail=args.detail)
    else:
        quotes = {}
        with console.status(f"Fetching {len(tickers)} quotes..."):
            for t in tickers:
                quotes[t] = fetch_quote(t)
        show_table(tickers, quotes)


if __name__ == "__main__":
    main()
