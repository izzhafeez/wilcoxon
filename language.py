import re
import pykakasi
import pinyin
import chinese
from hanziconv import HanziConv
from .spiderman import *
from .utils import *
from translate import Translator
import jaconv
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
import ast
import random
from tqdm import tqdm

"""
PURPOSE

This section sets up the pykakasi's Transliterator object, which allows you to convert Japanese text into its romanised form.
"""
kks = pykakasi.kakasi()
kks.setMode("H","a")
kks.setMode("K","a")
kks.setMode("J","a")
kks.setMode("s", True)
kks.setMode("C", True)
conv = kks.getConverter()
transliter = Transliter(academic)

### CHINESE
def tryPinyin(x):
    """
    PURPOSE

    Extends the pinyin.get() function to allow for errors.
    """
    try: return pinyin.get(x)
    except: return x


def tryTraditional(x):
    """
    PURPOSE

    Extends the toTraditional() function to allow for errors.
    """
    try: return HanziConv.toTraditional(x)
    except: return x
    

def trySimplified(x):
    """
    PURPOSE

    Extends the toSimplified() function to allow for errors.
    """
    try: return HanziConv.toSimplified(x)
    except: return x


def tryChineseSentenceOld(x):
    """
    PURPOSE

    Outdated way that I search for sentences.
    Basically, you input a chinese word, and it will return sentences containing it.
    I switched out of this because it was not reliable and versatile enough.
    """
    try:
        baseUrl = 'http://bcc.blcu.edu.cn/zh/search/0/'
        url = baseUrl + str(x.encode())[2:-1].replace(r'\x','%')
        site = spiderman.website(url)
        site.getRelevant(keywords = [x])
        toReturn = []

        for text in site.relevantText[:5]:
            try: toReturn.append(text.split('全文;')[1].replace(';',''))
            except: pass

        return '\n\n'.join(toReturn)
    except: return ''


def chineseSentence(word, meanings = '', all_ = False):
    """
    PURPOSE

    I use the chinesepod.com site to search for sentences based on Chinese words.

    PARAMETERS

    word [str]: self-explanatory
    meanings [str]: Most of the time, each word or character will have multiple meanings
                    However, when searching for a sample sentence, you'd usually want to focus on a particular meaning of the word.
                    This parameter takes care of that.
                    As long as the sentence contains one of the meanings in its English translation, it will pass through the filter.
                    As of now, the words within the parameter are split, and filtered based on character length (3 to 15).
                    I'd go for NLP on this, but I think that's a bit too overkill as I don't really want EVERY single sentence. Just a couple will do.
    all_ [boolean]: If it's True, then all search results will be returned

    OUTPUT

    A list containing the sentence, its pinyin equivalent, and its English meaning.
    """
    try:
        site = website('https://chinesepod.com/dictionary/english-chinese/' + word)
        site.getTables()
        meanings = re.findall('[A-Za-z]{3,15}',meanings)
        sentenceSets = site.tables[0][0].tolist()
        sentenceSets = keywordFilter(sentenceSets,meanings)

        if all_:
            toReturn = []
            for sentenceSet in sentenceSets:
                toReturn.append([entry.strip() for entry in re.split('Ǟ+',sentenceSet)[1:4]])
            return toReturn

        else:
            chosenSentenceSet = sentenceSets[random.randrange(0,len(sentenceSets))]
            return [entry.strip() for entry in re.split('Ǟ+',chosenSentenceSet)[1:4]]

    except: return ['','','']


