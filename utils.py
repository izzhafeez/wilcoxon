import re
import pandas as pd
from math import sin, cos, atan2, radians, sqrt
from .spiderman import *
import json
import requests


"""
PURPOSE

Chinese characters have their own regex expressions.
So to more easily find them, this is shorthand for the whole collection of characters.
"""

chineseRegex = r'[\u4e00-\u9fff]+'


def postcodeCoords(location):
    """
    PURPOSE

    This function uses the google search function to search for a particular location.
    This would return the latitude and longitude of the location, if it goes smoothly.
    This function is quite primitive, as such, I mostly use it to get the locations of postal codes in Singapore, using search parameters like "Singapore 410230"

    PARAMETERS

    location [str]: input the location of search

    OUTPUT

    A tuple containing the lat and the long of the location searched.
    If not found, return (0,0)
    """
    try:
        return (float(x) for x in re.findall(r"\d+\.\d+", website(f"https://www.google.com/search?q={'+'.join(location.split())}+coordinates").html.find(class_="BNeawe iBp4i AP7Wnd").string))
    except:
        return (0,0)


def latlong(location):
    """
    PURPOSE

    This is the more sophisticated version of the location search function, as it uses official Singapore government services.
    However, it of course is limited to the Singapore search area.

    PARAMETERS

    location [str]: input the location of search

    OUTPUT

    A tuple containing the lat and the long of the location searched.
    If not found, return (0,0)
    """
    try:
        coords = json.loads(requests.get(f"https://developers.onemap.sg/commonapi/search?searchVal={'+'.join(location.split())}&returnGeom=Y&getAddrDetails=Y").text)["results"][0]
        lat, long = float(coords["LATITUDE"]), float(coords["LONGITUDE"])
        return (lat,long)
    except:
        print(location,"could not be found.")
        return (0,0)


def regOR(keywords, toCompile = True, flags = 0):
    """
    PURPOSE

    Searches for a number of substrings using regex search.
    This function acts as a shorthand for the (a|b|c) kind of regex expression.
    Basically, instead of manually typing in every search term you want in that expression, you can just input a list into here and it will convert it for you.

    PARAMETERS

    keywords [str, list]: what keywords you want to search for
    toCompile [boolean]: whether to convert the expression into a re.compile() object, or just a string, where it can be added to other re.compile() objects
    flags [flags]: any regex flags you want to add

    OUTPUT

    Refer to toCompile [boolean] in the part above.
    """
    if type(keywords) == str:
        keywords = [keywords]
    elif type(keywords) != list:
        raise Exception("'keywords' must be a list/str")      
        
    if toCompile:
        return re.compile('(' + '|'.join(keywords) + ')', flags = flags)
    else:
        return '(' + '|'.join(keywords) + ')'


def minimumSatisfy(string, include=[], exclude=[], threshold=0, subtractExclude=False):
    """
    PURPOSE

    Let's say you want to rank a list of strings depending on whether it contains or does not contain certain substrings.
    This function facilitates that, giving more freedom and ease of use when performing this task.
    Basically, the substrings in include[] are the substrings that you want in your string and having them will increase the "score" of the string by +1 (stackable).
    As for the exclude[] substrings, if subtractExclude = True, having those substrings will decrease the "score" by -1 instead.
    Otherwise, if subtractExclude = False, if the string does not contain the substring, then the score will also increase by +1.
    If the score exceeds the threshold, then the output is True.
    Otherwise, False.
    """
    if type(include) == str:
        include = [include]
    elif type(include) != list:
        raise Exception("'include' must be a list/str")  
    if type(exclude) == str:
        exclude = [exclude]
    elif type(exclude) != list:
        raise Exception("'exclude' must be a list/str")

    total = 0
    total += sum(s in string for s in include)
    if subtractexclude:
        total -= sum(s in string for s in exclude)
    else:
        total += sum(s not in string for s in exclude)

    return total >= threshold


def intHex(x):
    """
    PURPOSE

    Just returns the hex form of an integer.
    """
    if type(x) == int:
        return hex(x)[2:]
    else:
        raise Exception("input must be an int")
    

def keywordFilter(listToFilter, include = [], exclude = [], flags = 0):
    """
    PURPOSE

    Let's say you want to filter the strings in a list based on whether they contain and exclude certain substrings.
    This does it.
    So basically, for a string to pass through, it has to contain at least one of the substrings in include[] and NONE of the substrings in exclude[].

    OUTPUT

    A filtered list.
    """
    if type(include) == str:
        include = [include]
    elif type(include) != list:
        raise Exception("'include' must be a list/str")
        
    if type(exclude) == str:
        exclude = [exclude]
    elif type(exclude) != list:
        raise Exception("'exclude' must be a list/str")
    
    if len(include) != 0: listToFilter = list(filter(lambda x: regOR(include, flags=flags).search(x), listToFilter))
    if len(exclude) != 0: listToFilter = list(filter(lambda x: not regOR(exclude, flags=flags).search(x), listToFilter))

    return listToFilter


def listOfLists(lists):
    """
    PURPOSE

    Converts a list of lists into a single list.
    """
    return [item for sublist in lists for item in sublist]


def headerDown(df):
    """
    PURPOSE

    This demotes the headers of a pandas dataframe to become its first row instead, pushing the other rows downwards.
    """
    return df.reset_index(drop=True).T.reset_index().T


def headerUp(df):
    """
    PURPOSE

    This promotes the first row of a pandas dataframe to become its header instead, pulling the other rows upwards
    """
    tempDf = df.copy()
    tempDf.columns = tempDf.iloc[0]
    tempDf = tempDf.drop(tempDf.index[0])
    return tempDf


def mergePivot(pvt1,pvt2):
    """
    PURPOSE

    Based on 2 pivot tables created using pandas, merge them according to index, outputting a single dataframe.
    """
    pvt1df = pd.DataFrame(pvt1)
    pvt1df.fillna(0,inplace=True)
    pvt1df.reset_index(inplace=True)
    pvt2df = pd.DataFrame(pvt2)
    pvt2df.fillna(0,inplace=True)
    pvt2df.reset_index(inplace=True)
    alldata = pvt1df.merge(pvt2df, how='left')
    return alldata


def convertCoords(d,m,s):
    """
    PURPOSE

    Converts coordinates from the arcminutes-arcseconds system to the decimal cardinal system.
    """
    return float(d) + float(m)/60 + float(s)/3600


def dist(x1,y1,x2,y2):
    """
    PURPOSE

    Calculates the distance between coordinates on the Earth.
    """
    R = 6373.0

    lat1 = radians(x1)
    lon1 = radians(y1)
    lat2 = radians(x2)
    lon2 = radians(y2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c