# from flask import Flask, render_template, request
import spacy
import sys,json
from nltk.tag import pos_tag
from flask import Flask
from flask import request
# from google_trans_new import google_translator
from langdetect import detect
from collections import OrderedDict
from googletrans import Translator

app  = Flask(__name__)

#translate text from one langauge to another
def translateText(text,src,dest):
	translator = Translator()
	translate_text = translator.translate(text, src=src, dest=dest)
	return translate_text.text

#detect the langauge of the textual information
def detectLang(text):
	return detect(text)

def merge_phrases(doc):
    with doc.retokenize() as retokenizer:
        for np in list(doc.noun_chunks):
            attrs = {
                "tag": np.root.tag_,
                "lemma": np.root.lemma_,
                "ent_type": np.root.ent_type_,
            }
            retokenizer.merge(np, attrs=attrs)
    return doc

def getTitles(sentences):
	nlp = spacy.load("en_core_web_sm")
	doc = nlp(sentences)
	result = merge_phrases(doc)
	final = []
	for i in result:
		if i.pos_ == 'NOUN':
			final.append(i.text)
	if final == []:
		for i in result:
			if i.pos_ == 'VERB':
				final.append(i.text)
	print(final)
	return final

#fetching possible titles when the textual information is English
def enTitles(textualinfo):
	sentences_with_nouns = []
	others = []
	foundThe = False
	result = getTitles(textualinfo)
	result.sort(key=lambda x: len(x.split(' ')) , reverse=True)
	for word in result:
		if len(word) > 1:
			sentences_with_nouns.append(str(word))
		else:
			others.append(str(word))
	# print(sentences_with_nouns)
	nlst = []
	for eachWord in sentences_with_nouns:
		word_posNew = [pos_tag([i]) for i in str(eachWord).split(' ')]
		flat_list = [item for sublist in word_posNew for item in sublist]
		# print("flat_list::", flat_list)
		if flat_list[0][1] == 'DT':  # or i[1] == 'PRP$':
			foundThe = True
			title = str(eachWord).replace(flat_list[0][0],"")
			lenWord = len(str(title).strip().split(' '))
			dicT = OrderedDict()
			dicT['title'] = title
			dicT['length'] = lenWord
			# dicT['foundThe'] = foundThe
			nlst.append(dicT)
			dicT = {}
		else:
			foundThe = False
			title = str(eachWord)
			lenWord = len(str(title).strip().split(' '))
			dicT = OrderedDict()
			dicT['title'] = title
			dicT['length'] = lenWord
			# dicT['foundThe'] = foundThe
			nlst.append(dicT)
			dicT = {}
	message = nlst
	return message

#fetching possible titles when the textual information is Hebrew
def heTitles(tranlated_text):
	sentences_with_nouns = []
	others = []
	foundThe = False
	result = getTitles(tranlated_text)
	result.sort(key=lambda x: len(x.split(' ')), reverse=True)
	for word in result:
		if len(word.split(" ")) <= 4:
			sentences_with_nouns.append(str(word))
		else:
			others.append(str(word))
	print(sentences_with_nouns)
	nlst = []
	l  = max(len(s.split(" ")) for s in sentences_with_nouns)
	print("l::", l)
	for eachWord in sentences_with_nouns:
		leneachWord = (len(str(eachWord).strip().split(' ')))
		print(leneachWord)
		if leneachWord == l:
			word_posNew = [pos_tag([i]) for i in str(eachWord).split(' ')]
			flat_list = [item for sublist in word_posNew for item in sublist]
			if flat_list[0][1] == 'DT':
				title = str(eachWord).replace(flat_list[0][0], "")
				titleNew = translateText(title,'en','he')
				print(titleNew)
				dicT = {'title' :  titleNew , 'translated_text': title , "titleCount" : len(titleNew.strip().split(" ")) , "includeDASH" : False}
				nlst.append(dicT)
				dicT = {}
			else:
				titleNew = translateText(str(eachWord), 'en', 'he')
				dicT = {'title' :  titleNew , 'translated_text' : eachWord ,"titleCount" : leneachWord , "includeDASH" : False}
				nlst.append(dicT)
				dicT = {}
		else:
			pass
	return nlst

def countOccurences(str, word):
	wordslist = list(str) #.split(' '))
	# print(wordslist)
	return wordslist.count(word)

def getkeywordwithoutMerge(sentences):
	nlp = spacy.load("en_core_web_sm")
	doc = nlp(sentences)
	#noun with root
	final = [(i.text) for i in doc if (i.pos_ =='NOUN' or i.pos_ == 'PROPN') and i.dep_ == 'ROOT']
	if final == []:
		final = [(i.text) for i in doc if (i.pos_ == 'NOUN' or i.pos_ == 'PROPN')]
		if final == []:
			final = [(i.text) for i in doc if i.dep_ == 'ROOT']
			final1 = final[0]
			isRoot = True
			isLastNoun = False
		else:
			final1 = final[-1]
			isRoot = False
			isLastNoun = True
	else:
		final1 = final[0]
		isRoot = True
		isLastNoun = False
	data = [{"keyword" : final1 , "isRoot" : isRoot, "isLastNoun" : isLastNoun}]
	return data