def chineseFull(word, meanings = '', all_ = False):
    """
    PURPOSE

    Consolidates the abovementioned functions, to give a more comprehensive understanding of the word.
    It uses the chineseSentence(), the tryPinyin() as well as the tryTraditional() functions.

    PARAMETERS

    word [str]: self-explanatory
    meanings [str]: Most of the time, each word or character will have multiple meanings
                    However, when searching for a sample sentence, you'd usually want to focus on a particular meaning of the word.
                    This parameter takes care of that.
                    As long as the sentence contains one of the meanings in its English translation, it will pass through the filter.
                    As of now, the words within the parameter are split, and filtered based on character length (3 to 15).
                    I'd go for NLP on this, but I think that's a bit too overkill as I don't really want EVERY single sentence. Just a couple will do.
    all_ [boolean]: If it's True, then all search results will be returned

    OUTPUT

    A dictionary containing the word itself, its meanings, its pinyin form, its traditional form, example sentences, the pinyin form of said sentences, and the English translation of said sentences.
    """
    if all_:
        Ls = []
        results = chineseSentence(word, meanings, all_ = True)
        for entry in results:
            L = {'Word':word,'Usages':meanings,'Word Pinyin':tryPinyin(word),'Traditional':tryTraditional(word),'Examples':'','Example pinyin':'','Example translation':''}
            L['Examples'], L['Example pinyin'], L['Example translation'] = entry
            Ls.append(L)
        return Ls

    else:
        L = {'Word':word,'Usages':meanings,'Word Pinyin':tryPinyin(word),'Traditional':tryTraditional(word),'Examples':'','Example pinyin':'','Example translation':''}
        results = chineseSentence(word,meanings)
        L['Examples'], L['Example pinyin'], L['Example translation'] = results
        return L


def getHSKVocab(level):
    """
    PURPOSE

    hsk.academy has compiled the vocabulary requirements for each of the HSK levels.
    Each word has its own page, coupled with the occasional sample sentences.
    This function extracts that information and compiles everything.

    PARAMETERS

    level [int, [1,6]]: input the HSK level of the vocabulary list you want
    """
    site = website('https://hsk.academy/en/hsk_%d' % level)
    soup = site.html('script',string=re.compile('words'))[0]
    words = re.findall('{"id".*?}',soup.string.replace('\\',''))
    words = [ast.literal_eval(x) for x in words]
    df = pd.DataFrame(words)[['hanziRaw','trad','pinyinToneSpace','def']]
    df.columns = ['Word','Traditional','Word Pinyin','Usages']
    df['Level'] = 'HSK %d' % level
    return df


def HSKSentence(word):
    """
    PURPOSE

    As mentioned, each word in the HSK list has its own page with sample sentences sometimes.
    This function extracts those sentences.

    PARAMETERS

    word [str]: word in the HSK list which you want to search
    """
    try:
        site = website('https://hsk.academy/en/words/%s' % word)
        results = []
        for span in site.html('span'):
            if span.parent.name == 'li':
                results.append(list(span.stripped_strings))
        if results == []:
            return [['','']]
        return results
    except: return [['','']]
    

def fullHSKProcess():
    """
    PURPOSE

    This conducts the whole process of getting the HSK words, as well as their sample sentences, using both functions mentioned above.
    It compiles the results into a singular dataframe, with standardised formats.
    """
    hsk = pd.concat([getHSKVocab(level) for level in range(1,7)])
    results = []
    for word in tqdm(hsk['Word']):
        results.append(HSKSentence(word))
    hsk['results'] = results
    hsk = hsk.explode('results')
    hsk['Sentence'] = hsk['results'].apply(lambda x: x[0])
    hsk['Sentence Pinyin'] = hsk['results'].apply(lambda x: x[1])
    hsk = hsk.drop('results', axis=1)
    return hsk.reset_index(drop=True)

### JAPANESE
def tryRomaji(x):
    """
    PURPOSE

    Extends the conv.do() function to allow for errors, converting Japanese text to its romaji form.
    """
    try: return conv.do(x).replace(' ha ',' wa ')
    except: return x


