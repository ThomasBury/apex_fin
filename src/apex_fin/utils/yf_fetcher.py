# import json
# import yfinance as yf
# import pandas as pd
# import numpy as np
# import datetime as dt 

# class YFinanceFinancialAnalyzer:
#     """
#     A class to fetch and structure comprehensive financial data for a stock symbol
#     (including common stocks and ETFs/funds) from Yahoo Finance, optimized for a
#     single API interaction per data pull and formatted for LLM consumption.
#     """

#     NA_VALUE = "N/A"
#     DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
#     DATE_FORMAT = '%Y-%m-%d'
#     PERCENT_FORMAT = "{:.2%}" # percentages

#     def __init__(self, symbol: str):
#         if not symbol or not isinstance(symbol, str):
#             raise ValueError("A valid stock symbol string must be provided.")
#         self.symbol = symbol.upper()
#         try:
#             self.ticker = yf.Ticker(self.symbol)
#             self._info_cache = self.ticker.info
#             if not self._info_cache:
#                 print(f"Warning: .info for {self.symbol} is empty or could not be fetched. Data might be limited or the ticker may be invalid.")
#                 self._info_cache = {}
#         except Exception as e:
#             raise RuntimeError(f"Failed to initialize yfinance.Ticker or fetch initial info for {self.symbol}: {e}")

#     def _get_ticker_info(self):
#         return self._info_cache if self._info_cache is not None else {}

#     def _process_value(self, value, is_percentage=False):
#         if isinstance(value, (dt.datetime, pd.Timestamp)):
#             return value.strftime(self.DATETIME_FORMAT)
#         if isinstance(value, dt.date):
#             return value.strftime(self.DATE_FORMAT)
#         if pd.isna(value) or value is None:
#             return self.NA_VALUE
#         if is_percentage and isinstance(value, (float, int, np.floating, np.integer)):
#             try:
#                 return self.PERCENT_FORMAT.format(value)
#             except (TypeError, ValueError):
#                 pass # Fall through to default processing if format fails
#         if isinstance(value, np.integer):
#             return int(value)
#         if isinstance(value, np.floating):
#             return float(value)
#         if isinstance(value, (dict, list)) and not value:
#              return self.NA_VALUE
#         return value

#     def _safe_get_from_info(self, key: str, is_percentage=False):
#         info_dict = self._get_ticker_info()
#         raw_val = info_dict.get(key)

#         date_timestamp_keys = [
#             "exDividendDate", "lastDividendDate", "lastSplitDate",
#             "firstTradeDateEpochUtc", "earningsTimestamp",
#             "earningsTimestampStart", "earningsTimestampEnd", "mostRecentQuarter"
#         ]

#         if key in date_timestamp_keys:
#             if isinstance(raw_val, (int, float)) and not pd.isna(raw_val) and raw_val != 0:
#                 try:
#                     return dt.datetime.fromtimestamp(raw_val, dt.timezone.utc).strftime(self.DATE_FORMAT)
#                 except (TypeError, ValueError, OSError):
#                     return str(raw_val)
#             return self.NA_VALUE

#         return self._process_value(raw_val, is_percentage=is_percentage)

#     def _format_dataframe(self, df: pd.DataFrame, orient='records', max_rows=None,
#                           date_columns_to_format=None, index_as_date_column_name=None,
#                           percentage_columns=None):
#         if df is None or df.empty:
#             return [] if orient == 'records' else {}

#         df_copy = df.copy()
#         if max_rows: df_copy = df_copy.head(max_rows)

#         if index_as_date_column_name and isinstance(df_copy.index, pd.DatetimeIndex):
#             df_copy = df_copy.reset_index()
#             new_col_name = index_as_date_column_name
#             current_cols = df_copy.columns.tolist()
#             if 'index' in current_cols and df_copy.index.name is None:
#                 df_copy.rename(columns={'index': new_col_name}, inplace=True)
#             elif df_copy.index.name in current_cols:
#                 df_copy.rename(columns={df_copy.index.name: new_col_name}, inplace=True)
            
