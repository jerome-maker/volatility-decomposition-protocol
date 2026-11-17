# -*- coding: utf-8 -*-
"""Unit 0a: the one cell a hosted runtime needs, and a no-op everywhere else."""
from parts._helpers import bi, code, mono

CELLS = [
    mono(
        "## 執行前 / Before you run\n\n"
        "---"
    ),
    bi(
        zh=(
            "下面這一格讓筆記本在 Colab、Binder 與本機都能直接執行，**不需要你先做任何事**。\n\n"
            "它只做兩件事，而且兩件都先檢查是否必要：\n\n"
            "1. **找不到資料時**才把倉庫複製下來並切換工作目錄。本機執行時資料就在旁邊，這一步完全不會觸發。\n"
            "2. **缺套件時**才安裝，版本以倉庫根目錄的 `requirements.txt` 為準"
            "（即論文 `ENVIRONMENT.md` 的 Environment A）。六個套件都在就什麼都不做。\n\n"
            "所以在自己電腦上跑的人看到的是兩行「不需要處理」，在 Colab 上跑的人什麼都不用加。"
            "這格也是整份筆記本唯一會動到環境的地方。"
        ),
        en=(
            "The cell below lets the notebook run as it is on Colab, on Binder and locally, **with nothing "
            "for you to do first**.\n\n"
            "It does two things, and checks whether each is needed before doing it:\n\n"
            "1. It clones the repository and changes directory **only when the data cannot be found**. Run "
            "locally, where the data sit next to the notebook, this step never fires.\n"
            "2. It installs packages **only when one is missing**, to the versions pinned in "
            "`requirements.txt` at the repository root, which is Environment A of the paper's "
            "`ENVIRONMENT.md`. With all six present it does nothing.\n\n"
            "So a reader on their own machine sees two lines saying there was nothing to do, and a reader on "
            "Colab adds nothing. This is also the only cell in the notebook that touches the environment."
        ),
    ),
    code(
        """
# Bootstrap. Runs on any host, changes nothing when the notebook is already in place.
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO = "https://github.com/jerome-maker/volatility-decomposition-protocol"
NEEDED = ["numpy", "pandas", "scipy", "statsmodels", "arch", "matplotlib"]
DATA_MARK = Path("data") / "analysis_daily.csv"          # the file every later cell depends on


def data_is_reachable(start=None):
    \"\"\"True when a later cell's find_dir() will succeed from here.\"\"\"
    start = start or Path.cwd()
    for root in (start, start.parent, start.parent.parent):
        if (root / DATA_MARK).is_file() or (root / "資訊階梯分析_程式與圖表" / DATA_MARK).is_file():
            return True
    return False


if data_is_reachable():
    print(f"data reachable from ./{Path.cwd().name} -- nothing to clone")
else:
    target = Path.cwd() / REPO.rsplit("/", 1)[-1]
    if not target.is_dir():
        print(f"data not found; cloning {REPO}")
        subprocess.run(["git", "clone", "--depth", "1", REPO, str(target)], check=True)
    os.chdir(target / "teaching")
    print(f"working directory is now ./{Path.cwd().parent.name}/{Path.cwd().name}")

missing = [m for m in NEEDED if importlib.util.find_spec(m) is None]
if not missing:
    print(f"all packages present -- nothing to install ({', '.join(NEEDED)})")
else:
    # Install ONLY what is missing, at the pinned version. Passing the whole
    # requirements file would also re-resolve packages that are already here,
    # which on the author's own machine means a build can change the very
    # environment whose versions the file is supposed to record.
    req = Path.cwd().parent / "requirements.txt"
    pins = {}
    if req.is_file():
        for line in req.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if "==" in line:
                pins[line.split("==")[0].strip().lower()] = line
    spec = [pins.get(m.lower(), m) for m in missing]
    print(f"installing {', '.join(spec)}")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *spec], check=True)
    print("install finished; if an import below fails, restart the kernel and run again")
"""
    ),
]
