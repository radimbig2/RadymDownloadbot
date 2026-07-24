import argparse
import base64
import sys
from pathlib import Path


def filter_cookie_text(cookie_text: str, expected_domains: tuple[str, ...]) -> str:
    filtered_lines = []
    matched_cookies = 0

    for line in cookie_text.splitlines():
        stripped = line.strip()
        if not stripped or (
            stripped.startswith("#") and not stripped.startswith("#HttpOnly_")
        ):
            filtered_lines.append(line)
            continue

        parts = stripped.split("\t")
        if len(parts) < 7:
            continue

        domain = parts[0].removeprefix("#HttpOnly_").lstrip(".").lower()
        if any(
            domain == expected or domain.endswith(f".{expected}")
            for expected in expected_domains
        ):
            filtered_lines.append(line)
            matched_cookies += 1

    if not matched_cookies:
        raise ValueError(
            "No cookies for the requested platform were found in the export"
        )

    return "\n".join(filtered_lines).strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a Netscape cookies.txt file into a YTDLP_COOKIES_BASE64 env line."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="cookies.txt",
        help="Path to the source cookies.txt file. Default: cookies.txt",
    )
    parser.add_argument(
        "--var-name",
        default="YTDLP_COOKIES_BASE64",
        help="Environment variable name to print. Default: YTDLP_COOKIES_BASE64",
    )
    parser.add_argument(
        "--output",
        help="Optional path to save the generated env line instead of printing it.",
    )
    return parser


def load_cookie_text(input_path: Path, var_name: str) -> str:
    if not input_path.exists():
        raise FileNotFoundError(f"Cookies file not found: {input_path}")

    cookie_text = input_path.read_text(encoding="utf-8").strip()
    if not cookie_text:
        raise ValueError("Cookies file is empty")

    if var_name.startswith("INSTAGRAM_"):
        expected_domains = ("instagram.com",)
        platform = "Instagram"
    elif var_name.startswith("TIKTOK_"):
        expected_domains = ("tiktok.com",)
        platform = "TikTok"
    else:
        expected_domains = ("youtube.com", "google.com")
        platform = "YouTube/Google"
    try:
        return filter_cookie_text(cookie_text, expected_domains)
    except ValueError as exc:
        raise ValueError(f"{platform}: {exc}") from exc


def main() -> int:
    args = build_parser().parse_args()
    input_path = Path(args.input_file)

    try:
        cookie_text = load_cookie_text(input_path, args.var_name)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    encoded = base64.b64encode(cookie_text.encode("utf-8")).decode("ascii")
    env_line = f"{args.var_name}={encoded}"

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(env_line + "\n", encoding="utf-8")
        print(f"Saved env line to {output_path}")
    else:
        print(env_line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
