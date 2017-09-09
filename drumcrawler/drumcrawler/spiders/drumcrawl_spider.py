import scrapy
from scrapy.http import Request

username = "zxc8520wer"
password = "aabb1122"
search_keyword = "kick"

class drumcrawlSpider( scrapy.Spider ) :
	name = "drumcrawl"
	allowed_domains = ["freesound.org"]
	start_urls = ['https://freesound.org']

	def start_requests(self):
		return [Request(url="https://freesound.org/home/login", callback=self.login)]

	def login(self, response):
		token = response.css('input[name=csrfmiddlewaretoken]::attr(value)').extract_first()
		return scrapy.FormRequest('https://freesound.org/home/login',
									formdata={'username': username, 'password': password, 'csrfmiddlewaretoken' : token},
									callback=self.parse, dont_filter=True)

	def parse(self, response):
		responsebody = response.body_as_unicode()

		if 'correct' in responsebody:
			self.logger.error('Login failed.')
			return
		for i in range(1,2):
			yield Request(url="https://freesound.org/search/?q=" + search_keyword + "&page=" + str(i) + "#sound", callback=self.get_sound_page_url)
		
	#다운로드 페이지 url
	def get_sound_page_url(self, response):
		for sel in response.css('.sample_player_small'):
			sound_link = sel.css('.sound_filename').css('.title').xpath('@href').extract()[0]
			yield Request(url='https://freesound.org' + sound_link, callback=self.get_download_url)

	#다운로드 링크 url
	def get_download_url(self, response):
		download_url = response.css('#download_button').xpath('@href').extract()[0]
		yield Request(url='https://freesound.org' + download_url, callback=self.save_file)

	#파일 저장	
	def save_file(self, response):
		path = response.url.split('/')[-1]
		print (response.headers)
		with open(path, "wb") as f:
			f.write(response.body)

