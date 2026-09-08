"""Reject the omissions and paragraph drift that previously reached the reader."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from annotations import attach, ROOT

class AnnotationCoverage(unittest.TestCase):
 def test_invalid_long_notes_are_rejected(self):
  corpus=json.loads((ROOT/'data/sutras.json').read_text())
  path=ROOT/'sources/long_sutra_notes.json'
  original=json.loads(path.read_text())
  read_text=Path.read_text
  for problem in ('missing','empty','shifted'):
   notes=copy.deepcopy(original)
   rows=notes['lotus_sutra']
   if problem=='missing':rows.pop(47)
   elif problem=='empty':rows[47]['meaning']=' '
   else:rows[47],rows[48]=rows[48],rows[47]
   def read(p,*args,**kwargs):
    return json.dumps(notes,ensure_ascii=False) if p==path else read_text(p,*args,**kwargs)
   with self.subTest(problem=problem),patch.object(Path,'read_text',read):
    with self.assertRaises(AssertionError):attach(copy.deepcopy(corpus))

 def test_all_paragraphs_and_shared_chapter(self):
  corpus=json.loads((ROOT/'data/sutras.json').read_text())
  attach(corpus)
  self.assertEqual([len(s['verses']) for s in corpus[-2:]],[216,871])
  for s in corpus:
   self.assertTrue(all(v['meaning'].strip() for v in s['verses']),s['id'])
  standalone={v['textHash']:v['meaning'] for v in corpus[3]['verses']}
  chapter=corpus[-1]['chapters'][24]
  for v in corpus[-1]['verses'][chapter['start']:chapter['end']]:
   self.assertEqual(v['meaning'],standalone[v['textHash']])

if __name__=='__main__':unittest.main()
