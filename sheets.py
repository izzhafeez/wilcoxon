from gsheets import Sheets
import pandas as pd

vocabSheetId = '1m9J0FYZtODqZkeSm_5zAvVQC3Lgj3s5FaFN_AzU8hFA'
codingSheetId = '1euM-vhh5I4Y-WLrHqp5e1HTIbNOP4adrLuCMZ0pRRKQ'
geoSheetId = '1M9Ujc54yZZPlxOX3yxWuqcuJOxzIrDYz4TAFx8ifB8c'
musicSheetId = '1WbVcNLA4yKUJqn6w96ai-nflvQ-ASUscBUZxna3HMlQ'

def getVocab(name):
	sheets = Sheets.from_files('client_secrets.json','~/storage.json')[vocabSheetId]
	return sheets.find(name).to_frame()

def getCoding(name):
	sheets = Sheets.from_files('client_secrets.json','~/storage.json')[codingSheetId]
	return sheets.find(name).to_frame()

def getGeo(name):
	sheets = Sheets.from_files('client_secrets.json','~/storage.json')[geoSheetId]
	return sheets.find(name).to_frame()

def getMusic(name):
	sheets = Sheets.from_files('client_secrets.json','~/storage.json')[musicSheetId]
	return sheets.find(name).to_frame()