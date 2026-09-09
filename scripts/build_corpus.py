#!/usr/bin/env python3
"""Build the complete reading corpus from preserved CBETA TEI sources.
Excludes editorial prefaces, colophons, variant notes and appended rituals.
The mantra is the complete dharani in T1060 (82 source-numbered clauses).
"""
import hashlib, json, re
from pathlib import Path
from lxml import etree as E
from opencc import OpenCC
from pypinyin import pinyin, load_phrases_dict, load_single_dict
ROOT=Path(__file__).resolve().parents[1]
NS={'t':'http://www.tei-c.org/ns/1.0','cb':'http://www.cbeta.org/ns/1.0'}
CC=OpenCC('t2s')
load_phrases_dict({w:[[p] for p in ps.split()] for w,ps in {
 '地藏':'dì zàng','宝藏':'bǎo zàng','忉利':'dāo lì','校量':'jiào liàng',
 '涌出':'yǒng chū','踊出':'yǒng chū','伽耶':'qié yē','阎浮':'yán fú',
 '阎罗':'yán luó','无尽意':'wú jìn yì','伽陀':'qié tuó',
 '那由他':'nà yóu tā','阿鞞':'ā pí','摩睺罗伽':'mó hóu luó qié',
 '干闼婆':'gān tà pó','毗舍离':'pí shè lí','舍宅':'shě zhái'
}.items()})
load_single_dict({ord(c):p for c,p in {'𪙁':'zhā','𡎰':'chí','𫖪':'kū','䟽':'shū'}.items()})
# Mandarin Buddhist readings; transliterations are Chinese readings, not Sanskrit reconstruction.
READINGS={'著衣':'zhuó yī','迦叶':'jiā shè','阿难':'ā nàn','无刹':'wú chà','憎恶人':'zēng è rén','行深':'xíng shēn','般若':'bō rě','般罗':'bō luó','南无':'ná mó','阿弥陀':'ā mí tuó','摩诃':'mó hē','菩提':'pú tí','萨埵':'sà duǒ','萨跢':'sà duǒ','伽蓝':'qié lán','伽罗':'qié luó','恒河':'héng hé','祇树':'qí shù','给孤独':'jǐ gū dú','舍卫':'shè wèi','舍利':'shè lì','降伏':'xiáng fú','三昧':'sān mèi','阿耨':'ā nòu','阿僧祇':'ā sēng qí','大乘':'dà shèng','小乘':'xiǎo shèng','辟支佛':'pì zhī fó','应供':'yìng gòng','供养':'gòng yǎng','天乐':'tiān yuè','音乐':'yīn yuè','伎乐':'jì yuè','雨天':'yù tiān','长老':'zhǎng lǎo','长者':'zhǎng zhě','增长':'zēng zhǎng','无量':'wú liàng','思量':'sī liáng','称名':'chēng míng','称赞':'chēng zàn','称念':'chēng niàn','称南无':'chēng ná mó','莎婆诃':'suō pó hē','娑婆诃':'suō pó hē','揭帝':'jiē dì','数怛':'shù dá','怛侄他':'dá zhí tuō','罣碍':'guà ài','阿他':'ā tuō','都曼':'dū màn','佛啰':'fó luó'}
load_phrases_dict({w:[[p] for p in ps.split()] for w,ps in READINGS.items()})
load_single_dict({ord(c):v for c,v in {'𤦲':'qú','𠰷':'lú','㖿':'yē','㘄':'léng','唵':'ōng','囇':'lì','嘇':'shān','诃':'hē','埵':'duǒ','跢':'duǒ','醯':'xī','咩':'miē','闍':'shé'}.items()})
SPEAK={'著衣':'卓衣','迦叶':'迦摄','阿难':'阿难' ,'无刹':'无岔','憎恶人':'憎饿人','行深':'形深','般若':'波惹','般罗':'波罗','南无':'拿摩','摩诃':'摩喝','给孤独':'几孤独','舍卫':'设卫','降伏':'祥伏','大乘':'大胜','小乘':'小胜','应供':'应贡','天乐':'天月','伎乐':'伎月','雨天':'玉天','莎婆诃':'娑婆喝','娑婆诃':'娑婆喝','𤦲':'渠','𠰷':'卢','㖿':'耶','㘄':'楞','唵':'嗡','囇':'利','嘇':'山','跢':'朵','埵':'朵','醯':'西','咩':'咩','闍':'蛇','诃':'喝','祇':'其'}
META=[('heart_sutra','T08n0251','般若波罗蜜多心经','心经','唐·玄奘译'),('diamond_sutra','T08n0235','金刚般若波罗蜜经','金刚经','姚秦·鸠摩罗什译'),('dabei_mantra','T20n1060','大悲心陀罗尼','大悲咒','唐·伽梵达摩译'),('pumen_pin','T09n0262','妙法莲华经·观世音菩萨普门品第二十五','普门品','后秦·鸠摩罗什译'),('amituo_sutra','T12n0366','佛说阿弥陀经','阿弥陀经','姚秦·鸠摩罗什译'),('eight_realizations','T17n0779','佛说八大人觉经','八大人觉经','后汉·安世高译')]
META += [('ksitigarbha_sutra','T13n0412','地藏菩萨本愿经','地藏经','唐·实叉难陀译'),('lotus_sutra','T09n0262','妙法莲华经','法华经','后秦·鸠摩罗什译')]
SPEAK.update({'地藏':'地葬','校量':'较量','忉利':'刀利','𪙁':'渣','𡎰':'池','𫖪':'枯','䟽':'书'})
load_phrases_dict({w:[[p] for p in ps.split()] for w,ps in {
 '觉悟':'jué wù','觉知':'jué zhī','正觉':'zhèng jué','行道':'xíng dào',
 '行菩萨道':'xíng pú sà dào','所行':'suǒ xíng','梵行':'fàn xíng',
 '还至':'huán zhì','复还':'fù huán','形为':'xíng wéi','释迦牟尼':'shì jiā móu ní',
 '无所得':'wú suǒ dé','有所得':'yǒu suǒ dé','七重':'qī chóng','七行':'qī háng',
 '一行':'yī háng','重说':'chóng shuō','重宣':'chóng xuān','童子':'tóng zǐ'
}.items()})
def textof(n):
 tag=E.QName(n).localname
 if tag in ('note','mulu','head','juan','byline','docNumber'):return ''
 if tag=='g':
  if not n.text:raise ValueError('unresolved gaiji '+str(n.attrib))
 return (n.text or '')+''.join(textof(c)+(c.tail or '') for c in n)
