import argparse
from src.data.repositories import get_portfolio, get_holdings_df, write_holding
from src.logging import get_logger

_logger = get_logger(__name__)

def valid_float(value: str) -> float:
    x = float(value)
    if x < 0:
        raise argparse.ArgumentTypeError("Must be positive")
    return x

def get_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="The name of the portfolio this holding belongs to")
    parser.add_argument("ticker", help="Ticker of the holding")
    parser.add_argument("quantity", help="The quantity to add", type=valid_float)
    parser.add_argument("price", help="Price the holding was bought at", type=valid_float)
    
    return parser.parse_args()

def add_holding():
    args = get_args()
    
    name = args.name 
    ticker = args.ticker
    quantity = args.quantity
    price = args.price
    
    portfolio = get_portfolio(name=name)
    holding_df = get_holdings_df(portfolio_id=portfolio.id, ticker=ticker)
    if holding_df.empty:
        new_quantity = quantity
        new_cost_basis = price
    else:
        holding = holding_df.iloc[0]
        new_quantity = quantity+holding.quantity
        new_cost_basis = round(((holding.quantity*holding.cost_basis)+(quantity*price)) / new_quantity, 2)
        
    _logger.info(f"adding holding | new_quantity={new_quantity} new_cost_basis={new_cost_basis}")
    write_holding(portfolio_id=portfolio.id, ticker=ticker, quantity=new_quantity, cost_basis=new_cost_basis)

if __name__ == "__main__":
    add_holding()