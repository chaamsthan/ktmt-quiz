#!/usr/bin/env python3
"""Generate contact sheets for HUMAN inspection, not replacement source assets."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--confirm-reviewed',action='store_true',help='Only AFTER human inspection of every final contact sheet and source page')
    args=parser.parse_args()
    crops=json.loads((ROOT/'subjects/nmmmh/audit/collections-2025-2026/crop_manifest.json').read_text())
    args.output.mkdir(parents=True,exist_ok=True)
    for start in range(0,len(crops),8):
        sheet=Image.new('RGB',(1800,2000),'#ddd');draw=ImageDraw.Draw(sheet)
        for offset,c in enumerate(crops[start:start+8]):
            x=(offset%2)*900;y=(offset//2)*500
            draw.text((x+5,y+5),c['question_id']+' / p'+str(c['source_page']),fill='black')
            img=Image.open(ROOT/c['path']).convert('RGB');img.thumbnail((890,470));sheet.paste(img,(x+5,y+25))
        path=args.output/f'pdf-crops-{start//8}.jpg';sheet.save(path,quality=94);print(path)
    if args.confirm_reviewed:
        evidence={c['path']:{'sha256':hashlib.sha256((ROOT/c['path']).read_bytes()).hexdigest(),
                            'review':'visually_compared_final_crop_with_original_page',
                            'source_limitation':'PC-1 source table itself is split/cut; disclosed on question' if c['question_id'].endswith('ca-2-17') else None} for c in crops}
        (ROOT/'subjects/nmmmh/audit/collections-2025-2026/crop_visual_review.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
