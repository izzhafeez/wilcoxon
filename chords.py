from .spiderman import *
import re
import json
import numpy as np
import pychord
import operator
import copy
import pandas as pd
import collections
from tqdm import tqdm
import time

"""
PURPOSE

These are the collections of notes for each major scale.
Normally, many libraries have this the standard collection of notes.
However, I want all the different enharmonic notes (C# and Db for instance)
This will be useful later.
"""
scales = {
    "C": {"C","D","E","F","G","A","B"},
    "C#": {"Db","Eb","F","Gb","Ab","Bb","C","C#","D#","F#","G#","A#"},
    "Db": {"Db","Eb","F","Gb","Ab","Bb","C","C#","D#","F#","G#","A#"},
    "D": {"D","E","F#","G","A","B","C#","Gb","Db"},
    "D#": {"Eb","F","G","Ab","Bb","C","D","D#","G#","A#"},
    "Eb": {"Eb","F","G","Ab","Bb","C","D","D#","G#","A#"},
    "E": {"E","F#","G#","A","B","C#","D#","Gb","Ab","Db","Eb"},
    "F": {"F","G","A","Bb","C","D","E","A#"},
    "F#": {"F#","G#","A#","B","C#","D#","E#","Gb","Ab","Db","Eb","F"},
    "Gb": {"F#","G#","A#","B","C#","D#","E#","Gb","Ab","Db","Eb","F"},
    "G": {"G","A","B","C","D","E","F#","Gb"},
    "G#": {"Ab","Bb","C","Db","Eb","F","G","G#","A#","C#","D#"},
    "Ab": {"Ab","Bb","C","Db","Eb","F","G","G#","A#","C#","D#"},
    "A": {"A","B","C#","D","E","F#","G#","Db","Gb","Ab"},
    "A#": {"Bb","C","D","Eb","F","G","A","A#","D#"},
    "Bb": {"Bb","C","D","Eb","F","G","A","A#","D#"},
    "B": {"B","C#","D#","E","F#","G#","A#","Db","Eb","Gb","Ab","Bb"}
}

def guessLen(seq):
    """
    PURPOSE

    This entire package is about standardising the chords used in songs, in order to find patterns within them.
    As such, one such standardisation method is to find patterns within the chord progressions.
    This function attempts to find whether the chord progression is of length 3, 4 or whatever.
    Only with this can the progression be analysed.
    """
    max_len = int((len(seq) - (len(seq) % 2)) / 2) + 1
    for x in range(2, max_len):
        if seq[0:x] == seq[x:2*x]:
            return x
    return len(seq)

def searchSong(song, artist):
    """
    PURPOSE

    Based on the song and artist, the function first searches for all user-generated tab sheets on the ultimate-guitar.com site.
    Then, from there, each page is extracted, and with a bunch of bs4 searches, the chords are extracted, along with the section of the song (verse, chorus, etc.) they came from.
    Afterwards, the function decides how long the chord progression is, based on some pattern recognition, retrieving only theese repeated patterns.
    Finally, extract out any other useful information to machine learning and return all the data extracted from all the pages.

    OUTPUT

    List containing the set of works when searching for that artist and song.
    It contains quite alot of useful information.
    """
    fullLinkResults = []
    searchParam = "+".join(artist.split()) + "+" + "+".join(song.split())
    page = 1
    
    while (True):
        
        site = website(f"https://www.ultimate-guitar.com/search.php?title={searchParam}&page={page}&type=300")
        
        try:
            linkResults = json.loads(site.html(class_="js-store")[0]["data-content"])["store"]["page"]["data"]["results"]
            linkResults = list(filter(lambda x: "id" in x, linkResults))
        except: break
            
        page += 1
        
        fullLinkResults.extend(linkResults)
    
    endResults = []
    
    for index, link in enumerate(fullLinkResults):
        
        try:
        
            link = link["tab_url"]

            subsite = website(link)

            tabJson = json.loads(subsite.html(class_="js-store")[0]["data-content"])["store"]["page"]["data"]["tab_view"]["wiki_tab"]["content"]
            statsJson = json.loads(subsite.html(class_="js-store")[0]["data-content"])["store"]["page"]["data"]["tab_view"]["stats"]
            htmlTitle = subsite.html.find("title").string
            songName = htmlTitle.split("CHORDS")[0].strip().capitalize()
            artistName = htmlTitle.split(" by ", 1)[1].split("@")[0].strip()

            # Finds all section names and chords
            allResults = re.findall(r"((?<=\[ch\]).*?(?=\[/ch\])|\[[A-Z].+\])", tabJson)
            # Finds all section names with enumeration
            filteredResults = [(i, x.replace("[", "").replace("]", "")) for i, x in enumerate(allResults) if re.compile(r"\[.*\]").search(x)]
            # Section names only
            sectionNames = [x[1] for x in filteredResults]

            sections = {}
            for sectionNumber in range(len(filteredResults)):
                try:
                    chordsInSection = allResults[filteredResults[sectionNumber][0] + 1 : filteredResults[sectionNumber + 1][0]]
                    sectionName = filteredResults[sectionNumber][1]
                    if sectionNames.count(sectionName) != 1:
                        sectionName = sectionName + " " + str(sectionNames[:sectionNumber + 1].count(sectionName))
                    if len(chordsInSection) % 7 == 0 and chordsInSection[0:3] == chordsInSection[4:7]:
                        sections[sectionName] = chordsInSection[0:4]
                    else:
                        guessedLen = guessLen(chordsInSection)
                        if guessedLen > 8 and guessLen(chordsInSection[:-1]) < 8:
                            sections[sectionName] = chordsInSection[:guessLen(chordsInSection[:-1])]
                        else:
                            sections[sectionName] = chordsInSection[:guessedLen]

                except Exception as e:
                    chordsInSection = allResults[filteredResults[sectionNumber][0] + 1: ]
                    sectionName = filteredResults[sectionNumber][1]
                    if sectionNames.count(sectionName) != 1:
                        sectionName = sectionName + " " + str(sectionNames[:sectionNumber + 1].count(sectionName))
                    if len(chordsInSection) % 7 == 0 and chordsInSection[0:3] == chordsInSection[4:7]:
                        sections[sectionName] = chordsInSection[0:4]
                    else:
                        guessedLen = guessLen(chordsInSection)
                        if guessedLen > 8 and guessLen(chordsInSection[:-1]) < 8:
                            sections[sectionName] = chordsInSection[:guessLen(chordsInSection[:-1])]
                        else:
                            sections[sectionName] = chordsInSection[:guessedLen]

            # Average chord length of section
            simplicity = np.mean(list(filter(lambda x: x > 0, [len(sections[section]) for section in sections])))

            # Average word length of chords
            allChordsInBrackets = [sections[section] for section in sections]
            allChords = [item for sublist in allChordsInBrackets for item in sublist]
            complexity = np.mean([len(chord
                                      .replace("m", "")
                                      .replace("b", "")
                                      .replace("#", "")) for chord in allChords])
            
            views = int(statsJson["view_total"])
            favorites = int(statsJson["favorites_count"])
            popularity = favorites / views

            endResults.append({"Song": songName,
                               "Artist": artistName,
                               "Tabs": sections,
                               "Simplicity": simplicity,
                               "Complexity": complexity,
                               "Views": views,
                               "Favorites": favorites,
                               "Popularity": popularity,
                               "Link": link})
        
        except Exception as e: print(e)
        
    setOfWorks = list(filter(lambda x: not np.isnan(x["Simplicity"]) and not "Mashup" in x["Artist"] and all([len(x) <= 16 and "ch" not in "".join(x) for x in x["Tabs"].values()]), endResults))
    
    return setOfWorks

