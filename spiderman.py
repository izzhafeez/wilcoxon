import requests
from bs4 import BeautifulSoup as bs
from tld import get_tld
import pandas as pd
import re
import copy
from urllib.parse import urljoin


def findPreviouses(soup, tag, n):

    """
    PURPOSE

    The find_previous() function in BeautifulSoup searches for previous occurrence of a particular tag.
    However, there often are cases where we need to use this function several times, having nested functions like (find_previous(find_previous(soup))).
    Before I found out about the find_all_previous() function, I needed a shorthand for searching for tags.
    So here I am

    PARAMETERS

    soup [BeautifulSoup object]: the soup object that you want to search in
    tag [HTML tag like 'p' or 'h3', or a list of them]: the tags that you want to search for
    n [int]: the number of times the function find_previous() is to be repeated

    OUTPUT

    [BeautifulSoup object]
    """

    for x in range(n):
        soup = soup.find_previous(tag)
    return soup


def findNexts(soup, tag, n):

    """
    PURPOSE

    The find_next() function in BeautifulSoup searches for next occurrence of a particular tag.
    However, there often are cases where we need to use this function several times, having nested functions like (find_next(find_next(soup))).
    Before I found out about the find_all_next() function, I needed a shorthand for searching for tags.
    So here I am

    PARAMETERS

    soup [BeautifulSoup object]: the soup object that you want to search in
    tag [HTML tag like 'p' or 'h3', or a list of them]: the tags that you want to search for
    n [int]: the number of times the function find_next() is to be repeated

    OUTPUT

    BeautifulSoup object
    """

    for x in range(n):
        soup = soup.find_next(tag)
    return soup


def allstr(soup, joiner=""):

    """
    PURPOSE

    The stripped_strings attribute takes a BeautifulSoup object and removes the whitespace elements.
    However, it outputs in an iterable format.
    As such, allstr() is shorthand for the cleanup process.

    PARAMETERS

    soup [BeautifulSoup object]: the soup object that you want to clean
    joiner [str]: how you want to join the list

    OUTPUT

    str
    """

    return joiner.join(list(soup.stripped_strings))


def soupstr(soup):

    """
    PURPOSE

    Similar to the above, soupstr() just converts into a list instead of joining all the strings together.

    PARAMETERS

    soup [BeautifulSoup object]: the soup object that you want to clean

    OUTPUT

    list of str
    """

    return list(soup.stripped_strings)