def japaneseSentence(word, meanings = '', all_ = False):
    """
    PURPOSE

    I use the kanshudo.com site to search for sentences based on Japanese words.

    PARAMETERS

    word [str]: self-explanatory
    meanings [str]: Most of the time, each word or character will have multiple meanings
                    However, when searching for a sample sentence, you'd usually want to focus on a particular meaning of the word.
                    This parameter takes care of that.
                    As long as the sentence contains one of the meanings in its English translation, it will pass through the filter.
                    As of now, the words within the parameter are split, and filtered based on character length (3 to 15).
                    I'd go for NLP on this, but I think that's a bit too overkill as I don't really want EVERY single sentence. Just a couple will do.
    all_ [boolean]: if it's True, then all search results will be returned

    OUTPUT

    A list containing the sentence, its romaji equivalent, and its English meaning.
    """
    try:
        site = website('https://www.kanshudo.com/searcht?q=' + word)
        meanings = re.findall('[A-Za-z]{3,15}',meanings)
        sentenceSets = site.html(class_='tatoeba')
        sentenceSets = list(filter(lambda x:re.compile(regOR(meanings)).search(x.get_text()),sentenceSets))

        if all_:
            toReturn = []
            for sentenceSet in sentenceSets:

                for furi in sentenceSet(class_='furigana'):
                    furi.clear()
                
                sentence = re.split('\n+', sentenceSet.get_text())[2]
                transliteration = tryRomaji(sentence)
                translation = re.split('\n+', sentenceSet.get_text())[3].strip()
                toReturn.append([sentence, transliteration, translation])

            return toReturn

        else:
            chosenNumber = random.randrange(0,len(sentenceSets))
            chosenSentenceSet = sentenceSets[chosenNumber]
            
            for furi in chosenSentenceSet(class_='furigana'):
                furi.clear()
            
            sentence = re.split('\n+', chosenSentenceSet.get_text())[2]
            transliteration = tryRomaji(sentence)
            translation = re.split('\n+', chosenSentenceSet.get_text())[3].strip()
            
            return [sentence, transliteration, translation]
    except:
        return ['','','']


def japaneseFull(word, meanings = "", all_ = False):
    """
    PURPOSE

    Consolidates the abovementioned functions, to give a more comprehensive understanding of the word.
    It uses the japaneseSentence(), the tryRomaji() as well as the tryPinyin() functions.

    PARAMETERS

    word [str]: self-explanatory
    meanings [str]: Most of the time, each word or character will have multiple meanings
                    However, when searching for a sample sentence, you'd usually want to focus on a particular meaning of the word.
                    This parameter takes care of that.
                    As long as the sentence contains one of the meanings in its English translation, it will pass through the filter.
                    As of now, the words within the parameter are split, and filtered based on character length (3 to 15).
                    I'd go for NLP on this, but I think that's a bit too overkill as I don't really want EVERY single sentence. Just a couple will do.
    all_ [boolean]: if it's True, then all search results will be returned

    OUTPUT

    A dictionary containing the word itself, its meanings, its romaji form, its pinyin form, example sentences, the pinyin form of said sentences, and the English translation of said sentences.
    """
    if all_:
        Ls = []
        results = japaneseSentence(word, meanings, all_ = True)
        for entry in results:
            L = {'Word':word,'Usages':meanings,'Transliteration':tryRomaji(word),'Chinese':tryPinyin(word),'Examples':'','English':'','Translation':''}
            L['Examples'], L['English'], L['Translation'] = entry
            Ls.append(L)
        return Ls

    else:
        L = {'Word':word,'Usages':meanings,'Transliteration':tryRomaji(word),'Chinese':tryPinyin(word),'Examples':'','English':'','Translation':''}
        results = japaneseSentence(word,meanings)
        L['Examples'], L['English'], L['Translation'] = results
        return L


def tryFindKanji(x, exact = False):
    """
    PURPOSE

    Japanese text has its romaji form, which is its English transliteration.
    Many times, there are overlaps in said romaji form ie multiple Japanese words can have the same English transliteration.
    As such, I wanted to find the overlaps and managed to make this function, powered by jisho.org.
    It takes in a string, such as "jisho" and returns the list of Japanese words that follow the same romaji.
    Setting exact = False will give more leeway to the results, enabling words like "jishou" to also come out.
    """
    try:   
        site = website('https://jisho.org/search/' + x)
        results = {}
        for i in site.html('span',class_='text')[1:]:
            word = i.get_text().strip()
            furigana = i.find_previous(class_='furigana').get_text().strip()
            meaning = i.find_next(class_='meaning-meaning').get_text()
            if furigana == x or not exact:
                results[word] = {'furigana':furigana, 'meaning':meaning}
        return results
    except: return {}


