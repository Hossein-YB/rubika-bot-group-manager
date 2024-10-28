import datetime
import re

LINK_RE = re.compile(r"((http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?|([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?)")
MENTION = re.compile(r"@[a-zA-Z0-9_]{4,32}")


def error_writer(e: Exception, f_name: str):
    with open("error_log", "a") as f:
        er = f_name + str(datetime.datetime.now()) + f"{e.args}"
        f.write(er)


def user_permissions_admin(func):
    async def check(self, msg, *args, **kwargs):
        ch = await self.check_sender(msg, is_admin=True)
        if not ch:
            return False
        f = func(self, msg, *args, **kwargs)
        return await f

    return check


def user_permissions_creator(func):
    async def check(self, msg, *args, **kwargs):
        ch = await self.check_sender(msg, is_creator=True)
        if not ch:
            return False
        f = func(self, msg, *args, **kwargs)
        return await f

    return check