def cleanSong(setOfWorks):
    """
    PURPOSE

    I conducted quite alot of machine learning projects regarding the chord progressions of songs.
    As such, to clean the data, I needed to standardise the data as much as possible.
    Of course, every song can be in a different key, so standardising them all to be in C major is the big first step.
    This turned out to be quite difficult so I managed a decent workaround with a close to 100% success rate for songs without a change in key.
    For each chord in the progression, extract out all the notes within it.
    Then, it is a matter of counting the occurrences of each note.
    Based on the 7 most common notes in the song, output the appropriate scale by some mapping.
    Then, once you know the scale of the song, it is much easier to convert it into C major.
    """
    newSetOfWorks = copy.deepcopy(setOfWorks)

    for index, work in enumerate(setOfWorks):

        try:

            progression = pychord.ChordProgression(
                [item for sublist in list(work["Tabs"].values()) for item in sublist])
            noteSet = set([item for sublist in [x.components() for x in progression] for item in sublist])
            notesUsed = collections.Counter([item for sublist in [x.components() for x in progression] for item in sublist])
            
            while len(noteSet) > 7:
                noteSet = noteSet - {min(notesUsed.items(),key=operator.itemgetter(1))[0]}
                
            notesUsedSorted = list(dict(sorted(notesUsed.items(), key = operator.itemgetter(1), reverse = True)).keys())
            scaleDiff = {x: noteSet - scales[x] for x in scales.keys()}
            scaleMinNum = min([len(noteSet - scales[x]) for x in scales.keys()])
            scaleWithMinNum = [x for x in scaleDiff.keys() if len(scaleDiff[x]) == scaleMinNum]
            scaleMin = [tuple for x in notesUsedSorted for tuple in scaleWithMinNum if tuple[0] == x][0]
            
            toTranspose = pychord.analyzer.notes_to_positions([scaleMin], "C")[0]

            newSetOfWorks[index].pop("Tabs", None)

            for section in work["Tabs"]:

                if section[0] == "I":
                    cleanedSection = section[:5].capitalize()
                else:
                    cleanedSection = section[0] + re.findall(r"\d*$", section)[0]

                sectionProgression = pychord.ChordProgression(work["Tabs"][section])
                sectionProgression.transpose(-toTranspose)
                newSetOfWorks[index][cleanedSection] = {"-".join([str(chord) for chord in sectionProgression])}
                try:
                    newSetOfWorks[index][re.sub(r"\d*", "", cleanedSection)].append("-".join([str(chord) for chord in sectionProgression]))
                except:
                    newSetOfWorks[index][re.sub(r"\d*", "", cleanedSection)] = {"-".join([str(chord) for chord in sectionProgression])}
        except: continue
    
    return newSetOfWorks

def findBPM(song, artist):
    """
    PURPOSE

    Find the BPM of the song based on its title and artist.
    """
    searchParam = "+".join(artist.split()) + "+" + "+".join(song.split())
    site = website(f"https://tunebat.com/Search?q={searchParam}")
    
    try: 
        bpm = int(site.html(class_ = "search-attribute-value")[2].string)
        scale = site.html(class_ = "search-attribute-value")[0].string
        return {"BPM": bpm, "Scale": scale}
    except: return {"BPM": 0, "Scale": ""}