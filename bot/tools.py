import datetime
import re

LINK_RE = re.compile(r"((http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?|([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?)")
MENTION = re.compile(r"@[a-zA-Z0-9_]{4,32}")


def error_writer(e: Exception, f_name:str):
    with open("error_log", "a") as f:
        er = f_name + str(datetime.datetime.now()) + "".join(e.args)
        f.write(er)

