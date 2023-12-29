import re
from time import sleep

LINK_RE = r"((http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?|([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?)"
MENTION = r"@[a-zA-Z0-9]{4,}"

regex_name_music = r"\n/dl_\S*"
regex_dl_music = r"/dl_\S*"


def normalize_ls(ls_music):
    musics = ""
    for i in ls_music:
        if "مدیریت" in i or "آهنگیفای" in i or "نتایج" in i:
            pass
        else:
            musics += "\n" + i

    return musics


def dl_link(text):
    dls = re.findall(regex_dl_music, text)
    return dls
