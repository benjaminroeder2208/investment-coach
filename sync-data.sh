#!/bin/bash
cd /home/investment-coach/investment-coach
/usr/local/bin/sc broker overview --json > portfolio_live.json
/usr/local/bin/sc broker holdings --json > portfolio_holdings.json
/usr/local/bin/sc broker transactions --json > portfolio_transactions.json
