import re

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import Plain, Image
from core.component import module
from core.scheduler import IntervalTrigger

Silian_test = module("test")


@Silian_test.command()
async def _(Silian_msg: Bot.MessageSession):
    #  >>> ~test
    #  <<< Hello World!
    await Silian_msg.send_message("Hello World!")


@Silian_test.command("say <word>")
async def _(msg: Bot.MessageSession, word: str):
    #  >>> ~test say Word
    #  <<< Word is Word
    await msg.finish(f"{word} is {msg.parsed_msg['<word>']}")


@Silian_test.command("reply")
async def _(Silian_msg: Bot.MessageSession):
    #  >>> ~test reply
    #  <<< Reply me!
    #  >>> Hello World! >> [Reply me!]
    #  <<< Hello World!
    Silian_s = await Silian_msg.wait_reply("Reply me!")
    await Silian_s.send_message(Silian_s.as_display())


@Silian_test.command("confirm")
async def _(Silian_msg: Bot.MessageSession):
    #  >>> ~test confirm
    #  <<< Are you sure?
    #  >>> Yes
    #  <<< OK!
    if await Silian_msg.wait_confirm("Are you sure?"):
        await Silian_msg.send_message("OK!")


@Silian_test.command("msgchain")
async def _(Silian_msg: Bot.MessageSession):
    #  >>> ~test msgchain
    #  <<< A picture: Image(url="https://http.cat/100.jpg")
    #  <<< KE Code is also Image(url="https://http.cat/200.jpg")
    await Silian_msg.send_message(MessageChain.assign([Plain("A picture:"), Image("https://http.cat/100.jpg")]))
    await Silian_msg.send_message(
        "[KE:plain,text=KE Code is also][KE:image,path=https://http.cat/200.jpg][KE:i18n,i18nkey=example]"
    )


@Silian_test.regex(r"\{\{(.*?)}}", mode="M")  # re.match
async def _(Silian_msg: Bot.MessageSession):
    #  >>> {{Hello World!}}
    #  <<< Hello World!
    await Silian_msg.finish(Silian_msg.matched_msg.group(1))


@Silian_test.regex(r"\[\[(.*?)]]", mode="A")  # re.findall
async def _(Silian_msg: Bot.MessageSession):
    #  >>> [[Hello]] [[World]]
    #  <<< Hello
    #  <<< World
    for Silian_x in Silian_msg.matched_msg:
        await Silian_msg.send_message(Silian_x)


@Silian_test.schedule(IntervalTrigger(seconds=30))
async def _():
    # Send a message to target which is enabled test module every 30 seconds
    await Bot.post_message("test", "This message is sent per 30 seconds")


@Silian_test.handle("test")  # all in one handler, including command, regex and schedule
async def _(Silian_msg: Bot.MessageSession):
    #  >>> ~test test
    #  <<< Hello World!
    await Silian_msg.finish("Hello World!")


@Silian_test.handle(re.compile(r"<(.*?)>"), mode="A")  # re.findall
async def _(Silian_msg: Bot.MessageSession):
    #  >>> <Hello World!>
    #  <<< Hello World!
    await Silian_msg.finish(Silian_msg.matched_msg[0])


@Silian_test.handle(IntervalTrigger(seconds=60))
async def _():
    # Send a message to target which is enabled test module every 60 seconds
    await Bot.post_message("test", "This message is sent per 60 seconds")
