"""Render the README's editing demonstration from a real template project.

Run from the repository after installation. No models, APIs or private art.
Browser screenshots in the gallery are captured separately from DX Editor.
"""
import argparse
import copy
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image
from dx_studio.project import Project
from dx_studio.scaffold import create


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/images')
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='dx-showcase-') as folder:
        project=Project(create(Path(folder)/'demo',format='16:9'))
        frames=[]
        for step in range(4):
            values=copy.deepcopy(project.defaults)
            values['eyebrow']=['01 / THE FIRST CUT','02 / CHANGE THE WORDS','03 / MAKE IT YOUR BRAND','04 / HIDE A LAYER'][step]
            if step>=1:values['title']='My story.\nMy final cut.'
            if step>=2:values['accent']='#167362'
            if step>=3:values['__layers']['row3']['visible']=False
            project.apply(values)
            surface=project.render(1,.5)
            arr=np.frombuffer(surface.get_data(),np.uint8).reshape(surface.get_height(),surface.get_stride()//4,4)
            frame=Image.fromarray(arr[:,:surface.get_width(),[2,1,0]].copy())
            frame.save(args.output/f'edit-step-{step+1}.png')
            frames.append(frame)
        frames[0].save(args.output/'editable-demo.gif',save_all=True,append_images=frames[1:],duration=2000,loop=0,optimize=True)
        print(args.output/'editable-demo.gif')

if __name__=='__main__':main()
