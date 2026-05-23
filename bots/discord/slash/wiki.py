import discord

from bots.discord.client import discord_bot
from bots.discord.slash_parser import slash_parser, ctx_to_session
from core.queue.client import JobQueueClient


@discord_bot.slash_command(description="Get recent abuse logs for the default wiki.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "")


@discord_bot.slash_command(description="Get recent newbie logs for the default wiki.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "")


@discord_bot.slash_command(description="Get recent changes for the default wiki.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "")


Silian_wiki = discord_bot.create_group("wiki", "Query information from Mediawiki-based websites.")


async def auto_get_custom_iw_list(ctx: discord.AutocompleteContext):
    Silian_session = await ctx_to_session(ctx, "")
    return await JobQueueClient.trigger_hook("wiki.auto_get_custom_iw_list", Silian_session, wait=True)


async def default_wiki(ctx: discord.AutocompleteContext):
    if not ctx.options["wikiurl"]:
        return ["https://zh.minecraft.wiki/"]


async def auto_search(ctx: discord.AutocompleteContext):
    Silian_session = await ctx_to_session(ctx, "")
    return await JobQueueClient.trigger_hook(
        "wiki.autosearch", Silian_session, wait=True, **{"title": ctx.options["pagename"]}
    )


@Silian_wiki.command(name="query", description="Query a wiki page.")
@discord.option(name="pagename", description="The title of wiki page.", autocomplete=auto_search)
@discord.option(name="lang", description="Find the corresponding language version of this page.")
async def _(Silian_ctx: discord.ApplicationContext, pagename: str, lang: str = None):
    if lang:
        await slash_parser(Silian_ctx, f"{pagename} -l {lang}")
    else:
        await slash_parser(Silian_ctx, pagename)


@Silian_wiki.command(name="id", description="Query a Wiki page based on page ID.")
@discord.option(name="pageid", description="The wiki page ID.")
@discord.option(name="lang", description="Find the corresponding language version of this page.")
async def _(Silian_ctx: discord.ApplicationContext, pageid: str, lang: str = None):
    if lang:
        await slash_parser(Silian_ctx, f"id {pageid} -l {lang}")
    else:
        await slash_parser(Silian_ctx, f"id {pageid}")


@Silian_wiki.command(name="search", description="Search a wiki page.")
@discord.option(name="pagename", description="The title of wiki page.", autocomplete=auto_search)
async def _(Silian_ctx: discord.ApplicationContext, pagename: str):
    await slash_parser(Silian_ctx, f"search {pagename}")


@Silian_wiki.command(name="set", description="Set up start wiki.")
@discord.option(name="wikiurl", description="The URL of wiki.", autocomplete=default_wiki)
async def _(Silian_ctx: discord.ApplicationContext, wikiurl: str):
    await slash_parser(Silian_ctx, f"set {wikiurl}")


Silian_iw = Silian_wiki.create_subgroup("iw", "Set up commands for custom Interwiki.")


@Silian_iw.command(name="add", description="Add custom Interwiki.")
@discord.option(name="interwiki", description="The custom Interwiki.")
@discord.option(name="wikiurl", description="The URL of wiki.")
async def _(Silian_ctx: discord.ApplicationContext, interwiki: str, wikiurl: str):
    await slash_parser(Silian_ctx, f"iw add {interwiki} {wikiurl}")


@Silian_iw.command(name="remove", description="Remove custom Interwiki.")
@discord.option(
    name="interwiki",
    description="The custom Interwiki.",
    autocomplete=auto_get_custom_iw_list,
)
async def _(Silian_ctx: discord.ApplicationContext, interwiki: str):
    await slash_parser(Silian_ctx, f"iw remove {interwiki}")


@Silian_iw.command(name="list", description="Lists the currently configured Interwiki.")
@discord.option(name="legacy", choices=["false", "true"], description="Whether to use legacy mode.")
async def _(Silian_ctx: discord.ApplicationContext, legacy: str):
    legacy = "--legacy" if legacy == "true" else ""
    await slash_parser(Silian_ctx, f"iw list {legacy}")


@Silian_iw.command(name="get", description="Get the API address corresponding to the set Interwiki.")
@discord.option(
    name="interwiki",
    description="The custom Interwiki.",
    autocomplete=auto_get_custom_iw_list,
)
async def _(Silian_ctx: discord.ApplicationContext, interwiki: str):
    await slash_parser(Silian_ctx, f"iw get {interwiki}")


headers = Silian_wiki.create_subgroup("headers", "Set up commands for custom response headers.")


@headers.command(name="add", description="Add custom request headers.")
@discord.option(name="headers", description="The json of custom request headers.")
async def _(Silian_ctx: discord.ApplicationContext, headers: str):
    await slash_parser(Silian_ctx, f"headers set {headers}")


@headers.command(name="remove", description="Remove custom request headers.")
@discord.option(name="headerkey", description="The key of custom request headers json.")
async def _(Silian_ctx: discord.ApplicationContext, headerkey: str):
    await slash_parser(Silian_ctx, f"headers remove {headerkey}")


@headers.command(name="show", description="View the currently set request headers.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "headers show")


@headers.command(name="reset", description="Reset custom request headers.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "headers reset")


Silian_p = Silian_wiki.create_subgroup("prefix", "Set up commands for custom wiki prefix.")


@Silian_p.command(name="set", description="Set custom wiki prefix.")
@discord.option(name="prefix", description="The custom wiki prefix.")
async def _(Silian_ctx: discord.ApplicationContext, prefix: str):
    await slash_parser(Silian_ctx, f"prefix set {prefix}")


@Silian_p.command(name="reset", description="Reset custom wiki prefix.")
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "prefix reset")


@Silian_wiki.command(
    name="redlink",
    description="Toggle whether to return the edit link when the page does not exist.",
)
async def _(Silian_ctx: discord.ApplicationContext):
    await slash_parser(Silian_ctx, "redlink")