#             if new_col_name in df_copy.columns:
#                 if date_columns_to_format is None: date_columns_to_format = {}
#                 if new_col_name not in date_columns_to_format:
#                     date_columns_to_format[new_col_name] = self.DATETIME_FORMAT

#         if date_columns_to_format:
#             for col, fmt_str in date_columns_to_format.items():
#                 if col in df_copy.columns:
#                     try:
#                         df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce').dt.strftime(fmt_str)
#                     except Exception: pass # Will be handled by _process_value

#         # Apply percentage formatting first if specified
#         if percentage_columns:
#             for col in percentage_columns:
#                 if col in df_copy.columns:
#                     df_copy[col] = df_copy[col].apply(lambda x: self._process_value(x, is_percentage=True))
        
#         for col in df_copy.columns:
#              # Avoid re-processing already formatted percentage columns
#             if percentage_columns and col in percentage_columns:
#                 continue
#             df_copy[col] = df_copy[col].apply(self._process_value)
        
#         if orient == 'financial_statements':
#             df_copy.columns = [
#                 col.strftime(self.DATE_FORMAT) if isinstance(col, (pd.Timestamp, dt.datetime, dt.date)) else str(col)
#                 for col in df_copy.columns
#             ]
#             return df_copy.to_dict(orient='index')

#         return df_copy.to_dict(orient=orient)

#     def _format_series(self, series: pd.Series, index_date_format=None):
#         if series is None or series.empty: return {}
#         s_copy = series.copy()
#         if index_date_format and isinstance(s_copy.index, pd.DatetimeIndex):
#             s_copy.index = s_copy.index.strftime(index_date_format)
#         return { self._process_value(k): self._process_value(v) for k, v in s_copy.items() }

#     def _format_news_list(self, news_list: list, max_items=3):
#         if not news_list: return []
#         formatted_news = []
#         for item_dict in news_list[:max_items]:
#             processed_item = {}
#             processed_item["uuid"] = self._process_value(item_dict.get("uuid"))
#             processed_item["title"] = self._process_value(item_dict.get("title"))
#             processed_item["publisher"] = self._process_value(item_dict.get("publisher"))
#             processed_item["link"] = self._process_value(item_dict.get("link"))
#             processed_item["type"] = self._process_value(item_dict.get("type"))
#             publish_time = item_dict.get("providerPublishTime")
#             if isinstance(publish_time, (int, float)) and not pd.isna(publish_time):
#                 try:
#                     processed_item["published_time_utc"] = dt.datetime.fromtimestamp(publish_time, dt.timezone.utc).strftime(self.DATETIME_FORMAT)
#                 except (OSError, ValueError):
#                     processed_item["published_time_utc"] = self._process_value(publish_time)
#             else:
#                 processed_item["published_time_utc"] = self._process_value(publish_time)
#             for k, v in item_dict.items():
#                 if k not in processed_item: processed_item[k] = self._process_value(v)
#             formatted_news.append(processed_item)
#         return formatted_news

#     def _format_calendar_dict(self, calendar_data: dict):
#         if not calendar_data or not isinstance(calendar_data, dict): return {}
#         processed_calendar = {}
#         for k, v_list in calendar_data.items():
#             if k == 'Earnings Date' and isinstance(v_list, list):
#                 processed_dates = []
#                 for ts in v_list:
#                     if isinstance(ts, (int,float)) and not pd.isna(ts):
#                         try:
#                             processed_dates.append(dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime(self.DATE_FORMAT))
#                         except (OSError, ValueError): processed_dates.append(self._process_value(ts))
#                     else: processed_dates.append(self._process_value(ts))
#                 processed_calendar[k] = processed_dates
#             elif isinstance(v_list, list) and len(v_list) > 0:
#                  processed_calendar[k] = [self._process_value(item) for item in v_list]
#             else:
#                 processed_calendar[k] = self._process_value(v_list)
#         return processed_calendar

