import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup 
import csv
from pprint import pprint

async def FetchBookInfo(url, session) -> dict:
    async with session.get(url) as response:
        bookSoup = BeautifulSoup(await response.text(), 'html.parser')
        productmain_container = bookSoup.find_all("div", class_="col-sm-6 product_main")
        book_title = productmain_container[0].find("h1").text
        book_price = productmain_container[0].find("p", class_="price_color").text
        print("[FetchBookInfo] fetching {0}".format(book_title))
        product_information_table = bookSoup.find("table", class_="table table-striped")
        product_details = {
            "Title": book_title,
            "Price": book_price,
            "UPC": None,
            "Product Type": None,
            "Price (excl. tax)": None,
            "Price (incl. tax)": None,
            "Tax": None,
            "Availability": None,
            "Number of reviews": None
        }
        for row in product_information_table.find_all("tr"):
            product_details[row.find("th").text] = row.find("td").text
        return product_details


async def FetchAuthorInfo(author_name, url, session) -> dict:
    # author name has to be passed by param becuase toscrape has a typo in its author-title tag where start:<h3> end </h2> via Google Chrome
    # response.text() will report h3 including all the informatio in the author_container
    async with session.get(url) as response:
        authorSoup = BeautifulSoup(await response.text(), 'html.parser')
        author_container = authorSoup.find('div', class_='author-details')
        #author_name = author_container.findChil("h2", class_='author-title') decremented until toscrape fixes error
        author_dob = author_container.find('span', class_='author-born-date').text
        author_pob = author_container.find('span', class_='author-born-location').text
        author_desc = author_container.find('div', class_='author-description').text
        ##TODO: CHECK DESCRIPTION BECUASE CSV missing length
        print("[FetchBookInfo] fetching {0}".format(len(author_desc.strip())))
        product_details = {
            "Author": author_name,
            "Date of Birth": author_dob,
            "Location of Birth": author_pob,
            "Description": author_desc.strip()
        }
        return product_details

async def FetchFiveStar():
    fivestar_href_List = []
    headers = [
        "Title", 
        "Price", 
        "UPC",
        "Product Type", 
        "Price (excl. tax)", 
        "Price (incl. tax)", 
        "Tax", 
        "Availability", 
        "Number of reviews"
    ]
    async with aiohttp.ClientSession('http://books.toscrape.com/') as session:
        tasks = []
        book_href = []
        for i in range(1, 10):
            async with session.get('/catalogue/page-{0}.html'.format(i)) as resp:
                soup = BeautifulSoup(await resp.text(), 'html.parser')
                page_range = soup.find_all("li", class_="current")[0].text.strip()
                page_current = re.search(r'Page (.*?) of', page_range).group(1)
                for book in soup.find_all("p", class_="star-rating Five"):
                    book_parent_container = book.parent
                    book_href.append("/catalogue/{0}".format(book_parent_container.find("h3").find("a")['href']))
        for href in book_href:
            task = asyncio.ensure_future(FetchBookInfo(href, session))
            tasks.append(task)

            #responses = await asyncio.gather(*tasks)
            fivestar_href_List = await asyncio.gather(*tasks)

    await session.close()
    return headers, fivestar_href_List

async def FetchHistoricalFictionBooks():
    fivestar_href_List = []
    headers = [
        "Title", 
        "Price", 
        "UPC",
        "Product Type", 
        "Price (excl. tax)", 
        "Price (incl. tax)", 
        "Tax", 
        "Availability", 
        "Number of reviews"
    ]
    async with aiohttp.ClientSession('http://books.toscrape.com/') as session:
        tasks = []
        book_href = []
        for i in range(1, 10):
            async with session.get('/catalogue/page-{0}.html'.format(i)) as resp:
                soup = BeautifulSoup(await resp.text(), 'html.parser')
                page_range = soup.find_all("li", class_="current")[0].text.strip()
                page_current = re.search(r'Page (.*?) of', page_range).group(1)
                for price in soup.find_all("p", class_="price_color"):
                    if (float(str(price.text)[1:]) > 30.00):
                        book_parent_container = price.parent.parent
                        book_href.append("/catalogue/{0}".format(book_parent_container.find("h3").find("a")['href']))
        for href in book_href:
            task = asyncio.ensure_future(FetchBookInfo(href, session))
            tasks.append(task)

            #responses = await asyncio.gather(*tasks)
            fivestar_href_List = await asyncio.gather(*tasks)

    await session.close()
    return headers, fivestar_href_List

def WriteToCSV(filename, header, data):
    """
    - data must be an array of dicts
    - elements must not contain nested dicts
    - data keys = header
    """
    
    with open(filename + '.csv', 'w') as csvfile:
        print("[WriteToCSV] {0}.csv has been opened and is currently being written ...".format(filename))
        csvwriter = csv.DictWriter(csvfile, fieldnames = header)
        csvwriter.writeheader()
        csvwriter.writerows(data)
        print("[WriteToCSV] {0}.csv has successfully been written to.".format(filename))


async def FetchInspirationalQuotes():
    quote_details = []
    header = [
        'Quote',
        'Author'
    ]
    async with aiohttp.ClientSession('https://quotes.toscrape.com/') as session:
        for i in range(1,2):
            async with session.get('/tag/inspirational/page/{0}/'.format(i)) as resp:
                soup = BeautifulSoup(await resp.text(), 'html.parser')
                tags_parent = soup.find_all('div', class_="quote")
                for item in tags_parent:
                    quote_details.append(
                        {
                        'Quote': item.find('span', class_="text").text,
                        'Author': item.find('small', class_="author").text
                        }
                    )
    await session.close()
    return header, quote_details
    
    
async def FetchFriendshipQuotes():
    author_detail_list = []
    author_href = []
    header = [
        'Author',
        'Date of Birth',
        'Location of Birth',
        'Description'
    ]
    tasks = []
    async with aiohttp.ClientSession('https://quotes.toscrape.com/') as session:
        for i in range(1,2):
            async with session.get('/tag/friendship/page/{0}/'.format(i)) as resp:
                soup = BeautifulSoup(await resp.text(), 'html.parser')
                tags_parent = soup.find_all('div', class_="quote")
                for quote in tags_parent:
                    author_href.append(
                        [
                            quote.find('small', class_="author").text,
                            quote.find_all('span')[1].find('a')['href'] #in form /author/[author name]
                        ]) 
                for href in author_href:
                    task = asyncio.ensure_future(FetchAuthorInfo(href[0], href[1], session))
                    tasks.append(task)
                    
                    author_detail_list = await asyncio.gather(*tasks)
    await session.close()
    return header, author_detail_list
    

async def main():
    #result = await FetchHistoricalFictionBooks()
    test = await FetchFriendshipQuotes()
    pprint(test)
    WriteToCSV("auhtor_data", test[0], test[1])
    #pprint(result[1])
    #WriteToCSV("asy", result[0], result[1])

asyncio.get_event_loop().run_until_complete(main())