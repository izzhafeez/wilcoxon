import telepot
from datetime import datetime as dt
from datetime import timedelta as td
import numpy as np
import json
import requests

def getChatIds(botId, onlyId = False):
    """
    PURPOSE

    Obtain all the chatIds that the bot is chatting with.
    This includes all the group chats as well.

    PARAMETERS

    botId [str]: botId of the bot in question
    onlyId [str]: setting it to False will also return the username of the accounts

    OUTPUT

    List of unique ids.
    """
    data = json.loads(requests.get(f'https://api.telegram.org/bot{botId}/getUpdates').text)
    if onlyId:
        return list(set(x['message']['chat']['id'] for x in data['result']))
    else:
        return list(set([(x['message']['chat']['username'], x['message']['chat']['id']) for x in data['result']]))


class Telegram:
    """
    PURPOSE

    This class is meant to wrap around the iterable in the loop.
    So in the case of a for loop, it can be wrapped like this:

    for x in Telegram(range(0,20), params):
        print(x)

    What the function does is send a progress update after a set time interval.
    Basically, after every iteration, the code checks how much time has elapsed since the previous message.
    If that time exceeds the time interval, the message is sent and the timer is reset.
    The message sent can be customised, and will include the percentage of the loop that has been completed.
    The code works best if the number of repetitions is high, and each loop takes a long time to run.
    The code sends messages regarding the datetimes that the loop started and ended.

    PARAMETERS

    iterable [iterable]: something that is iterable
    chatIds [str, list]: the chatIds of the accounts you want to send a message to
    botId [str]: the id of the Telegram bot
    params [dict]: An alternative method to input the parameters.
                   If you have the parameters saved in a variable, there is no need to type in the values for each of them.
                   You can just put params = params.
                   In the dictionary, the keys should be the parameter name as a string, and the value can be whatever you want.
    start [str]: the message you want to send to the user when the loop is starting
    end [str]: the message you want to send to the user when the loop has been completed
    middle [str]: The message you want to send to the user whenever the time interval is met.
                  By default, it will just show a percentage, but changing this parameter allows you to add text to the back of this percentage.
                  So it's just like appending.
    timing [float]: the time interval, in minutes
    date [str]: the default format of the datetimes in this is '%H:%M:%S %d %b %y', but this can be changed

    OUTPUT

    List of unique ids.
    """
    def __init__(self,
                 iterable,
                 chatIds = None,
                 botId = None,
                 params = {},
                 start = None,
                 middle = None,
                 timing = 0,
                 end = None,
                 date = '%H:%M:%S %d %b %y'):
        
        Params = {'chatIds': chatIds,
                  'botId': botId,
                  'start': start,
                  'middle': middle,
                  'timing': timing,
                  'end': end,
                  'date': date}
        
        Params.update(params)
        chatIds = Params['chatIds']
        Params['chatIds'] = [chatIds] if type(chatIds) != list else chatIds
        Params['bot'] = telepot.Bot(Params['botId'])
        
        self.iterable = iterable
        self.params = Params
        
        
    def __iter__(self):
        
        self.startTime = dt.now()
        self.periodStartTime = self.startTime
        
        if self.params['start'] != None:
            print(self.params['start'])
            for chatId in self.params['chatIds']:
                self.params['bot'].sendMessage(chatId,self.params['start'])
        
        try:
            print('Started: %s' % self.startTime.strftime(self.params['date']))
        except: pass
        
        if type(self.iterable) == list:
            self.len = len(self.iterable)
            
        elif type(self.iterable) == int:
            self.len = self.iterable
        
        else:
            raise Exception('iterable must be int or list')
            
        print('Total: %d' % self.len)
        
        self.n = 0
        return self
    
    def __next__(self):
        
        now = dt.now()
        timeElapsed = (now - self.periodStartTime).total_seconds()/60
        
        if self.n < self.len:
            
            if self.params['timing'] <= 0:
                pass
            
            elif type(self.params['timing']) not in [float,int]:
                print('invalid timing')
            
            elif timeElapsed > self.params['timing']:
                
                totalTimeElapsed = (now - self.startTime).total_seconds()/60
                percentageDone = str(round(self.n / self.len * 100, 1))
                
                try:
                    for chatId in self.params['chatIds']:
                        self.params['bot'].sendMessage(chatId,str(percentageDone) + "%" + self.params['middle'])
                except Exception as e:
                    print(e)

                timeToAdd = totalTimeElapsed - totalTimeElapsed % self.params['timing']
                self.periodStartTime = self.startTime + td(minutes = timeToAdd)
            
            if type(self.iterable) == list:
                current = self.iterable[self.n]
            else:
                current = self.n
            
            self.n += 1
            return current
        
        else: 
            
            if self.params['end'] != None:
                print(self.params['end'])
                for chatId in self.params['chatIds']:
                    self.params['bot'].sendMessage(chatId,self.params['end'])
                    
            totalTimeElapsed = (dt.now() - self.startTime).total_seconds()/60
            try: print('Duration: %f mins' % totalTimeElapsed)
            except Exception as e: print(e)
            try: print('Ended: %s' % dt.now().strftime(self.params['date']))
            except: pass
            raise StopIteration

