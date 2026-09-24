"""Root's line-by-line comparison against all nine preserved page images."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / 'reports/raft-prep/candidates/davy-1651A-text.v2.luna.json'
d = json.loads(src.read_text())
fixes = {
    21: [('My dear Sir,', '', 'Opening salutation removed with letter header.')],
    22: [('bloodcorpuscles', 'blood-corpuscles', 'Printed compound spans a line; compare same compound on p24.'),
         ('Leven. v', 'Leven.', 'Stray OCR v is not printed authorial text.')],
    24: [('in. Of Exposure in Air and TVater to a Temperature at or below the Freezing-^point.',
          'III. Of Exposure in Air and Water to a Temperature at or below the Freezing-point.',
          'Roman numeral, italic Water and hyphenated heading verified in image.'),
         ('same as. that', 'same as that', 'Stray OCR full stop absent from print.'),
         ('h. Exposed an egg', '5. Exposed an egg', 'Printed experiment number is 5.'),
         ('7- An ovum', '7. An ovum', 'Printed experiment number ends with a full stop.'),
         ('freezingpoint', 'freezing-point', 'Printed compound spans a line; preserve its hyphen.')],
    25: [("'39 inch", '·39 inch', 'Printed leading decimal point, not an apostrophe.'),
         ("29°'5", '29°·5', 'Printed raised decimal point following degree sign.'),
         ('*02 inch', '·02 inch', 'Printed leading decimal point, not an asterisk.'),
         ('Of Exposure in IVater', 'Of Exposure in Water', 'Italic Water misread as IVater.')],
    27: [("disinteg'ration", 'disintegration', 'No apostrophe in the printed word.')],
    28: [('detailed, 1 have', 'detailed, I have', 'Printed first-person I, not numeral 1.'),
         ('expei’iments', 'experiments', 'Printed word experiments, no apostrophe.')],
    29: [('Galway*.', 'Galway.', 'Footnote marker removed; footnote text remains excluded.'),
         ('Salmonidae', 'Salmonidæ', 'Printed ligature retained.')],
}
corrections=[]
pages=[]
for page in d['pages']:
    n=page['printed_page'];text=page['text']
    image=ROOT/page['page_image']['path']
    assert hashlib.sha256(image.read_bytes()).hexdigest()==page['page_image']['sha256']
    for old,new,reason in fixes.get(n,[]):
        assert text.count(old)==1,(n,old)
        text=text.replace(old,new)
        corrections.append({'printed_page':n,'original':old,'corrected':new,
                            'reason':reason,'evidence':page['page_image']})
    text='\n\n'.join(re.sub(r'\s+',' ',p).strip() for p in text.strip().split('\n\n') if p.strip())
    pages.append({**page,'text':text})
content=' '.join(p['text'] for p in pages)
assert '*' not in content and 'TVater' not in content and 'IVater' not in content
out={'status':'primary_source_verified_printed_letter_transcription',
     'source_id':'DCP-LETT-1651A','source':d['source'],
     'inputs':[{'path':str(src.relative_to(ROOT)),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()},
               {'path':str(Path(__file__).relative_to(ROOT)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}],
     'primary_verification':{'reviewer':'root','all_nine_images_viewed_this_review':True,
        'printed_pages':list(range(21,30)),'method':'Read each page image and compare all surviving candidate prose, scientific quantities, source boundaries and page joins.',
        'page_join_rule':'Each page ends within a continuing authorial paragraph or numbered experiment; join with one space.',
        'omissions':'Article title, running headers and page numbers, receipt/read line, letter salutation, dateline, signature, footnote marker/text and printer signatures.',
        'witness_limit':'Published letter witness, not a manuscript facsimile; retain historical spelling and printed numerical scale.'},
     'corrections':corrections,'pages':pages,'content':content,
     'content_sha256':hashlib.sha256(content.encode()).hexdigest()}
target=ROOT/'reports/raft-prep/davy-1651A-text.primary.json'
assert not target.exists(),'Primary artifact already exists'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pages':len(pages),'repairs':len(corrections),'characters':len(content)}))
