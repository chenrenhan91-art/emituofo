#!/usr/bin/env python3
"""Generate content-addressed neural recitation from the canonical corpus.
Whole paragraphs preserve prosody. Punctuation supplies phrase pauses; the
player adds a 500 ms breath between paragraphs. Existing successful files
are reusable; manifest is written only after ALL audio has been generated.
"""
import asyncio, hashlib, json
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parents[1]
VOICE='zh-CN-XiaoxiaoNeural'
RATE='-18%'
async def main():
 data=json.loads((ROOT/'data/sutras.json').read_text());gate=asyncio.Semaphore(3)
 total=sum(len(s['verses']) for s in data);done=0
 async def one(s,i,v):
  nonlocal done
  dest=ROOT/v['audio'];dest.parent.mkdir(parents=True,exist_ok=True)
  async with gate:
   if not(dest.exists() and dest.stat().st_size>1000):
    for attempt in range(5):
     try:
      tmp=dest.with_suffix('.part.mp3')
      await edge_tts.Communicate(v['speechText'],VOICE,rate=RATE,pitch='+0Hz').save(str(tmp))
      if tmp.stat().st_size<1000:raise ValueError('empty recording')
      tmp.replace(dest);break
     except Exception:
      if attempt==4:raise
      await asyncio.sleep(2*(attempt+1))
   done+=1;print(f'{done}/{total} {s["id"]} {i+1}',flush=True)
   return {'sutra':s['id'],'index':i,'text':v['text'],'speechText':v['speechText'],'textHash':v['textHash'],'audio':v['audio'],'audioHash':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size}
 records=await asyncio.gather(*(one(s,i,v) for s in data for i,v in enumerate(s['verses'])))
 (ROOT/'audio/verses.json').write_text(json.dumps({'voice':VOICE,'rate':RATE,'pitch':'+0Hz','paragraphPauseMs':500,'records':records},ensure_ascii=False,indent=2)+'\n')
 print('All audio generated and manifest committed.',flush=True)
if __name__=='__main__':asyncio.run(main())
