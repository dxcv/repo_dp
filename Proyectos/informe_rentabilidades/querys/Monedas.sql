Select 
	CASE 
		WHEN Index_ID=605 THEN 'ARS'
		WHEN Index_ID=23 THEN 'UF'
		WHEN Index_ID=66 THEN 'US$'
		WHEN Index_ID=85 THEN 'MX'
	END AS Moneda,
	CASE
		WHEN Index_ID=605 THEN 'US$'
		WHEN Index_ID=23 THEN '$'
		WHEN Index_ID=66 THEN '$'
		WHEN Index_ID=85 THEN '$'
	END AS paridad, valor from indices_dinamica where Index_ID in (23,66,85,605) and fecha='AUTODATE' 