def clean(s):
 s=re.sub(r'[\n\r\t ]','',s)
 return CC.convert(s).replace('\u3000','，').strip('，')
def chunks(s):
 # Break at sentence/semicolon boundaries; preserve every character and its order.
 parts=re.findall(r'.+?(?:[。！？；][」』]?|$)',s)
 out=[]; cur=''
 for p in parts:
  if cur and len(cur)+len(p)>150:out.append(cur);cur=''
  cur+=p
 if cur:out.append(cur)
 assert ''.join(out)==s
 return out
def build():
 corpus=[]
 for sid,code,title,short,translator in META:
  path=ROOT/'sources/cbeta'/f'{code}.xml';r=E.parse(str(path));body=r.find('.//t:body',NS)
  if sid in ('ksitigarbha_sutra','lotus_sutra'):
   nodes=body.xpath('./cb:div[@type="pin"]',namespaces=NS)
   assert len(nodes)==(13 if sid=='ksitigarbha_sutra' else 28)
  elif sid=='pumen_pin':
   nodes=[x for x in body.findall('cb:div',NS) if x.get('type')=='pin' and ''.join(x.itertext()).lstrip().startswith('25 ')]; assert len(nodes)==1
  elif sid=='dabei_mantra':
   nodes=body.xpath('.//t:p[@cb:type="dharani"]',namespaces=NS)
   nodes=[x for x in nodes if '南無喝囉' in ''.join(x.itertext())];assert len(nodes)==1
  else:nodes=body.xpath('./cb:div[@type="jing"]',namespaces=NS)
  paragraphs=[]; chapters=[]
  if sid=='dabei_mantra':
   # The source's full-width spaces are the original clause boundaries.
   clauses=clean(textof(nodes[0])).strip('「」').split('，');assert len(clauses)==82,len(clauses)
   paragraphs=['。'.join(clauses[i:i+6])+'。' for i in range(0,82,6)]
  else:
   for n in nodes:
    start=len(paragraphs)
    for c in n:
     if E.QName(c).localname in ('p','lg'):
      t=clean(textof(c))
      if t:paragraphs+=chunks(t)
    mulu=n.find('cb:mulu',NS)
    title_text=clean(''.join(mulu.itertext())) if mulu is not None else '全文'
    chapters.append({'title':title_text,'start':start,'end':len(paragraphs)})
  full=''.join(paragraphs)
  assert len(full)>200
  verses=[]
  for t in paragraphs:
   sounds=[v[0] for v in pinyin(t,errors=lambda x:list(x))]
   # Phrase dictionaries can incorrectly assign secular readings to Buddhist names.
   for i,char in enumerate(t):
    if char in {'佛','觉','牟'}:sounds[i]={'佛':'fó','觉':'jué','牟':'móu'}[char]
   for word,reading in {**READINGS,'地藏':'dì zàng','虚空藏':'xū kōng zàng','善男子':'shàn nán zǐ','无间':'wú jiàn','相好':'xiàng hǎo','种善根':'zhòng shàn gēn'}.items():
    for match in re.finditer(re.escape(word),t):sounds[match.start():match.end()]=reading.split()
   py=' '.join(sounds)
   unknown=re.findall(r'[\u3400-\u9fff\U00020000-\U000323af]',py)
   if unknown:raise ValueError((sid,unknown))
   spoken=re.sub('|'.join(map(re.escape,sorted(SPEAK,key=len,reverse=True))),lambda m:SPEAK[m[0]],t)
   key=hashlib.sha256((t+'\0'+spoken+'\0Xiaoxiao:-18%:0Hz:v1').encode()).hexdigest()[:16]
   verses.append({'text':t,'pinyin':py,'speechText':spoken,'audio':f'audio/{sid}/{key}.mp3','textHash':hashlib.sha256(t.encode()).hexdigest()})
  corpus.append(dict(id=sid,title=title,shortTitle=short,translator=translator,category='完整咒文' if sid=='dabei_mantra' else '完整经文',source=f'https://cbetaonline.dila.edu.tw/zh/{code}',sourceCode=code,sourceHash=hashlib.sha256(path.read_bytes()).hexdigest(),verses=verses))
  corpus[-1]['chapters']=chapters or [{'title':'完整咒文','start':0,'end':len(verses)}]
  print(sid,len(verses),len(re.findall(r'[\u3400-\u9fff]',full)),full[:30],full[-45:])
 from user_corpus import build_user_liturgy
 corpus.append(build_user_liturgy(ROOT,READINGS,SPEAK))
 from annotations import attach
 attach(corpus)
 (ROOT/'data/sutras.json').write_text(json.dumps(corpus,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'data/sutras.js').write_text('/* Generated by scripts/build_corpus.py; do not edit. */\nconst SUTRA_DATABASE = '+json.dumps(corpus,ensure_ascii=False,separators=(',',':'))+';\n')
 # Tie the page and service-worker cache to the exact generated dataset.
 version='cbeta-'+hashlib.sha256((ROOT/'data/sutras.js').read_bytes()).hexdigest()[:12]
 page=ROOT/'index.html'
 html=page.read_text()
 html=re.sub(r'data/sutras.js\?v=[^"\s]+', 'data/sutras.js?v='+version, html)
 html=re.sub(r'const CORPUS_VERSION = "[^"]+"', 'const CORPUS_VERSION = "'+version+'"', html)
 html=re.sub(r'./sw.js\?v=[^"\s]+', './sw.js?v='+version, html)
 page.write_text(html)
 sw=ROOT/'sw.js';js=sw.read_text()
 js=re.sub(r'const CACHE = "[^"]+"', 'const CACHE = "lingtai-'+version+'"', js)
 js=re.sub(r'/data/sutras.js\?v=[^"\s]+', '/data/sutras.js?v='+version, js)
 sw.write_text(js)
if __name__=='__main__':build()
