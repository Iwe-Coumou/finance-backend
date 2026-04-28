import argparse
from src.data.repositories import write_portfolio

def add_portfolio():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Name of portfolio")
    parser.add_argument("source", help="Platform of the portfolio (e.g., DEGIRO)")
    
    args = parser.parse_args()   
    name = args.name
    source = args.source
    
    write_portfolio(name=name, source=source)

if __name__ == "__main__":
    add_portfolio()