def JLPTKanji():
    """
    PURPOSE

    JLPTsensei has a very good list of Kanji, ordered by frequency of use.
    This function basically just extracts useful information yet again, and I had to apply alot of standardisation principles in all of this.
    """
    links = []
    i = 1
    while i < 12:
        try:
            site = website("https://jlptsensei.com/kanji-list-ordered-by-frequency-of-use/page/{}/".format(i))
            links.extend(list(set(a["href"] for a in site.html("a", href=re.compile("learn-japanese-kanji")))))
            i += 1
        except:
            break
    links = list(set(links))

    result = []

    for link in tqdm(links):

        subsite = website(link)

        try: kpro = allstr(subsite.html(class_="header-kunyomi")[0]," ")
        except: kpro = ""
        try: opro = allstr(subsite.html(class_="header-onyomi")[0]," ")
        except: opro = ""

        krea = []
        try:
            for word in list(subsite.html(text=re.compile("Kunyomi Readings"))[0].next_siblings):
                try:
                    krea.append(tuple(map(lambda x: x.strip(), re.split("【|】",word))))
                except: continue
        except: None            

        orea = []
        try:
            for word in list(subsite.html(text=re.compile("Onyomi Readings"))[0].next_siblings):
                try:
                    orea.append(tuple(map(lambda x: x.strip(), re.split("【|】",word))))
                except: continue
        except: None

        sentences = []
        for h in subsite.html("h5"):
            try:
                jap, *a, romaji, meaning = list(map(allstr, h.next_siblings))
                sentences.append((jap, romaji, meaning))
            except: continue

        try: rank = int(allstr(subsite.html(text="2,500")[0].find_previous("b").find_previous("b")))
        except: rank = 0
        try: meaning = subsite.html(text=re.compile("Meaning: "))[0]
        except: meaning = ""
        try: kanji = subsite.html(text=re.compile("Meaning of"))[0].replace("Meaning of","").strip()
        except: kanji = ""

        for sentence in sentences:
            try:
                result.append({"Rank":rank,
                               "Kanji":kanji,
                               "Word":kanji,
                               "KPro":kpro,
                               "OPro":opro,
                               "Meaning":meaning,
                               "Sentence":sentence[0],
                               "Romaji":sentence[1],
                               "SMeaning":sentence[2]})
            except: None

        for kre in krea:
            try:
                result.append({"Rank":rank,
                               "Kanji":kanji,
                               "Word":kre[0],
                               "KPro":kre[1],
                               "OPro":"",
                               "Meaning":kre[2],
                               "Sentence":"",
                               "Romaji":"",
                               "SMeaning":""})
            except: None

        for ore in orea:
            try:
                result.append({"Rank":rank,
                               "Kanji":kanji,
                               "Word":ore[0],
                               "KPro":ore[1],
                               "OPro":"",
                               "Meaning":ore[2],
                               "Sentence":"",
                               "Romaji":"",
                               "SMeaning":""})
            except: None
    return result


