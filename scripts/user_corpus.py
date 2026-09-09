"""Build the user-supplied liturgy without changing its wording."""
import hashlib, json, re
from html import unescape
from pypinyin import pinyin

def build_user_liturgy(root, standard_readings, standard_speech):
 path=root/'sources/user/taizang_nine.json'
 source=json.loads(path.read_text())
 readings={**standard_readings,'胎藏':'tāi zàng','毗卢遮那':'pí lú zhē nà','正等觉':'zhèng děng jué','三种':'sān zhǒng','种种':'zhǒng zhǒng','刹尘':'chà chén','刹土':'chà tǔ','法藏':'fǎ zàng','莲花藏':'lián huā zàng','宝幢':'bǎo chuáng','降三世':'xiáng sān shì','军荼利':'jūn tú lì','无暇':'wú xiá','降法雨':'jiàng fǎ yǔ'}
 speech={**standard_speech,'胎藏':'胎葬','毗卢遮那':'皮卢遮纳','宝幢':'宝床','降三世':'祥三世','军荼利':'军图利','刹土':'岔土','刹尘':'岔尘'}
 readings.update({'佛子':'fó zǐ','尽皆':'jìn jiē','尽十方':'jìn shí fāng','尽无余':'jìn wú yú'})
 speech.update({'佛子':'佛紫','尽皆':'进皆','尽十方':'进十方','尽无余':'进无余','一切恭敬敬礼':'一切恭敬，敬礼'})
 verses=[]
 for row in source['rows']:
  text=re.sub(r'\s+', '，', unescape(row['text']).strip())
  if text[-1] not in '。！？':text+='。'
  sounds=[v[0] for v in pinyin(text,errors=lambda x:list(x))]
  for word,reading in readings.items():
   for match in re.finditer(re.escape(word),text):sounds[match.start():match.end()]=reading.split()
  for i,c in enumerate(text):
   if c=='佛':sounds[i]='fó'
  spoken=text
  # Add breath groups to the two long unpunctuated lines; every source word stays audible.
  for before,after in {
   '普为五类诸天众九际世出世父母诸善知识道场施主一切金刚护持者尽无余界一切有情并愿断除诸障皈命礼忏悔':'普为五类诸天众，九际世出世父母，诸善知识，道场施主，一切金刚护持者，尽无余界一切有情，并愿断除诸障，皈命礼忏悔',
   '尽十方莲花藏世界海不可说不可说微尘刹土海会中常住三世平等一切三宝':'尽十方莲花藏世界海，不可说不可说微尘刹土海会中，常住三世平等一切三宝'
  }.items():spoken=spoken.replace(before,after)
  spoken=re.sub('|'.join(map(re.escape,sorted(speech,key=len,reverse=True))),lambda m:speech[m[0]],spoken)
  key=hashlib.sha256((text+'\0'+spoken+'\0Xiaoxiao:-18%:0Hz:v1').encode()).hexdigest()[:16]
  verses.append({'text':text,'pinyin':' '.join(sounds),'speechText':spoken,'audio':f'audio/taizang_nine/{key}.mp3','textHash':hashlib.sha256(text.encode()).hexdigest(),'meaning':row['meaning']})
 return {'id':'taizang_nine','title':source['title'],'shortTitle':source['title'],'translator':'用户提供全文','category':'礼诵仪文','source':'sources/user/taizang_nine.json','sourceLabel':'所用底本','sourceCode':'USER-TAIZANG-NINE','sourceHash':hashlib.sha256(path.read_bytes()).hexdigest(),'introduction':'本篇依次展开归命、出罪、皈依、施身、发心、随喜、劝请、安住法身与回向九种方便，接续称名礼敬和清净偈。可把握恭敬、悔过、发愿、利他这一贯穿全文的方向。正文依用户提供版本保留，白话注释帮助理解各段大意。','studySources':[{'title':'用户提供底本','url':'sources/user/taizang_nine.json'}],'chapters':[{'title':'全文','start':0,'end':len(verses)}],'verses':verses}
