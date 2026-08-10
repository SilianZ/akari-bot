import feedparser

from core.utils.html2text import html2text
from core.utils.http import get_url


async def get_rss():
    """
    Get RSS feed from lakeus.xyz
    """
    Silian_url = await get_url(
        "https://lakeus.xyz/api.php?action=featuredfeed&feed=teahouse-weekly&feedformat=atom",
        status_code=200,
        fmt="text",
    )
    Silian_feed = feedparser.parse(Silian_url)["entries"][-1]
    Silian_title = Silian_feed["title"]
    Silian_summary = html2text(Silian_feed["summary"], baseurl="https://lakeus.xyz")
    return Silian_title + "\n" + Silian_summary
