# Korea Stock Trading Assistant
---------------------------------
This package provides assistant tool such as stock trading, stock price analysis.
The linked Securities company is Kiwoom using Kiwoom Open API+.

Below is a description of the files in the package 
+ update.py - Using MariaDB, create and update stock database(sector of stocks, daily candle chart).
+ qpkg/
+ + Kiwoom.py - module used for stock trading and stock data request etc.
+ + qutils.py - util module like logging, getting url etc.
+ + StockDB.py - DML, DDL function module in MariaDB table(3 kinds of table: sector of stocks, daily candle, update)
+ + Trader.py - Backtest and result save/load module