class website():

    """
    PURPOSE

    A class to represent data retrieved from a website.
    Functions can also be applied to extract more information.

    DEFAULT ATTRIBUTES

    url [str]: the link itself
    domain [str]: the domain link
    html [BeautifulSoup object]: the contents of the page, in html format
    hrefs [list of str]: all the outward links of the page

    OUTPUT

    str
    """
    
    def __init__(self, url):
        
        """
        PARAMETERS

        url [str]: the link to the site
        """
        self.url = url
        self.domain = get_tld(url,as_object = True).fld
        self.html = bs(requests.get(url).text,'html.parser')
        self.hrefs = [a['href'] for a in self.html(href=True)]
        

    def __str__(self):

        """
        PURPOSE

        When the object itself is called, return a dictionary containing its url and hrefs.
        """
        
        return {"url":self.url,"hrefs":self.hrefs}

        
    def attachHrefs(self, hrefOpen = '(href', hrefClose = 'href)', subset = None, edit = False):

        """
        PURPOSE

        This function aims to take each "a"-tagged element and extract its url and the text it contains.
        After that, the url is appended to the text, and the whole thing is returned as a string back to the BeautifulSoup object.
        In order to keep track of what changes I've made to the BeautifulSoup object, as well as to more easily find the urls, a "container" is placed around the urls.
        That's where hrefOpen and hrefClose come into play.
        They basically surround the url and makes the url easier to find using search terms.
        By default, they convert an "a" tag from <a href="url.com">text</a> into text(hrefurl.comhref).
        But of course, they can be changed.

        PARAMETERS

        hrefOpen [str]: refer to above
        hrefClose [str]: refer to above
        subset [list of html tags like 'p', 'h3']: controls which tags to conduct this operation on (eg. only want to change the "a" tags within div elements)
        edit [boolean]: controls whether to change the self.html attribute (setting it to False will output the result to self.editHtml attribute instead)

        OUTPUT

        Will change either self.html or self.editHtml
        """
        
        if edit:
            html = self.html
        else:
            self.editHtml = copy.copy(self.html)
            html = self.editHtml
        
        for tag in html(subset):
            for a in tag('a',href=True):
                try: a.string = a.string + hrefOpen + website.cleanHref(a['href'], domain=self.domain, url = self.url) + hrefClose
                except: a.string = hrefOpen + website.cleanHref(a['href'], domain=self.domain, url = self.url) + hrefClose

        
    def getTables(self, merge = True, href = True, hrefOpen = '(href', hrefClose = 'href)', hrefSeparate = True, edit = True):

        """
        PURPOSE

        The simple function is to retrieve all the tables within the html.
        That simple task is done using Pandas' read_html() function.
        However, combining it with the previously discussed function yields more useful results.
        You see, as it stands, quite alot of tables contain links within their cells and as such, the pd.read_html() function doesn't work as well.
        So, this function rips the links out of their "a" tags and places them either into separate columns, or attached to the text.
        Under the former, for each row, all the links found are gathered into a single column.


        Another purpose of this function is to combine tables with identical column headers.
        Under the condition merge = True, the code looks for groups of tables with the exact same set of column headers.
        From that, it returns the merged tables.

        PARAMETERS

        hrefOpen [str]: refer to above
        hrefClose [str]: refer to above
        merge [boolean]: refer to above
        href [boolean]: whether to include the links, or too discard them altogether
        hrefSeparate [boolean]: whether to separate the hrefs into a separate column
        edit [boolean]: there are two different places where html content is stored (self.html and self.editHtml). As such, this parameter will choose which one to use.

        OUTPUT

        Under merge = True, two new attributes will be added: self.mergedTables and self.uniqueTables.
        mergedTables contains the tables that can be merged, while uniqueTables contains the rest.
        """
            
        if href:
            self.attachHrefs(subset = 'td', hrefOpen = hrefOpen, hrefClose = hrefClose, edit = False)
        
        if edit:
            self.tables = pd.read_html(re.sub('[\n\t]+','Ǟ',str(self.html('table'))))
        else:
            self.tables = pd.read_html(re.sub('[\n\t]+','Ǟ',str(self.editHtml('table'))))
        
        self.tables = [table.fillna('') for table in self.tables]
            
        if hrefSeparate:
            
            for table in self.tables:
                
                table['Links'] = table.apply(lambda x: '\n'.join(re.findall(re.compile(hrefOpen + "(.*?)" + hrefClose),''.join(list(x)))),axis=1)
                table.loc[:,table.columns != 'Links'] = table.loc[:,table.columns != 'Links'].applymap(lambda x: re.sub(re.compile(hrefOpen + ".*?" + hrefClose),'',x))

        self.mergedTables = []
        self.uniqueTables = []

        if merge:
            
            columnSets = {}
            for table in self.tables:
                try:
                    columns = '||'.join(sorted(list(table.columns)))
                    if columns not in columnSets:
                        columnSets[columns] = [table]
                    else:
                        columnSets[columns].append(table)
                except:
                    self.uniqueTables.append(table)
            
            for columnSet in columnSets:
                self.mergedTables.append(pd.concat(columnSets[columnSet]))

    def getLists(self, href = True, hrefOpen = '(href', hrefClose = 'href)', edit = False):

        """
        PURPOSE

        Simliar to the getTables() function, the getLists() function consolidates the urls found within list elements.

        PARAMETERS

        hrefOpen [str]: refer to getTables()
        hrefClose [str]: refer to getTables()
        href [boolean]: whether to include the links, or too discard them altogether
        edit [boolean]: there are two different places where html content is stored (self.html and self.editHtml). As such, this parameter will choose which one to use.

        OUTPUT

        self.rawLists is a list of lists, which just outputs everything
        self.lists is the version of it where the links are attached to the texts
        """
        
        if href:
            self.attachHrefs(subset = re.compile('[oi]l'), hrefOpen = hrefOpen, hrefClose = hrefClose)
            
        if edit:
            self.rawLists = self.html(re.compile('[oi]l'))
        else:
            self.rawLists = self.editHtml(re.compile('[oi]l'))
            
        self.lists = []
        
        for rawList in self.rawLists:
            ss = pd.DataFrame([li.get_text() for li in rawList('li')], columns = ['Text'])
            ss['Hrefs'] = ss['Text'].apply(lambda x: '\n'.join(re.findall(re.compile(hrefOpen + "(.*?)" + hrefClose),x)))
            ss['Text'] = ss['Text'].apply(lambda x: re.sub(re.compile(hrefOpen + ".*?" + hrefClose),'',x))
            self.lists.append(ss)
        

    @staticmethod
    def cleanHref(href, domain=None, url=None):

        """
        PURPOSE

        Sometimes, the href of an "a" element points to an id on the same page (href="#projects" etc.)
        Sometimes, the href of an "a" element points to a page in the same domain (href="projects.html" etc.)
        Sometimes, the href of an "a" element points to an external source (href="projects.com" etc.)
        This code aims to standardise all the codes, making it easier to traverse the site.

        PARAMETERS

        Since this is function mainly used by other functions within this package, there is not really a need to use it on its own.

        href [str]: the input url which you want to clean
        domain [str]: if you know the domain link, then put it here, else, just leave it be
        url [str]: the input the current url of the site, which helps to convert the internal hrefs

        OUTPUT

        A single str for the cleaned url
        """
        
        if href[0] == '#':
            return re.split('#[^#]*$',url)[0] + href
        elif href[0:2] == '//':
            return 'http:' + href
        elif href[0] == '/':
            return 'http://' + domain + href
        else:
            return href
        return href
    

    @classmethod
    def cleanHrefs(self):

        """
        PURPOSE

        This applies the cleanHref() function to all the links in the website.
        Simple as that.

        OUTPUT

        Quite self-explanatory new attributes for the website() object.
        allHrefs is for everything, selfHrefs is for ID references on the same page, intHrefs is for links to the same domain, and extHrefs is everything else.
        """
        
        self.allHrefs = []
        self.selfHrefs = []
        self.intHrefs = []
        self.extHrefs = []
        
        for href in self.hrefs:
            
            try:
                if href[0] == '#':
                    self.selfHrefs.append(re.split('#[^#]*$',self.url)[0]+href)
                elif href[0:2] == '//':
                    self.extHrefs.append('http:'+href)
                elif href[0] == '/':
                    self.intHrefs.append('http://'+self.domain+href)
                else:
                    self.extHrefs.append(href)
                self.allHrefs.append(href)
            except: pass
        
        self.allHrefs = list(set(self.allHrefs))
        self.selfHrefs = list(set(self.selfHrefs))
        self.intHrefs = list(set(self.intHrefs))
        self.extHrefs = list(set(self.extHrefs))