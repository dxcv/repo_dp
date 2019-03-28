










AUI.add(
	'portal-available-languages',
	function(A) {
		var available = {};

		var direction = {};

		

			available['ca_ES'] = 'Catalan (Spain)';
			direction['ca_ES'] = 'ltr';

		

			available['zh_CN'] = 'Chinese (China)';
			direction['zh_CN'] = 'ltr';

		

			available['en_US'] = 'English (United States)';
			direction['en_US'] = 'ltr';

		

			available['fi_FI'] = 'Finnish (Finland)';
			direction['fi_FI'] = 'ltr';

		

			available['fr_FR'] = 'French (France)';
			direction['fr_FR'] = 'ltr';

		

			available['de_DE'] = 'German (Germany)';
			direction['de_DE'] = 'ltr';

		

			available['iw_IL'] = 'Hebrew (Israel)';
			direction['iw_IL'] = 'rtl';

		

			available['hu_HU'] = 'Hungarian (Hungary)';
			direction['hu_HU'] = 'ltr';

		

			available['ja_JP'] = 'Japanese (Japan)';
			direction['ja_JP'] = 'ltr';

		

			available['pt_BR'] = 'Portuguese (Brazil)';
			direction['pt_BR'] = 'ltr';

		

			available['es_ES'] = 'Spanish (Spain)';
			direction['es_ES'] = 'ltr';

		

		Liferay.Language.available = available;
		Liferay.Language.direction = direction;
	},
	'',
	{
		requires: ['liferay-language']
	}
);