# Wilcoxon

Wilcoxon is a Python library designed to assist me in my hobbies. I use it quite often and constantly look for ways to improve upon it. Currently, they are written in pretty bad Python code, but as I progress, I'm intending to incorporate them into functional apps, using my newfound knowledge on code design (from school). Here are some important submodules within the library:

1. Chords :- A song processing module designed for analysing the chords used within a song matching them up to its lyrics. I use this to further my Deep Learning model in Tensorflow to predict chords based on lyrics given in a song.
2. Language :- Powered by web-scraping functions, Language is designed for obtaining exam-level vocabulary as well as sample sentences for Chinese, Japanese and Korean. I use this to practice for my language tests, building an Angular application to produce flashcards.
3. Geo :- A collection of geospatial functions used to extract and parse data pertaining to Singapore. The methods in this module have helped me produce my MALLS Card Game, using React as its frontend.
4. Spiderman :- A module that facilitates web-scraping. After reading through the BeautifulSoup documentation, I found that certain common operations are not automated. As such, I decided to compile some of my most-used operations into one module.
5. Telegram :- A Telegram interface used to check on the progress of code. I use this as a wrapper around my iterables so that the Telegram bot can give me progress updates on how many iterations of the loop the code has performed. This is very useful as I don't have to babysit the code.

## Chords

A song processing module designed for analysing the chords used within a song matching them up to its lyrics. I use this to further my Deep Learning model in Tensorflow to predict chords based on lyrics given in a song.

The main sequence of my chords module uses the UltimateGuitar website to extract user-generated chords sheets for guitar players. To extract and parse data from this site, I produced the following methods:

1. ```searchSong(song, artist)``` :- Queries the site based on song and artist, and first displays all the possible search results. This page would include all the users on the platform that have transcribed the chords of the song. Afterwards, I go through each page, extracting text based on regex manipulation.
2. ```guessLen(seq)``` :- Songs may not have the same number of chords in a progression. For example, some songs may go "F-G-C", while some may go "F-C-G-Am". As such, I designed this method to guess the length of the progression used, using some pattern searching.
3. ```cleanSong(setOfWorks)``` :- Once I obtained sufficient chord transcriptions, I needed a way to compile them. The first problem I encountered was that most of them had transcribed the chords in different keys. As such, I had to standardise them to the same key of C major. I did this by analysing the signature of the most commonly used notes in the song. Once I had the unique signature, I matched it with the most likely scale.
4. ```findBPM(song, artist)``` :- Using another website, I produced a script to obtain the BPM of the song.


## Language

Powered by web-scraping functions, Language is designed for obtaining exam-level vocabulary as well as sample sentences for Chinese, Japanese and Korean. I use this to practice for my language tests, building an Angular application to produce flashcards.

Here is what I've done to facilitate the learning of Chinese, Japanese and Korean:

#### Chinese

1. ```chineseSentence(word, meanings='', all_)``` :- In this method, I used [Chinese Pod](chinesepod.com) to search for sentences based on Chinese words. Most of the time, a particular chinese word may have many definitions and meanings. As such, I had an additional filter to take only the sentence that best fit the meaning I was trying to get.
2. ```chineseFull(word, meanings='', all_)``` :- This method consolidates the ```chineseSentence``` method, along with other useful operations like converting into Traditional, Pinyin and Simplified versions of the word.
3. ```getHSKVocab(level)``` :- This method extracts and parses data from the [HSK academy website](hskacademy.com), obtaining the official word list of each HSK level and compiling and maniplating all data using ```fullHSKProcess```. This functionality is improved with the ```HSKSentence``` method, which further extracts sentence data from the site.

#### Japanese