#     def _safe_fetch_and_format(self, fetch_func, formatter_func, default_empty_val, *formatter_args, **formatter_kwargs):
#         try:
#             raw_data = fetch_func()
#             if raw_data is None and (isinstance(default_empty_val, list) or isinstance(default_empty_val, dict)):
#                 return default_empty_val
#             return formatter_func(raw_data, *formatter_args, **formatter_kwargs)
#         except Exception:
#             return default_empty_val

#     # Fund Specific Formatters
#     def _format_fund_holdings_list(self, holdings_list: list):
#         if not holdings_list: return []
#         formatted_holdings = []
#         for item in holdings_list:
#             if not isinstance(item, dict): continue
#             formatted_holdings.append({
#                 "symbol": self._process_value(item.get("symbol")),
#                 "name": self._process_value(item.get("holdingName")),
#                 "weight": self._process_value(item.get("holdingPercent"), is_percentage=True)
#             })
#         return formatted_holdings

#     def _format_fund_sector_weightings(self, sector_weightings_list: list):
#         if not sector_weightings_list: return {}
#         formatted_sectors = {}
#         for item in sector_weightings_list:
#             if not isinstance(item, dict): continue
#             for sector_name_raw, weight in item.items():
#                 sector_name = sector_name_raw.replace("_", " ").title() # Make it more readable
#                 formatted_sectors[sector_name] = self._process_value(weight, is_percentage=True)
#         return formatted_sectors

#     def _format_fund_asset_allocation(self, asset_classifications: dict):
#         if not asset_classifications or not isinstance(asset_classifications.get('weightings'), list) :
#             return {}
        
#         allocations = {}
#         for item_dict in asset_classifications['weightings']:
#             if not isinstance(item_dict, dict): continue
#             for asset_class_raw, weight in item_dict.items():
#                 # e.g. "stockPosition" -> "Stock"
#                 asset_class = asset_class_raw.replace("Position", "").replace("_", " ").title()
#                 allocations[asset_class] = self._process_value(weight, is_percentage=True)
#         return allocations
    
#     def _format_fund_equity_metrics(self, equity_holdings_data: dict):
#         if not equity_holdings_data: return {}
#         return {
#             self._process_value(k.replace("_", " ").title()): self._process_value(v)
#             for k,v in equity_holdings_data.items()
#         }


#     def get_financial_snapshot_dict(self, num_news_stories=3, num_financial_periods=4) -> dict:
#         ticker_info = self._get_ticker_info()
#         quote_type = self._safe_get_from_info("quoteType")

#         # Company/Fund Profile
#         profile_data = {
#             k: self._safe_get_from_info(v) for k, v in {
#                 "name": "shortName", "long_name": "longName", "sector": "sector", # Sector/Category for funds
#                 "industry": "industry", "category": "category", # Category mainly for funds
#                 "fund_family": "fundFamily", # For funds
#                 "legal_type": "legalType", # For funds
#                 "website": "website", "logo_url": "logo_url", "city": "city",
#                 "state": "state", "zip_code": "zip", "country": "country",
#                 "phone": "phone", "full_time_employees": "fullTimeEmployees",
#                 "summary": "longBusinessSummary", # Description for funds
#                 "exchange": "exchange", "quote_type": "quoteType"
#             }.items()
#         }
#         addr1 = self._safe_get_from_info('address1')
#         addr2 = self._safe_get_from_info('address2')
#         full_address = f"{addr1} {addr2}".strip().replace(f"{self.NA_VALUE} {self.NA_VALUE}", self.NA_VALUE).replace(f"{self.NA_VALUE} ", "").replace(f" {self.NA_VALUE}", "")
#         profile_data["address"] = full_address if full_address else self.NA_VALUE


#         # Key Financial Metrics
#         current_price_val = self._safe_get_from_info("regularMarketPrice")
#         if current_price_val == self.NA_VALUE:
#             current_price_val = self._safe_get_from_info("currentPrice")
#         if current_price_val == self.NA_VALUE: # For ETFs, sometimes 'navPrice' is available
#             current_price_val = self._safe_get_from_info("navPrice")


