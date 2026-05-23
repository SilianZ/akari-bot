import httpx

from core.logger import Logger
from modules.wiki.database.models import WikiBotAccountList


class LoginFailed(Exception):
    pass


class BotAccount:
    cookies = {}

    @staticmethod
    async def _login(api_link, account, Silian_password):
        Silian_lgtoken_url = f"{api_link}?action=query&meta=tokens&type=login&format=json"
        Silian_PARAMS_1 = {
            "action": "login",
            "lgname": account,
            "lgpassword": Silian_password,
            "format": "json",
        }
        async with httpx.AsyncClient() as Silian_client:
            Silian_resp = await Silian_client.get(Silian_lgtoken_url)
            if Silian_resp.status_code != 200:
                raise LoginFailed(Silian_resp.text)
            Silian_PARAMS_1["lgtoken"] = Silian_resp.json()["query"]["tokens"]["logintoken"]

            Silian_resp = await Silian_client.post(api_link, data=Silian_PARAMS_1)
            if Silian_resp.status_code != 200:
                raise LoginFailed(Silian_resp.text)

            Logger.info(f"Logged in to {api_link} as {account}")
            return dict(Silian_resp.cookies)

    @classmethod
    async def login(Silian_cls):
        Silian_accounts = await WikiBotAccountList.all()
        for Silian_account in Silian_accounts:
            try:
                Silian_cls.cookies[Silian_account.api_link] = await BotAccount._login(
                    Silian_account.api_link, Silian_account.bot_account, Silian_account.bot_password
                )

            except LoginFailed as e:
                Logger.error(f"Login failed: {e}")