1. ```japaneseSentence(word, meanings='', all_)``` :- Similar to that of Chinese, this method uses the [kanshudo website](kanshudo.com) to search for Japanese sentences. This is a little bit more tricky, as japanese words are subject to grammar, and the characters may not appear in their exact form. Furthermore, the text is all over the place, with random pronunciations cluttering the sentence space.
2. ```japaneseFull(word, meanings='', all_)``` :- Similar to that of Chinese, this method consolidates multiple Japanese word processing functionalities into one.
3. ```JLPTKanji()``` :- This method extracts [JLPTsensei](jlptsensei.com)'s list of kanji, ordered by frequency of use. However, there was a lot more restructuring and standardisation of data that I had to accomplish in order to produce a clean dataset.
4. ```japaneseLesson(link)``` :- [Kanshudo](kanshudo.com) has alot of useful Japanese lessons and grammar points, along with useful sentences. Based on a particular link from kanshudo, this function extracts alot of useful information and standardises them into sizeable lesson points. This data is compiled using the function ```japaneseLessonFull()``` which gets all the lessons found on the website.

#### Korean

1. ```koreanLesson(link)``` :- [howtostudykorean.com](howtostudykorean.com) has a good collection of lessons planned out. As such, I decided to extract them out. This was much easier said than done, because there was even more unstructured content. This was purely a text-based lesson plan with little to no structured data involved. A lot of pattern-finding was needed to extract the relevant information. Coupled with the ```koreanLessonFull()``` method, this function can output all the lesson info, and standardise them into a useful pandas format.

## Geo

A collection of geospatial functions used to extract and parse data pertaining to Singapore. The methods in this module have helped me produce my MALLS Card Game, using React as its frontend.

This is by far my most used module, as it has helped me through many projects, including my work at SCDF. Here are some of the important methods used:

1. ```getMRT()``` :- This 200+ lines of code performs many operations. First, it scrapes the wikipedia page for the [list of Singapore MRT stations](https://en.wikipedia.org/wiki/List_of_Singapore_MRT_stations) to get links to each station's Wikipedia page. Next, I extracted data from each of those pages, obtaining station labels, station names, chinese translations, addresses, postal codes as well as coordinates. This was troublesome, as many left these fields blank, which meant that I had to individually find each field using different regexes. At this stage, I also mapped the station names to their abbreviations. Next, I found the coordinates of the exits of the MRT and LRT stations using LTA's dataset, mapping each exit to an existing train station. Finally, I did some easy mappings to the monthly ridership and color of the MRT line.
2. ```getBus(accountKey)``` :- I made this function to extract data from LTA's datamall, obtaining information on bus stops and their services. Using this, I was further able to map them to roads and passenger volumes.
3. ```getRoads()``` :- This function parses the road map of Singapore, given in KML format. As a byproduct, I have also parsed the planning zone map of Singapore, making it easier to visualise road networks in individual planning zones.
4. ```generateElevationMap()``` :- This method estimates the altitude of a particular location, based on some topographical line data. This dataset only includes elevation intervals [0m, 20m, 40m,...] so it became a matter of coming up with a suitable metric for finding the in-between points.

## Spiderman

A module that facilitates web-scraping. After reading through the BeautifulSoup documentation, I found that certain common operations are not automated. As such, I decided to compile some of my most-used operations into one module.

My first proper OOP project, I did my best to incorporate OOP principles into its functionality:

1. ```attachHrefs()``` :- When parsing a data, sometimes the links disappear. As such, this method separates the href from its 'a' tag.
2. ```getTables()``` :- With a couple of additional functionality like merging and href binding, this method improves upon pandas' read_html method.
3. ```getLists()``` :- Similar to ```getTables()```, this method improves upon base functionality, giving the option to attach hrefs to the dataframes.
4. ```cleanHref()``` :- Some links found in a website can point to external sources, some to internal sources and some to the page itself. As such, I standardised them all using this function.

## Telegram

A Telegram interface used to check on the progress of code. I use this as a wrapper around my iterables so that the Telegram bot can give me progress updates on how many iterations of the loop the code has performed. This is very useful as I don't have to babysit the code. This was just a matter of defining ```__init__```, ```__iter__``` and ```__next__``` methods so nothing special there.