def japaneseLesson(link):
    """
    PURPOSE

    Kanshudo has alot of useful Japanese lessons and grammar points, along with useful sentences.
    Based on a particular link from kanshudo, this function extracts alot of useful information and standardises them into sizeable lesson points.
    On its own, it's quite useless.
    So just use the japaneseLessonFull() function to get all the lessons at once, then decide from there what you want.
    """
    si = website(link)
    results = []
    for h4 in si.html('h4'):
        word = h4.get_text().split(' - Grammar')[0]
        level = 'N' + link[-1]
        transliteration = tryRomaji(word)
        purpose = 'Grammar'
        usage = h4.find_next('div').get_text()
        sentence = ''
        furigana = ''
        sentenceMeaning = ''
        details = h4.find_next(string='DETAILS')
        for sibling in list(details.parent.parent.next_siblings):
            try:
                text = sibling.get_text()
                try:
                    try: 
                        kanji = sibling.find(class_='f_kanji').get_text()
                        sentence += kanji
                        furi = sibling.find(class_='furigana').get_text()
                        furigana += furi
                        sentence += text.replace(kanji,'').replace(furi,'')
                    except:
                        sentence += text
                        furigana += text
                except:
                    sentence += text
                    furigana += text
            except: sentenceMeaning += sibling.strip()
        furigana = tryRomaji(sentence)
        results.append({'Word':word,
                        'Transliteration':transliteration,
                        'Purposes':purpose,
                        'Usages':usage,
                        'Examples':sentence,
                        'English':furigana,
                        'Translation':sentenceMeaning,
                        'Level':level,
                        'Link':link})
        
    if len(results) == 0:
        word = si.html.find('title').get_text().split(' - Grammar')[0]
        level = 'N' + link[-1]
        transliteration = tryRomaji(word)
        usage = ''
        
        for gpBody in si.html(class_='gp_body'):
            
            content = gpBody.contents
            purpose = 'Grammar'
            sentence = ''
            furigana = ''
            sentenceMeaning = ''
            counter = 1
            
            while(True):
                try: 
                    details = content[counter].find(string='DETAILS')
                    for sibling in list(details.parent.parent.next_siblings):
                        try:
                            text = sibling.get_text()
                            try:
                                try: 
                                    kanji = sibling.find(class_='f_kanji').get_text()
                                    sentence += kanji
                                    furi = sibling.find(class_='furigana').get_text()
                                    furigana += furi
                                    sentence += text.replace(kanji,'').replace(furi,'')
                                except:
                                    sentence += text
                                    furigana += text
                            except:
                                sentence += text
                                furigana += text
                        except: sentenceMeaning += sibling.strip()
                except: break
                counter += 2
            
            if 'DETAILS' not in content[1].get_text():
                usage = content[1].get_text()
                
            else:
                usage = content[1].find(class_='tatoeba').parent.previous_sibling.get_text()
            furigana = tryRomaji(sentence)
            results.append({'Word':word,
                        'Transliteration':transliteration,
                        'Purposes':purpose,
                        'Usages':usage,
                        'Examples':sentence,
                        'English':furigana,
                        'Translation':sentenceMeaning,
                        'Level':level,
                        'Link':link})
        
    return results

def japaneseLessonFull():
    """
    PURPOSE

    This function extracts all the lesson points from the 5 levels of the JLPT syllabus from Kanshudo.
    It gets pretty much the grammar points, their explanations, sample sentences etc.
    """
    masterResults = []

    for i in range(1,6):
        pageNum = 1
        while(True):
            print('JLPT N%d\nPage Number: %d' % (i,pageNum))
            try:
                link = 'https://www.kanshudo.com/searchg?page=' + str(pageNum) + '&q=jlpt:' + str(i)
                sit = website(link)
                hrefs = sit.html(href=re.compile(r'oq=jlpt:\d$'))

                if len(hrefs) == 0:
                    break

                for href in tqdm(hrefs):
                    try: masterResults.extend(japaneseLesson('https://www.kanshudo.com' + href['href']))
                    except: continue

            except Exception as e:
                print(e)
                break
            pageNum += 1
    return masterResults

### KOREAN
def tryKoreanRomanizer(x):
    """
    PURPOSE

    Extends the transliter.translit() function to allow for errors, converting Korean text to its romaji form.
    """
    try: return transliter.translit(x)
    except: return x


def tryHanja(x,tolerance=2):
    """
    PURPOSE

    Due to overlaps in language history, Korean words sometimes have Chinese origin.
    So as to make the learning experience easier, I've decided to map as many Korean words as I can into their Chinese form.
    I used the koreanhanja.app site to do my searching.
    It is also to be noted that inputting certain Korean words like "가" would yield a plethora of results.
    As such, I added the tolerance meter to only accept inputs whose lengths are more than the tolerance.
    """
    try:
        if len(x) >= tolerance:
            url = 'https://koreanhanja.app/%' + str(x.encode()).replace(r'\x','%')[3:-1]
            splitted = [i.getText() for i in website(url).html('a')]
            splitted = [trySimplified(i.strip()) for i in splitted]
            clean_splitted = list(filter(lambda y: re.search('[\u4e00-\u9fff]+',y),splitted))
            min_length = min([len(i.strip()) for i in clean_splitted])
            short_splitted = ', '.join(list(set(filter(lambda y: len(y) == min_length,clean_splitted))))
            return short_splitted
        else: return ''
    except: return ''