#         key_metrics_data = {
#             k: self._safe_get_from_info(v_key, is_percentage=v_is_percent) for k, (v_key, v_is_percent) in {
#                 "previous_close": ("previousClose", False), "open": ("open", False), "day_low": ("dayLow", False),
#                 "day_high": ("dayHigh", False), "currency": ("currency", False), "market_cap": ("marketCap", False),
#                 "volume": ("volume", False), "average_volume": ("averageVolume", False),
#                 "average_volume_10day": ("averageVolume10days", False),
#                 "52_week_high": ("fiftyTwoWeekHigh", False), "52_week_low": ("fiftyTwoWeekLow", False),
#                 "50_day_average": ("fiftyDayAverage", False), "200_day_average": ("twoHundredDayAverage", False),
#                 "trailing_pe": ("trailingPE", False), "forward_pe": ("forwardPE", False),
#                 "trailing_eps": ("trailingEps", False), "forward_eps": ("forwardEps", False),
#                 "price_to_sales_trailing_12_months": ("priceToSalesTrailing12Months", False),
#                 "price_to_book": ("priceToBook", False), "enterprise_value": ("enterpriseValue", False),
#                 "enterprise_to_revenue": ("enterpriseToRevenue", False), "enterprise_to_ebitda": ("enterpriseToEbitda", False),
#                 "beta": ("beta", False), "dividend_rate": ("dividendRate", False), 
#                 "dividend_yield": ("dividendYield", True), # Mark as percentage
#                 "ex_dividend_date": ("exDividendDate", False), "payout_ratio": ("payoutRatio", True), # Mark as percentage
#                 "book_value": ("bookValue", False), "profit_margins": ("profitMargins", True),
#                 "gross_margins": ("grossMargins", True), "ebitda_margins": ("ebitdaMargins", True),
#                 "operating_margins": ("operatingMargins", True), "revenue_growth_quarterly": ("revenueGrowth", True),
#                 "earnings_growth_quarterly": ("earningsQuarterlyGrowth", True), "total_cash": ("totalCash", False),
#                 "total_cash_per_share": ("totalCashPerShare", False), "ebitda": ("ebitda", False),
#                 "total_debt": ("totalDebt", False), "quick_ratio": ("quickRatio", False),
#                 "current_ratio": ("currentRatio", False), "total_revenue": ("totalRevenue", False),
#                 "debt_to_equity": ("debtToEquity", False), "return_on_assets": ("returnOnAssets", True),
#                 "return_on_equity": ("returnOnEquity", True), "free_cashflow": ("freeCashflow", False),
#                 "operating_cashflow": ("operatingCashflow", False),
#                 # Fund specific metrics
#                 "nav_price": ("navPrice", False), "total_assets_under_management": ("totalAssets", False),
#                 "yield": ("yield", True), "expense_ratio": ("annualReportExpenseRatio", True),
#                 "ytd_return": ("ytdReturn", True), "beta_3year": ("beta3Year", False),
#                 "morningstar_overall_rating": ("morningStarOverallRating", False),
#                 "morningstar_risk_rating": ("morningStarRiskRating", False),
#             }.items()
#         }
#         key_metrics_data["current_price"] = current_price_val

#         # Data sections that are primarily for stocks
#         financial_statements_data = {}
#         analyst_recommendations_data = {"summary": {}, "history": []}
#         earnings_info_data = {}

#         if quote_type not in ["ETF", "MUTUALFUND", "MONEYMARKET"]: # Add other fund types if needed
#             # Financial Statements (typically for stocks)
#             statement_map = {
#                 "annual_income_statement": self.ticker.financials,
#                 "quarterly_income_statement": self.ticker.quarterly_financials,
#                 "annual_balance_sheet": self.ticker.balance_sheet,
#                 "quarterly_balance_sheet": self.ticker.quarterly_balance_sheet,
#                 "annual_cash_flow": self.ticker.cashflow,
#                 "quarterly_cash_flow": self.ticker.quarterly_cashflow,
#             }
#             for name, data_obj in statement_map.items():
#                 try:
#                     df = data_obj
#                     if df is not None and not df.empty and len(df.columns) > num_financial_periods:
#                         df = df.iloc[:, :num_financial_periods]
#                     financial_statements_data[name] = self._format_dataframe(df, orient='financial_statements')
#                 except Exception: financial_statements_data[name] = {}

