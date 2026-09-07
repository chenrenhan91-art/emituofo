"""Attach original explanatory notes to stable text and verified source anchors."""
import json, re
from pathlib import Path
from opencc import OpenCC
ROOT = Path(__file__).resolve().parents[1]
CC = OpenCC('t2s')
INTRO = [
 '以观照五蕴说明缘起性空：身心与世界依条件而成立，没有独立不变的自性。理解空，是为了减少执著与恐惧，并非否定生活与责任。',
 '围绕如何安住内心、降伏执著展开。布施、度众生与修善仍要认真做，同时不执著于自我、对象和功德的固定形象。',
 '本篇是《千手千眼观世音菩萨广大圆满无碍大悲心陀罗尼经》中的完整陀罗尼。汉字主要记录音声，不能逐字按现代汉语翻译；下方注释解释诵持背景与阅读方法。',
 '这是《法华经》第二十五品，以称名救苦与随类示现说明观世音的慈悲。长行与偈颂彼此呼应，读诵可联系日常倾听、安慰与帮助受苦者。',
 '描写极乐世界的修学环境，劝人发愿、执持佛名，并由诸佛劝信收束。庄严景象属于本经的净土信仰，修学方向包含专注、善行与不退转。',
 '以八项觉察联系无常、少欲、知足、精进、智慧、平等布施、节制与大悲。可逐项联系日常选择，让理解落实为行动。',
 '全经十三品，以地藏的久远愿行为中心，把孝亲报恩扩展到救助一切受苦众生。因果、忏悔、布施与回向相互联系，重点是停止伤害、持续修善和不舍弃他人。本底本分上下二卷。',
 '全经二十八品，以一佛乘说明不同教法共同引向佛的智慧。火宅、穷子、药草、化城等譬喻解释循序引导；后半展开菩萨愿行与受持实践。各品导读帮助理解结构，不能替代原文。'
]
def norm(text):
 return re.sub(r'[^\w]', '', CC.convert(text))
def attach(corpus):
 notes=json.loads((ROOT/'sources/verse_notes.json').read_text())
 guides=json.loads((ROOT/'sources/chapter_guides.json').read_text())
 hashes=json.loads((ROOT/'sources/verse_notes.hashes.json').read_text())
 for s,intro in zip(corpus,INTRO):
  s['introduction']=intro
  s['studySources']=[{'title':'CBETA 经文底本','url':s['source']}]
  reference={'ksitigarbha_sutra':'https://mantra.ddm.org.tw/about.php?no=43','lotus_sutra':'https://www.ddm.org.tw/event/edm/app/pages/page2-7.html','pumen_pin':'https://mantra.ddm.org.tw/about.php?no=48','amituo_sutra':'https://mantra.ddm.org.tw/about.php?no=46','dabei_mantra':'https://mantra.ddm.org.tw/about.php?no=35'}.get(s['id'])
  if reference:s['studySources'].append({'title':'法鼓山参考导读','url':reference})
  if s['id'] in notes:
   assert hashes[s['id']]==[v['textHash'] for v in s['verses']], 'Commentary text changed'
   assert len(notes[s['id']])==len(s['verses'])
   for v,n in zip(s['verses'],notes[s['id']]):v['meaning']=n
  if s['id'] in guides:
   assert len(guides[s['id']])==len(s['chapters'])
   for ch,g in zip(s['chapters'],guides[s['id']]):
    ch['summary']=g['summary']
    verses=s['verses'][ch['start']:ch['end']]
    texts=[norm(v['text']) for v in verses];full=''.join(texts)
    for anchor,note in g['notes']:
     pos=full.find(norm(anchor))
     assert pos>=0,(s['id'],ch['title'],anchor)
     offset=0
     for v,t in zip(verses,texts):
      if offset<=pos<offset+len(t):
       v['meaning']=(v.get('meaning','')+' '+note).strip();break
      offset+=len(t)
 # Keep the standalone chapter and its full-book counterpart consistent.
 pumen={v['textHash']:v['meaning'] for v in corpus[3]['verses']}
 for v in corpus[-1]['verses']:
  if v['textHash'] in pumen:v['meaning']=pumen[v['textHash']]