def koreanLesson(link):
    """
    PURPOSE

    howtostudykorean.com has a good collection of lessons laid out.
    As such, I decided to extract them out.
    This was much easier said than done, because there was alot of unstructured content in the site.
    There was alot of pattern-finding and regex searches to be done.
    Similar to japaneseLesson(), this function is useless on its own, just necessary for the koreanLessonFull function.
    """
    site = website(link)
    title = re.findall(r'Lesson \d+',site.html(class_='titlebar-title')[0].get_text())[0]
    words = {}
    for collapse in site.html(class_='collapseomatic'):
        word = collapse.find_previous('a').get_text()
        words.update({word:{}})
        try:
            words[word]['Meaning'] = collapse.get_text()
        except: continue
        try:
            maybe_common = collapse.find_next(string=re.compile('Common'))
            if maybe_common.find_next('a') == collapse.find_next('a'):
                words[word]['Common'] = maybe_common.parent.get_text().split('\n')[1:]
        except: continue
        try:
            maybe_examples = collapse.find_next(string=re.compile('Examples'))
            if maybe_examples.find_next('a') == collapse.find_next('a'):
                words[word]['Examples'] = [i.replace('\n',' ') for i in re.split('\n(?!=)',re.split('\n',maybe_examples.parent.get_text(),maxsplit=1)[1])]
        except: continue

    if len(words) == 0:
        for i in site.html(string=re.compile('^ = [a-z]')):
            words.update({i.find_previous('a').get_text():{'Meaning':i.split('=')[1].strip()}})
        
    if len(words) == 0:
        for i in re.findall('(.* = .{1,40})\n',site.html.get_text()):
            words.update({i.split(' = ')[0]:i.split(' = ')[1]})

    contents = {}
    hrefs = [x['href'][1:] for x in site.html(href=re.compile(r'^#\d'))]
    for href in hrefs:
        try:
            topic = site.html(attrs = {'name':href})[0].find_next('p',string=re.compile(r'\w'))
            topicText = topic.get_text()
            contents.update({topicText:{}})
            contents[topicText]['Link'] = link + '#' + href
            try:
                sentence = topic.find_next('a')
                sentenceText = sentence.get_text()
                contents[topicText]['Sentence'] = sentenceText
                meaningText = sentence.find_next('p').get_text()
                contents[topicText]['Meaning'] = meaningText
            except: continue
            numColon = 0
            intro = ''
            sentences = []
            currentTag = topic.find_next('p')

            while numColon == 0:
                try:
                    if ':' in currentTag.get_text():
                        numColon += 1
                        if '.' in currentTag.get_text():
                            intro += ' ' + currentTag.get_text()
                    else: intro += ' ' + currentTag.get_text()
                    currentTag = currentTag.find_next('p')
                except: break

            contents[topicText]['Intro'] = '.'.join(re.split(r'\.[^\.]',intro)[:5])
        except Exception as e: print(e)
    return {title:{'Link':link,'Words':words,'Contents':contents}}


def koreanLessonFull():
    """
    PURPOSE

    This function extracts all the lesson info from the howtostudykorean.com lesson plan.
    It gives the links to the lessons, the new vocabulary contained within them, as well as the contents for the lessons themselves.
    """
    site = website('https://www.howtostudykorean.com/other-stuff/lesson-list/')
    links = []
    for i in site.html(string=re.compile('Lesson ')):
        try: 
            link = i.find_previous('a')['href']
            if 'other-stuff' not in link:
                links.append(link)
        except: continue

    lessons = {}
    for link in tqdm(links):
        try:lessons.update(getLesson(link))
        except Exception as e:
            print(link)
            print(e)
    return lessons