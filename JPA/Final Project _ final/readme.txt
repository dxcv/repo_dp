CVA.py contains the code for the CVA part.
BL.py contains the code for the Portfolio Construction part

Considerations:
BL.py will read the excel BLdata.xlsx. By default, the actual BLdata.xlsx has the information for the fixed income part. 

In order to use the equity part, the following procedure needs to be followed:
	- Rename BLdata.xlsx to any desired name (BLdata_FI.xlsx for example)
	- Rename BLdata_Equity.xlsx to BLdata.xlsx, so BL.py reads this input
	- Within BL.py, comment line 165 and uncomment line 164 (example graph for FI/Equity), and uncomment line 192 and comment line 191 (changing sharpe ratios from FI to Equity)

