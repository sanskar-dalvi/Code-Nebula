print("CLI script started")
import argparse
def main():
    parser = argparse.ArgumentParser(description="C# to Graph CLI Tool")
    parser.add_argument("filepath", help="Path to the C# file")
    args = parser.parse_args()
    print(f"[CLI] File path received: {args.filepath}")

if __name__ == "__main__":
    main()
