import scrapy
from scrapy.http import Request

username = "zxc8520wer"
password = "aabb1122"
SEARCH_KEYWORD = "kick"
LIMIT_SIZE = 5*(2**20) # 5MB
LIMIT_COUNT = 100
CURRENT_COUNT = 0

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

		# 로그인 검사
		if 'correct' in responsebody:
			self.logger.error('Login failed.')
			return

		for i in range(1,50):
			yield Request(url="https://freesound.org/search/?q=" + SEARCH_KEYWORD + "&page=" + str(i) + "#sound", callback=self.get_sound_page_url)
		
	#다운로드 페이지 url
	def get_sound_page_url(self, response):
		for sel in response.css('.sample_player_small'):
			sound_link = sel.css('.sound_filename').css('.title').xpath('@href').extract()[0]
			yield Request(url='https://freesound.org' + sound_link, callback=self.get_download_url)

	#다운로드 링크 url
	def get_download_url(self, response):
		download_url = response.css('#download_button').xpath('@href').extract()[0]

		# method 파라미터를 HEAD로 입력해서 파일 용량을 미리 알 수 있게 요청
		yield Request(url='https://freesound.org' + download_url, method="HEAD", callback=self.file_filter)

	#파일 필터링
	#용량, 확장자
	def file_filter(self, response):
		global CURRENT_COUNT
		content_length = response.headers['content-length'].decode()
		# print ('name: ' + response.url + ' length: ' + content_length)

		# 용량
		if int(content_length) > LIMIT_SIZE:
			return

		# 확장자
		file_name = response.url.split('/')[-1]
		if '.mp3' not in file_name :
			if '.wav' not in file_name :
				return
		# 100개만 다운로드
		if CURRENT_COUNT >= LIMIT_COUNT :
			return

		CURRENT_COUNT += 1
		# print ('CURRENT_COUNT: ' + str(CURRENT_COUNT))

		# 실제 파일 다운로드 요청
		yield Request(url=response.url, callback=self.save_file)

	#파일 저장	
	def save_file(self, response):
		path = response.url.split('/')[-1]
		with open(path, "wb") as f:
			f.write(response.body)