#!/usr/bin/env python3
"""Check completeness, per-character pinyin, audio identity and decodability."""
import concurrent.futures,hashlib,json,re,subprocess,tempfile,wave
from pathlib import Path
from lxml import etree as E
from opencc import OpenCC
ROOT=Path(__file__).resolve().parents[1]
NS={'t':'http://www.tei-c.org/ns/1.0','cb':'http://www.cbeta.org/ns/1.0'}
cc=OpenCC('t2s')
def han(s):return ''.join(c for c in s if '\u3400'<=c<='\u9fff' or '\U00020000'<=c<='\U000323af')
def main():
 data=json.loads((ROOT/'data/sutras.json').read_text());manifest=json.loads((ROOT/'audio/verses.json').read_text())
 notes=json.loads((ROOT/'sources/long_sutra_notes.json').read_text())
 records={(r['sutra'],r['index']):r for r in manifest['records']};report=[];paths=set()
 for s in data:
  if s['id'] in notes:assert len(notes[s['id']])==len(s['verses']),('commentary count',s['id'])
  raw=ROOT/'sources/user/taizang_nine.json' if s['id']=='taizang_nine' else ROOT/'sources/cbeta'/f'{s["sourceCode"]}.xml'
  assert hashlib.sha256(raw.read_bytes()).hexdigest()==s['sourceHash']
  body=E.parse(str(raw)).find('.//t:body',NS) if s['id']!='taizang_nine' else None
  if s['id']=='taizang_nine':
   supplied=json.loads(raw.read_text())['rows']
   assert len(supplied)==len(s['verses'])
   for row,v in zip(supplied,s['verses']):
    assert han(row['text'])==han(v['text']) and row['meaning']==v['meaning'],('user text/notes mismatch',s['id'])
   selected=[E.Element('p')];selected[0].text=''.join(row['text'] for row in supplied)
  elif s['id'] in ('ksitigarbha_sutra','lotus_sutra'):selected=body.xpath('./cb:div[@type="pin"]',namespaces=NS)
  elif s['id']=='pumen_pin':selected=[x for x in body.findall('cb:div',NS) if x.get('type')=='pin' and ''.join(x.itertext()).lstrip().startswith('25 ')]
  elif s['id']=='dabei_mantra':selected=[x for x in body.xpath('.//t:p[@cb:type="dharani"]',namespaces=NS) if '南無喝囉' in ''.join(x.itertext())]
  else:selected=body.xpath('./cb:div[@type="jing"]',namespaces=NS)
  assert len(selected)=={'ksitigarbha_sutra':13,'lotus_sutra':28}.get(s['id'],1)
  assert s['introduction'] and s['studySources']
  end=0
  for ch in s['chapters']:
   assert ch['start']==end and ch['end']>end
   end=ch['end']
  assert end==len(s['verses'])
  for root in selected:
   for el in list(root.iter())[::-1]:
    if E.QName(el).localname in ('note','mulu','head','juan','byline','docNumber'):
     # remove subtree but preserve following text
     if el.tail:
      prev=el.getprevious()
      if prev is not None:prev.tail=(prev.tail or '')+el.tail
      else:el.getparent().text=(el.getparent().text or '')+el.tail
     el.getparent().remove(el)
  expected=han(cc.convert(''.join(''.join(n.itertext()) for n in selected)))
  actual=han(''.join(v['text'] for v in s['verses']))
  assert actual==expected,('source text missing/reordered',s['id'])
  for i,v in enumerate(s['verses']):
   assert isinstance(v.get('meaning'),str) and len(v['meaning'].strip())>=15,('missing commentary',s['id'],i)
   if s['id'] in notes:
    assert notes[s['id']][i]=={'textHash':v['textHash'],'meaning':v['meaning']},('commentary mapping',s['id'],i)
   assert len(v['text'])==len(v['pinyin'].split()),('pinyin alignment',s['id'],i)
   assert not han(v['pinyin']),('unresolved reading',s['id'],i)
   assert v['textHash']==hashlib.sha256(v['text'].encode()).hexdigest()
   record=records[(s['id'],i)]
   for key in ['text','speechText','textHash','audio']:assert v[key]==record[key],(key,s['id'],i)
   f=ROOT/v['audio'];assert f.stat().st_size==record['bytes'];assert hashlib.sha256(f.read_bytes()).hexdigest()==record['audioHash']
   paths.add(v['audio'])
  report.append({'id':s['id'],'title':s['title'],'source':s['source'],'paragraphs':len(s['verses']),'annotatedParagraphs':sum(bool(v.get('meaning','').strip()) for v in s['verses']),'characters':len(actual)})
 assert len(records)==sum(x['paragraphs'] for x in report)
 def decode(path):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'decoded.wav';subprocess.run(['afconvert','-f','WAVE','-d','LEI16@16000','-c','1',str(ROOT/path),str(out)],check=True,capture_output=True)
   with wave.open(str(out)) as w:
    duration=w.getnframes()/w.getframerate();frames=w.readframes(w.getnframes())
    assert duration>0.3 and any(frames),('silent/empty audio',path)
   return duration
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:durations=list(pool.map(decode,sorted(paths)))
 result={'corpus':report,'audioFiles':len(paths),'audioSeconds':round(sum(durations),2),'sourceTextMatches':True,'pinyinAligned':True,'audioHashesMatch':True,'allAudioDecodes':True,'note':'Programmatic completeness and audio integrity checks; ASR spot checks are diagnostic, not a human pronunciation review.'}
 (ROOT/'data/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
