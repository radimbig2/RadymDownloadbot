import argparse
import base64
import sys
from pathlib import Path


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


def load_cookie_text(input_path: Path) -> str:
    if not input_path.exists():
        raise FileNotFoundError(f"Cookies file not found: {input_path}")

    cookie_text = input_path.read_text(encoding="utf-8").strip()
    if not cookie_text:
        raise ValueError("Cookies file is empty")

    if "youtube.com" not in cookie_text and "google.com" not in cookie_text:
        print(
            "Warning: the file does not look like YouTube/Google cookies. Continuing anyway.",
            file=sys.stderr,
        )

    return cookie_text


def main() -> int:
    args = build_parser().parse_args()
    input_path = Path(args.input_file)

    try:
        cookie_text = load_cookie_text(input_path)
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