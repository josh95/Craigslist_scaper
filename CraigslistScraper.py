from bs4 import BeautifulSoup
import requests
import csv
import re
import nltk
from nltk.stem.porter import *
nltk.download('punkt')

def main():
    with open("CraigsList_Data.csv", "w", newline="", encoding='utf-8') as csvfile:
        csvWriter = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow(["title","compensation","postedDate","url"])
    ListingList = buildListingList()
  
    for link in ListingList:
        postingExtractor(link)
    processRaw()

def buildListingList():
    #returns a list of urls for all the listings
    linksList= []
    for i in range(0,500,120):
        if i == 0:
            listingUrl = "https://boston.craigslist.org/search/ggg"
        else:
            listingUrl = "https://boston.craigslist.org/search/ggg?s=" + str(i)
        print(listingUrl)
        html_doc = requests.get(listingUrl).text
        html_doc = html_doc.encode("utf-8", "ignore")
        soup = BeautifulSoup(html_doc, "html.parser")
        
        for span in soup.find_all("a", { "class" : "result-title" }):
            linksList.append(span.get("href"))
    return linksList

def postingExtractor(link):
    #extracts important info from the listing page: title, compensation, posting date
    domain = "https://boston.craigslist.org"
    try:
        url = domain + link
        html_doc = requests.get(url).text
        html_doc = html_doc.encode("ascii", "ignore")
        soup = BeautifulSoup(html_doc, 'html.parser')
        title = soup.find("span",{"id": "titletextonly"}).text.encode("ascii", "ignore").decode("ascii") # encode/decode to ascii while ignoring errors to remove non-compliant characters
        compensation = soup.find("p" , {"class":"attrgroup"}).text.strip().encode("ascii", "ignore").decode("ascii")
        postedDate = soup.find("time", {"class":"date timeago"}).get("datetime").split("T")[0]
    except AttributeError:
        #postings sometimes get flagged for removal and show an error page
        print("encountered error scraping:")
        print(url)
        return
    
    with open("CraigsList_Data.csv", "a", newline="", encoding='utf-8') as csvfile:
        csvWriter = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow([title,compensation,postedDate,url])

def processRaw():
    with open('CraigsList_Data.csv', 'r') as readfile:
        csvreader = csv.reader(readfile, delimiter=',', quotechar='"')
        csvreader.__next__() #skip header
        with open("CraigsList_Data_analysis.csv", "w", newline="", encoding='utf-8') as writefile:
            csvWriter = csv.writer(writefile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csvWriter.writerow(["title","compensation","date","url","compensation_clean","payCadence","isSketchy"])
            for row in csvreader:
                compData = parseCompensation(row[1])
                isSketchy = parseTitle(row[0])
                csvWriter.writerow([row[0],row[1],row[2],row[3],compData[0],compData[1],isSketchy])

def parseCompensation(compensation):
    #reads the text for the compensation and parses out the pay rate and whether it is a flat rate or hourly
    compensation = compensation.replace(",", "").lower()
    if compensation  == "no pay":
        return (0, "flat")
    else:
        if "hour" in compensation or "hr" in compensation:
            per = "hourly"
        elif "week" in compensation or "wk" in compensation:
            per = "weekly"
        elif "month" in compensation:
            per = "monthly"
        else:
            per = "flat"
        
        if  len(re.findall('\d+%',compensation)) > 0: #user used %. Probably a percentage based commision.
            return (0, "percentage")

        if  len(re.findall('\d*\.?\d+k',compensation)) > 0: #user used k abreviation
            rate = re.findall('\d*\.?\d+k',compensation)
            rate = [x.replace("k","000") for x in rate]
        else:
            rate = re.findall('\d*\.?\d+',compensation)
        if len(rate) > 0:
            #this clause catches any instances where compensation is a range eg. $15-$17/hour
            #Use the mean as a way to estimate
            rate = [float(x) for x in rate]
            return (sum(rate) / len(rate), per)
        else:
            return (0, per)

def parseTitle(title):
    #reads the title and tries to decide if it is a sketchy ad or not
    title = re.sub(r"[-~*,.;@#?!&$\/+()]+", " ", title)
    tokens = nltk.word_tokenize(title)
    stemmer = PorterStemmer()
    cleanWords = [stemmer.stem(token) for token in tokens]
    definatelySketchy = ["erot", "stripper", "exot", "adult"]
    girlsOnly = ["femal", "girl"]
    for word in definatelySketchy:
        if word in cleanWords:
            return "sketchy"
    for word in girlsOnly:
        if word in cleanWords:
            return "girls only"
    return "normal"

if __name__ == "__main__":
    main()