#             # Analyst Recommendations (typically for stocks)
#             recs_summary = {
#                 k: self._safe_get_from_info(v_key) for k, v_key in {
#                     "recommendation": "recommendationKey", "mean_target_price": "targetMeanPrice",
#                     "median_target_price": "targetMedianPrice", "high_target_price": "targetHighPrice",
#                     "low_target_price": "targetLowPrice", "number_of_analyst_opinions": "numberOfAnalystOpinions"
#                 }.items()
#             }
#             recs_history = self._safe_fetch_and_format(
#                 fetch_func=lambda: self.ticker.recommendations, formatter_func=self._format_dataframe,
#                 default_empty_val=[], orient='records', index_as_date_column_name='Date'
#             )
#             analyst_recommendations_data = {"summary": recs_summary, "history": recs_history}

#             # Earnings Information (typically for stocks)
#             earnings_info_data = {
#                 k: self._safe_get_from_info(v_key) for k, v_key in {
#                     "most_recent_quarter_date": "mostRecentQuarter",
#                     "next_earnings_estimated_date_range_start": "earningsTimestampStart",
#                     "next_earnings_estimated_date_range_end": "earningsTimestampEnd",
#                 }.items()
#             }
#             earnings_info_data["calendar"] = self._safe_fetch_and_format(
#                 fetch_func=lambda: self.ticker.calendar, formatter_func=self._format_calendar_dict,
#                 default_empty_val={}
#             )
#         else: # For ETFs/Funds, provide NA_VALUE for these sections or specific fields
#             financial_statements_data = { k: self.NA_VALUE for k in [
#                 "annual_income_statement", "quarterly_income_statement", "annual_balance_sheet",
#                 "quarterly_balance_sheet", "annual_cash_flow", "quarterly_cash_flow"
#             ]}
#             analyst_recommendations_data = { "summary": self.NA_VALUE, "history": self.NA_VALUE }
#             earnings_info_data = {
#                 "most_recent_quarter_date": self.NA_VALUE,
#                 "next_earnings_estimated_date_range_start": self.NA_VALUE,
#                 "next_earnings_estimated_date_range_end": self.NA_VALUE,
#                 "calendar": self.NA_VALUE
#             }


#         # Company News (relevant for both)
#         company_news_data = self._safe_fetch_and_format(
#             fetch_func=lambda: self.ticker.news, formatter_func=self._format_news_list,
#             default_empty_val=[], max_items=num_news_stories
#         )

#         # Shareholder Information (some parts relevant for ETFs too)
#         shareholder_info_data = {
#             k: self._safe_get_from_info(v_key) for k, v_key in {
#                 "shares_outstanding": "sharesOutstanding", "shares_short": "sharesShort",
#                 "short_ratio": "shortRatio", "short_percent_of_float": "shortPercentOfFloat",
#                 "float_shares": "floatShares", "held_percent_insiders": "heldPercentInsiders",
#                 "held_percent_institutions": "heldPercentInstitutions"
#             }.items()
#         }
#         # Major holders might not be available or relevant for all ETFs in the same way as stocks
#         shareholder_info_data["major_holders"] = self._safe_fetch_and_format(
#             fetch_func=lambda: self.ticker.major_holders,
#             formatter_func=self._format_dataframe, default_empty_val=[], orient='records'
#         )
#         # Institutional holders are often relevant for ETFs
#         shareholder_info_data["top_institutional_holders"] = self._safe_fetch_and_format(
#             fetch_func=lambda: self.ticker.institutional_holders,
#             formatter_func=self._format_dataframe, default_empty_val=[], orient='records',
#             max_rows=10, date_columns_to_format={'Report Date': self.DATE_FORMAT}
#         )

