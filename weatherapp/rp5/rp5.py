import logging
import urllib.parse

from bs4 import BeautifulSoup

from weatherapp.core import config
from weatherapp.core import decorators
from weatherapp.core.abstract import WeatherProvider
from weatherapp.core.exception import WeatherProviderError


class Rp5WeatherProvider(WeatherProvider):

	""" Weather provider for RP5 site.
	"""

	name = config.RP5_PROVIDER_NAME
	title = config.RP5_PROVIDER_TITLE
	logger = logging.getLogger(__name__)

	def get_name(self):
		return self.name

	def get_default_location(self):
		""" Default location name.
		"""

		return config.DEFAULT_RP5_LOCATION_NAME

	def get_default_url(self):
		""" Default location url.
		"""

		return config.DEFAULT_RP5_LOCATION_URL

	def get_locations_rp5(self, locations_url):
	    """ Getting locations from rp5.ua.
	    """

	    locations_page = self.get_page_source(locations_url)
	    soup = BeautifulSoup(locations_page, 'html.parser')
	    part_url = ''

	    locations = []
	    for location in soup.find_all('div', class_='country_map_links'):
	    	part_url = location.find('a').attrs['href']
	    	part_url = urllib.parse.quote(part_url)
	    	url = config.base_url_rp5 + part_url
	    	location = location.find('a').text
	    	locations.append((location, url))
	    if locations == []:
	    	for location in soup.find_all('h3'):
	    		part_url = location.find('a').attrs['href']
	    		part_url = urllib.parse.quote(part_url)
	    		url = config.base_url_rp5 + '/' + part_url
	    		location = location.find('a').text
	    		locations.append((location, url))

	    return locations

	def configurate(self):
	    """ Displays the list of locations for the user to select from RP5.
	    """

	    locations = self.get_locations_rp5(config.RP5_BROWSE_LOCATIONS)
	    while locations:
	    	for index, location in enumerate(locations):
	    		print(f'{index + 1}. {location[0]}')

	    	try:
	    		selected_index = int(input('Please select location: '))
	    	except (UnboundLocalError, ValueError):
	    		msg = 'Error!'
	    		if self.app.options.debug:
	    			self.logger.exception(msg)
	    		else:
	    			self.logger.error(msg)	
	    		raise WeatherProviderError(
	    	    		 'You have entered the wrong data format! \n'
	    	    		 'Repeat again, input a number.', 
	    	    		  name1=self.name).action()
	    	
	    	try:
	    		location = locations[selected_index - 1]
	    	except IndexError:
	    		msg = 'Error!'
	    		if self.app.options.debug:
	    			self.logger.exception(msg)
	    		else:
	    			self.logger.error(msg)	
	    		raise WeatherProviderError(
	    	    		'You have entered a non-existent number in the '
	    		    	'list!\nRepeat again.', name1=self.name).action()

	    	locations = self.get_locations_rp5(location[1])

	    self.save_configuration(*location)

	@decorators.timer
	def get_weather_info(self, page_content):
	    """ Getting the final result in tuple from site rp5.
	    """

	    city_page = BeautifulSoup(page_content, 'html.parser')
	    weather_info = {}
	    if not self.app.options.tomorrow:
	    	weather_details = city_page.find('div', 
	    		                      attrs={'id': 'archiveString'})
	    	weather_details_cond = weather_details.find('div', 
	    		                                   class_='ArchiveInfo')
	    	conditions = weather_details.get_text()
	    	condition = str(conditions[conditions.find('F,')+3:])
	    	if condition:
	    		weather_info['cond'] = condition
	    	weather_details_temp = weather_details.find('div',
                                                    class_='ArchiveTemp')
	    	temp = weather_details_temp.find('span', class_='t_0')
	    	if temp:
	    		weather_info['temp'] = temp.text
	    	weather_details_feal_temp = weather_details.find('div',
                                                class_='ArchiveTempFeeling')
	    	feal_temp = weather_details_feal_temp.find('span', class_='t_0')
	    	if feal_temp:
	    		weather_info['feal_temp'] = feal_temp.text
	    else:
	    	weather_details = city_page.find('div', attrs={'id': 
                                                   'forecastShort-content'})
	    	weather_details_tomorrow = weather_details.find('span',
                                                        class_='second-part')
	    	conditions = weather_details_tomorrow.findPrevious('b').text
	    	condition_all = str(conditions[conditions.find('Завтра:')+28:])
	    	condition = str(condition_all[condition_all.find('F,')+3:])
	    	if condition:
	    		weather_info['cond'] = condition
	    	temp = weather_details_tomorrow.find('span', class_='t_0')
	    	if temp:
	    		weather_info['temp'] = temp.text

	    return weather_info
