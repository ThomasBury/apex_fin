import yfinance as yf
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def validate_and_get_ticker(user_input: str) -> Optional[tuple[str, str]]:
    """
    Validates user input to find a corresponding Yahoo Finance ticker.

    This function takes a user-provided string, which could be a company
    name or a ticker symbol, and uses the yfinance search feature to
    find the most likely ticker.

    Args:
        user_input: The company name or ticker symbol to validate.

    Returns:
        The validated Yahoo Finance ticker symbol and company name as a string,
        or None if no valid ticker is found.
    """
    # Validation check
    if not isinstance(user_input, str) or not user_input.strip():
        logger.error("Validation Error: Input must be a non-empty string")
        return None

    try:
        # Perform search with expanded results
        search_results = yf.Search(user_input.strip(), max_results=5).quotes
        
        if not search_results:
            logger.warning(f"No results found for '{user_input}'")
            return None

        # Get the best match
        best_match = search_results[0]
        ticker = best_match.get('symbol', '').strip()
        company_name = best_match.get('longname', '').strip() or best_match.get('shortname', '').strip()

        if not ticker:
            logger.warning(f"Valid ticker not found in results for '{user_input}'")
            return None

        logger.info(f"Found '{ticker} - {company_name}' for '{user_input}'")
        return (ticker, company_name)

    except Exception as e:
        logger.error(f"Search failed for '{user_input}': {str(e)}", exc_info=True)
        return None

# Example Usage
if __name__ == "__main__":
    # Example 1: Using a company name
    print("Searching for a company name...")
    company_name = "BYD Company"
    # For standalone testing, configure basic logging
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO)

    validated_ticker = validate_and_get_ticker(company_name)
    if validated_ticker:
        # You can now use this ticker with other yfinance functions
        stock_data = yf.Ticker(validated_ticker[0]).info
        print(f"Successfully fetched data for {stock_data.get('longName', validated_ticker[0])}")
    else:
        print(f"Could not validate ticker for {company_name}")
    print("\n" + "="*40 + "\n")

    # # Example 2: Using a common but potentially unformatted ticker
    # print("Searching for a common symbol...")
    # common_ticker = "aapl" # Lowercase
    # validated_ticker_aapl = validate_and_get_ticker(common_ticker)
    # if validated_ticker_aapl:
    #     stock_data = yf.Ticker(validated_ticker_aapl).info
    #     print(f"Successfully fetched data for {stock_data.get('longName', validated_ticker_aapl)}")

    # print("\n" + "="*40 + "\n")

    # # Example 3: Handling an invalid input
    # print("Searching for invalid input...")
    # invalid_input = "Not A Real Company Inc"
    # validated_ticker_invalid = validate_and_get_ticker(invalid_input)
    # if not validated_ticker_invalid:
    #     print("As expected, no data could be fetched.")