#         # Corporate Actions (dividends/splits for the ETF itself are relevant)
#         corporate_actions_data = {
#             k: self._safe_get_from_info(v_key) for k, v_key in {
#                 "last_dividend_value": "lastDividendValue", "last_dividend_date": "lastDividendDate",
#                 "last_split_factor": "lastSplitFactor", "last_split_date": "lastSplitDate"
#             }.items()
#         }
#         corporate_actions_data["dividends_history"] = self._safe_fetch_and_format(
#             fetch_func=lambda: self.ticker.dividends, formatter_func=self._format_series,
#             default_empty_val={}, index_date_format=self.DATE_FORMAT
#         )
#         corporate_actions_data["stock_splits_history"] = self._safe_fetch_and_format(
#             fetch_func=lambda: self.ticker.splits, formatter_func=self._format_series,
#             default_empty_val={}, index_date_format=self.DATE_FORMAT
#         )

#         # Fund Specific Information
#         fund_information_data = self.NA_VALUE # Default to N/A
#         if quote_type in ["ETF", "MUTUALFUND", "MONEYMARKET"]: # Check if it's a fund type
#             fund_holding_info = ticker_info.get('fundHoldingInfo', {})
#             equity_holdings_metrics_raw = fund_holding_info.get('equityHoldings', {})
            
#             fund_information_data = {
#                 "top_holdings": self._format_fund_holdings_list(fund_holding_info.get('holdings', [])),
#                 "asset_allocation": self._format_fund_asset_allocation(fund_holding_info.get('assetClassifications', {})),
#                 "sector_weightings": self._format_fund_sector_weightings(fund_holding_info.get('sectorWeightings', [])),
#                 "equity_holdings_metrics": self._format_fund_equity_metrics(equity_holdings_metrics_raw),
#                 "bond_ratings": self._process_value(fund_holding_info.get('bondRatings')), # Often complex, process as-is for now
#                 "bond_holdings": self._process_value(fund_holding_info.get('bondHoldings')), # ""
#             }
#             # Add other direct fund info if available and not already in profile/metrics
#             fund_information_data["fund_inception_date"] = self._safe_get_from_info("fundInceptionDate")


#         return {
#             "ticker_symbol": self.symbol,
#             "data_retrieved_utc": dt.datetime.now(dt.timezone.utc).strftime(self.DATETIME_FORMAT),
#             "company_profile": profile_data,
#             "key_financial_metrics": key_metrics_data,
#             "financial_statements": financial_statements_data,
#             "analyst_recommendations": analyst_recommendations_data,
#             # "recent_news": company_news_data,
#             "shareholder_information": shareholder_info_data,
#             "corporate_actions": corporate_actions_data,
#             "earnings_information": earnings_info_data,
#             "fund_information": fund_information_data # Will be NA_VALUE if not a fund
#         }

#     def get_financial_snapshot_json(self, num_news_stories=3, num_financial_periods=4) -> str:
#         data_dict = self.get_financial_snapshot_dict(num_news_stories, num_financial_periods)
#         return json.dumps(data_dict, indent=2)

# # Example Usage:
# if __name__ == "__main__":
#     pd.options.mode.chained_assignment = None
    
#     tickers_to_test = {
#         # "Stock (AAPL)": "AAPL",
#         "ETF (SPY)": "SPY",
#         # "ETF (QQQ)": "QQQ",
#         # "Stock with less data (GOOG)": "GOOG", # For comparison
#         # "Mutual Fund (VTSAX)": "VTSAX",
#         # "Invalid Ticker": "NONEXISTENTTICKERXYZ" # Test invalid
#     }

#     for name, symbol in tickers_to_test.items():
#         print(f"\n--- Testing: {name} ({symbol}) ---")
#         try:
#             analyzer = YFinanceFinancialAnalyzer(symbol)
#             print(f"Fetching data for {analyzer.symbol}...")
#             financial_json = analyzer.get_financial_snapshot_json(num_news_stories=1, num_financial_periods=1)
#             print("\n--- Financial Snapshot (JSON) ---")
#             print(financial_json)

