from bs4 import BeautifulSoup
import requests

proxies = {
    'http': 'http://172.87.132.189:8080',
}
listingUrl = "https://boston.craigslist.org/search/ggg"
html_doc = requests.get(listingUrl,proxies=proxies).text
print(html_doc)