@app.route('/getTitles/', methods=['post', 'get'])
def getTitle():
	data_to_return = OrderedDict()
	if request.method == 'POST':
		textualinfo = request.json['text']
		if detectLang(textualinfo) == 'en':
			message = enTitles(textualinfo)
			message = sorted(message, key=lambda k: k['length'], reverse=True)
			data_to_return = {"original_sentence": textualinfo, "details":message}

		elif detectLang(textualinfo) == 'he':
			colonOccurence = countOccurences(str(textualinfo), ':')
			if colonOccurence == 1:
				indexOfColon = textualinfo.index(':')
				beforeElem = indexOfColon-1
				afterElem = indexOfColon+1
				if textualinfo[beforeElem] == ' ' or textualinfo[afterElem] == ' ':
					textualInfo1 = textualinfo.split(':')[0]
					countChars = len(textualInfo1.strip().split(" "))
					if countChars <= 3:
						titleNew = textualInfo1
						message = [{"title": titleNew, "translated_text": translateText(str(titleNew), 'he', 'en'),
									"titleCount": countChars, "includeDASH": True}]
						message1 = sorted(message, key=lambda k: k['titleCount'], reverse=True)
					else:
						tranlated_text = translateText(textualInfo1, 'he', 'en')
						message = heTitles(tranlated_text)
						message1 = sorted(message, key=lambda k: k['titleCount'], reverse=True)
				else:
					dashOccurence1 = countOccurences(str(textualinfo), '–')
					dashOccurence2 = countOccurences(str(textualinfo), '-')
					indexOfDash1 = textualinfo.index('–') if '–' in textualinfo else 99
					indexOfDash2 = textualinfo.index('-') if '-' in textualinfo else 99
					if dashOccurence1 == 1 or dashOccurence2 == 1:
						if indexOfDash1 < indexOfDash2:
							textualInfo1 = textualinfo.split('–')[0]
						else:
							textualInfo1 = textualinfo.split('-')[0]
						countChars = len(textualInfo1.strip().split(" "))
						if countChars <= 3:
							titleNew = textualInfo1
							message = [{"title": titleNew, "translated_text": translateText(str(titleNew), 'he', 'en'),
										"titleCount": countChars, "includeDASH": True}]
							message1 = sorted(message, key=lambda k: k['titleCount'], reverse=True)
						else:
							tranlated_text = translateText(textualInfo1, 'he', 'en')
							message = heTitles(tranlated_text)
							message1 = sorted(message, key=lambda k: k['titleCount'], reverse=True)
					else:
						wordCount = len(textualinfo.split(" "))
						if wordCount <= 3:
							titleNew = textualinfo
							message = [{"title": titleNew, "translated_text": translateText(str(titleNew), 'he', 'en'),
										"titleCount": len(titleNew.strip().split(" ")), "includeDASH": False}]
							message1 = sorted(message, key=lambda k: k['titleCount'], reverse=True)
						else:
							tranlated_text = translateText(textualinfo, 'he', 'en')
							message = heTitles(tranlated_text)
							message1 = sorted(message, key=lambda k: k['titleCount'], reverse=True)
			else:
				dashOccurence1 = countOccurences(str(textualinfo), '–')
				dashOccurence2 = countOccurences(str(textualinfo), '-')
				indexOfDash1 = textualinfo.index('–') if '–' in textualinfo else 99
				indexOfDash2 = textualinfo.index('-') if '-' in textualinfo else 99
				if dashOccurence1 == 1 or dashOccurence2 == 1:
					if indexOfDash1 < indexOfDash2:
						textualInfo1 = textualinfo.split('–')[0]
					else:
						textualInfo1 = textualinfo.split('-')[0]
					countChars = len(textualInfo1.strip().split(" "))
					if countChars <=3:
						titleNew = textualInfo1
						message = [{"title": titleNew, "translated_text": translateText(str(titleNew), 'he', 'en'), "titleCount": countChars , "includeDASH" : True}]
						message1 = sorted(message, key=lambda k: k['titleCount'], reverse=True)
					else:
						tranlated_text = translateText(textualInfo1, 'he', 'en')
						message = heTitles(tranlated_text)
						message1 = sorted(message, key=lambda k: k['titleCount'], reverse=True)
				else:
					wordCount = len(textualinfo.split(" "))
					if wordCount <= 3:
						titleNew = textualinfo
						message = [{"title": titleNew, "translated_text": translateText(str(titleNew), 'he', 'en'),
									"titleCount": len(titleNew.strip().split(" ")), "includeDASH": False}]
						message1 = sorted(message, key=lambda k: k['titleCount'], reverse=True)
					else:
						tranlated_text = translateText(textualinfo, 'he', 'en')
						message = heTitles(tranlated_text)
						message1 = sorted(message, key=lambda k: k['titleCount'], reverse=True)

			translatedText = message1[0]['translated_text']
			keywordDetails = getkeywordwithoutMerge(translatedText)

			data_to_return =  {"original_sentence": textualinfo, "details" : message1 , "keyword": keywordDetails}
	return json.dumps(data_to_return)



if __name__ == '__main__':
	app.run(debug=True)