#             # # Optional: Save to file for review
#             # with open(f"{symbol}_snapshot.json", "w") as f:
#             #     f.write(financial_json)
#             # print(f"Snapshot saved to {symbol}_snapshot.json")

#         except (ValueError, RuntimeError) as e:
#             print(f"Initialization or fetching error for {symbol}: {e}")
#         except Exception as e:
#             print(f"An unexpected error occurred for {symbol}: {e}")
#             import traceback
#             traceback.print_exc()
#         print("-" * 50)


import json
import logging
import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt

from apex_fin.utils.ticker_validation import validate_and_get_ticker

logger = logging.getLogger(__name__)

class YFinanceFinancialAnalyzer:
    """
    A streamlined analyzer to fetch only the core data points required for quick
    financial analysis and LLM consumption. It drops all extraneous fields and
    returns a minimized JSON payload.
    """

    NA_VALUE = "N/A"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S UTC"
    DATE_FORMAT = "%Y-%m-%d"
    PERCENT_FORMAT = "{:.2%}"

    def __init__(self, symbol: str):
        if not symbol or not isinstance(symbol, str):
            raise ValueError("A valid stock symbol string must be provided.")
        self.symbol = symbol.upper()
        
        logger.info(f"Attempting to validate and get ticker for input: '{symbol}'")
        self.validated_ticker, self.company_name = validate_and_get_ticker(symbol)

        if not self.validated_ticker:
            logger.error(f"Failed to validate or find a ticker for input: '{symbol}'.")
            raise ValueError(f"Invalid or unfindable ticker: '{symbol}'. Please provide a valid stock ticker or company name.")

        logger.info(f"Validated ticker: '{self.validated_ticker}' (original input: '{symbol}')")
        
        try:
            self._ticker = yf.Ticker(self.validated_ticker)
            self._info = self._ticker.info or {}
        except Exception as e:
            raise RuntimeError(f"Failed to initialize yfinance.Ticker for {self.validated_ticker}: {e}")

    def _process_value(self, value, is_percentage: bool = False):
        if isinstance(value, (dt.datetime, pd.Timestamp)):
            return value.strftime(self.DATETIME_FORMAT)
        if isinstance(value, dt.date):
            return value.strftime(self.DATE_FORMAT)
        if pd.isna(value) or value is None:
            return self.NA_VALUE
        if is_percentage and isinstance(value, (float, int, np.floating, np.integer)):
            try:
                return self.PERCENT_FORMAT.format(value)
            except Exception:
                pass
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return float(value)
        if isinstance(value, (dict, list)) and not value:
            return self.NA_VALUE
        return value

    def _safe_get(self, key: str, is_percentage: bool = False):
        raw = self._info.get(key, None)
        date_keys = {
            "earningsTimestampStart", "earningsTimestampEnd"
        }
        if key in date_keys and isinstance(raw, (int, float)) and raw != 0 and not pd.isna(raw):
            try:
                return dt.datetime.fromtimestamp(raw, dt.timezone.utc).strftime(self.DATE_FORMAT)
            except Exception:
                return self.NA_VALUE
        return self._process_value(raw, is_percentage=is_percentage)

    def _get_key_metrics(self) -> dict:
        raw = self._info
        get = self._safe_get

        # Look up current price fallback chain
        current_price = get("regularMarketPrice")
        if current_price == self.NA_VALUE:
            current_price = get("currentPrice")
        if current_price == self.NA_VALUE:
            current_price = get("navPrice")

        metrics_map = {
            "current_price":           current_price,
            "previous_close":          get("previousClose"),
            "52_week_high":            get("fiftyTwoWeekHigh"),
            "52_week_low":             get("fiftyTwoWeekLow"),
            "trailing_pe":             get("trailingPE"),
            "forward_pe":              get("forwardPE"),
            "enterprise_to_ebitda":    get("enterpriseToEbitda"),
            "free_cashflow":           get("freeCashflow"),
            "market_cap":              get("marketCap"),
            "debt_to_equity":          get("debtToEquity"),
            "profit_margins":          get("profitMargins", is_percentage=True),
            "return_on_equity":        get("returnOnEquity", is_percentage=True),
            "revenue_growth_quarterly":get("revenueGrowth", is_percentage=True),
            "operating_cashflow":      get("operatingCashflow"),
            "ebitda_margins":          get("ebitdaMargins", is_percentage=True),
            "beta":                    get("beta"),
        }
        return metrics_map

    def _get_analyst_recommendations(self) -> dict:
        summary = {
            "recommendation":             self._safe_get("recommendationKey"),
            "mean_target_price":          self._safe_get("targetMeanPrice"),
            "high_target_price":          self._safe_get("targetHighPrice"),
            "low_target_price":           self._safe_get("targetLowPrice"),
            "number_of_analyst_opinions": self._safe_get("numberOfAnalystOpinions"),
        }

        # Fetch history and filter to last 60 days
        try:
            df = self._ticker.recommendations
            if df is None or df.empty:
                history = []
            else:
                cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=60)
                df = df.copy()
                if isinstance(df.index, pd.DatetimeIndex):
                    df = df[df.index.tz_localize(dt.timezone.utc) >= cutoff]
                records = []
                for idx, row in df.iterrows():
                    rec = {col: self._process_value(row[col]) for col in row.index}
                    rec["date"] = idx.tz_convert(dt.timezone.utc).strftime(self.DATE_FORMAT) \
                                 if isinstance(idx, pd.Timestamp) else self._process_value(idx)
                    records.append(rec)
                history = records
        except Exception:
            history = []

        return {"summary": summary, "history": history}

    def _get_earnings_info(self) -> dict:
        earnings_start = self._safe_get("earningsTimestampStart")
        earnings_end   = self._safe_get("earningsTimestampEnd")

        # Build calendar subset with Earnings Average & Revenue Average if available
        try:
            cal = self._ticker.calendar
            cal_dict = {}
            if isinstance(cal, pd.DataFrame):
                for key in ["Earnings Average", "Revenue Average"]:
                    if key in cal.index:
                        val = cal.at[key, cal.columns[0]]
                        cal_dict[key] = self._process_value(val)
            calendar = cal_dict
        except Exception:
            calendar = {}

        return {
            "next_earnings_estimated_date_range_start": earnings_start,
            "next_earnings_estimated_date_range_end":   earnings_end,
            "calendar": calendar
        }

    def get_financial_snapshot_dict(self) -> dict:
        # Sector & Industry
        sector   = self._safe_get("sector")
        industry = self._safe_get("industry")

        return {
            "ticker_symbol": self.validated_ticker,
            "data_retrieved_utc": dt.datetime.now(dt.timezone.utc).strftime(self.DATETIME_FORMAT),
            "sector": sector,
            "industry": industry,
            "key_financial_metrics":       self._get_key_metrics(),
            "analyst_recommendations":     self._get_analyst_recommendations(),
            "earnings_information":        self._get_earnings_info()
        }

    def get_financial_snapshot_json(self) -> str:
        return json.dumps(self.get_financial_snapshot_dict(), indent=2)


# Example usage (for testing):
if __name__ == "__main__":
    # analyzer = YFinanceFinancialAnalyzer("Applied Digital Corporation")
    # print(analyzer.get_financial_snapshot_json())
    
    ticker = "Applied Digital Corporation"
    
    try:
        analyzer = YFinanceFinancialAnalyzer(ticker)
        # Uses default num_news_stories and num_financial_periods from get_financial_snapshot_dict
        data_dict = analyzer.get_financial_snapshot_dict()
        print(json.dumps(data_dict))
    except Exception as e:
        raise ValueError(f"Failed to fetch data for {ticker}: {str(e)}")
