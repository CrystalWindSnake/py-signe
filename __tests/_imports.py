import sys
from pathlib import Path
import os

cur_root = Path(__file__).absolute().parent

os.chdir(cur_root)


def find_close_set_pj_root():
    target = cur_root

    while 1:
        if list(target.glob("signe")) == 0:
            target = target.parent

            if target.is_block_device():
                raise Exception("")
            continue

        return target


sys.path.insert(0, str(find_close_set_pj_root()))

# print(str(Path(__file__).absolute().parent))
sys.path.append(str(cur_root.parent))
