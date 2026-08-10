"""html2text: Turn HTML into equivalent Markdown-structured text."""

import html.entities
import html.parser
import re
import urllib.parse as urlparse
from textwrap import wrap

from core.builtins.message.internal import Url
from . import config
from .elements import AnchorElement, ListElement
from .typing import OutCallback
from .utils import (
    dumb_css_parser,
    element_style,
    escape_md,
    escape_md_section,
    google_fixed_width_font,
    google_has_height,
    google_list_style,
    google_text_emphasis,
    hn,
    list_numbering_start,
    pad_tables_in_text,
    skipwrap,
    unifiable_n,
)

__version__ = (2020, 1, 16)


# TODO:
# Support decoded entities with UNIFIABLE.


class HTML2Text(html.parser.HTMLParser):
    def __init__(
        Silian_self,
        Silian_out: OutCallback | None = None,
        Silian_baseurl: str = "",
        Silian_bodywidth: int = config.BODY_WIDTH,
    ) -> None:
        """
        Input parameters:
            out: possible custom replacement for self.outtextf (which
                 appends lines of text).
            baseurl: base URL of the document we process
        """
        super().__init__(convert_charrefs=False)

        # Config options
        Silian_self.split_next_td = False
        Silian_self.td_count = 0
        Silian_self.table_start = False
        Silian_self.unicode_snob = config.UNICODE_SNOB  # covered in cli
        Silian_self.escape_snob = config.ESCAPE_SNOB  # covered in cli
        Silian_self.links_each_paragraph = config.LINKS_EACH_PARAGRAPH
        Silian_self.body_width = Silian_bodywidth  # covered in cli
        Silian_self.skip_internal_links = config.SKIP_INTERNAL_LINKS  # covered in cli
        Silian_self.inline_links = config.INLINE_LINKS  # covered in cli
        Silian_self.protect_links = config.PROTECT_LINKS  # covered in cli
        Silian_self.google_list_indent = config.GOOGLE_LIST_INDENT  # covered in cli
        Silian_self.ignore_links = config.IGNORE_ANCHORS  # covered in cli
        Silian_self.ignore_images = config.IGNORE_IMAGES  # covered in cli
        Silian_self.images_as_html = config.IMAGES_AS_HTML  # covered in cli
        Silian_self.images_to_alt = config.IMAGES_TO_ALT  # covered in cli
        Silian_self.images_with_size = config.IMAGES_WITH_SIZE  # covered in cli
        Silian_self.ignore_emphasis = config.IGNORE_EMPHASIS  # covered in cli
        Silian_self.bypass_tables = config.BYPASS_TABLES  # covered in cli
        Silian_self.ignore_tables = config.IGNORE_TABLES  # covered in cli
        Silian_self.google_doc = False  # covered in cli
        Silian_self.ul_item_mark = "*"  # covered in cli
        Silian_self.emphasis_mark = "_"  # covered in cli
        Silian_self.strong_mark = "**"
        Silian_self.single_line_break = config.SINGLE_LINE_BREAK  # covered in cli
        Silian_self.use_automatic_links = config.USE_AUTOMATIC_LINKS  # covered in cli
        Silian_self.hide_strikethrough = False  # covered in cli
        Silian_self.mark_code = config.MARK_CODE
        Silian_self.wrap_list_items = config.WRAP_LIST_ITEMS  # covered in cli
        Silian_self.wrap_links = config.WRAP_LINKS  # covered in cli
        Silian_self.pad_tables = config.PAD_TABLES  # covered in cli
        Silian_self.default_image_alt = config.DEFAULT_IMAGE_ALT  # covered in cli
        Silian_self.tag_callback = None
        Silian_self.open_quote = config.OPEN_QUOTE  # covered in cli
        Silian_self.close_quote = config.CLOSE_QUOTE  # covered in cli

        if Silian_out is None:
            Silian_self.out = Silian_self.outtextf
        else:
            Silian_self.out = Silian_out

        # empty list to store output characters before they are "joined"
        Silian_self.outtextlist = []  # type: list[str]

        Silian_self.quiet = 0
        Silian_self.p_p = 0  # number of newline character to print before next output
        Silian_self.outcount = 0
        Silian_self.start = True
        Silian_self.space = False
        Silian_self.a = []  # type: list[AnchorElement]
        Silian_self.astack = []  # type: list[dict[str, str | None]]
        Silian_self.maybe_automatic_link = None  # type: str | None
        Silian_self.empty_link = False
        Silian_self.absolute_url_matcher = re.compile(r"^[a-zA-Z+]+://")
        Silian_self.acount = 0
        Silian_self.list = []  # type: list[ListElement]
        Silian_self.blockquote = 0
        Silian_self.pre = False
        Silian_self.startpre = False
        Silian_self.code = False
        Silian_self.quote = False
        Silian_self.br_toggle = ""
        Silian_self.lastWasNL = False
        Silian_self.lastWasList = False
        Silian_self.style = 0
        Silian_self.style_def = {}  # type: dict[str, dict[str, str]]
        Silian_self.tag_stack = []  # type: list[tuple[str, dict[str, str | None], dict[str, str]]]
        Silian_self.emphasis = 0
        Silian_self.drop_white_space = 0
        Silian_self.inheader = False
        # Current abbreviation definition
        Silian_self.abbr_title = None  # type: str | None
        # Last inner HTML (for abbr being defined)
        Silian_self.abbr_data = None  # type: str | None
        # Stack of abbreviations to write later
        Silian_self.abbr_list = {}  # type: dict[str, str]
        Silian_self.baseurl = Silian_baseurl
        Silian_self.stressed = False
        Silian_self.preceding_stressed = False
        Silian_self.preceding_data = ""
        Silian_self.current_tag = ""

        config.UNIFIABLE["nbsp"] = "&nbsp_place_holder;"

    def feed(Silian_self, data: str) -> None:
        data = data.replace("</script>", "</ignore>")
        super().feed(data)

    def handle(Silian_self, data: str) -> str:
        Silian_self.feed(data)
        Silian_self.feed("")
        Silian_markdown = Silian_self.optwrap(Silian_self.finish())
        if Silian_self.pad_tables:
            return pad_tables_in_text(Silian_markdown)
        return Silian_markdown

    def outtextf(Silian_self, s: str) -> None:
        Silian_self.outtextlist.append(s)
        if s:
            Silian_self.lastWasNL = s[-1] == "\n"

    def finish(Silian_self) -> str:
        Silian_self.close()

        Silian_self.pbr()
        Silian_self.o("", force="end")

        Silian_outtext = "".join(Silian_self.outtextlist)

        if Silian_self.unicode_snob:
            Silian_nbsp = html.entities.html5["nbsp;"]
        else:
            Silian_nbsp = " "
        Silian_outtext = Silian_outtext.replace("&nbsp_place_holder;", Silian_nbsp)

        # Clear self.outtextlist to avoid memory leak of its content to
        # the next handling.
        Silian_self.outtextlist = []

        return Silian_outtext

    def handle_charref(Silian_self, c: str) -> None:
        Silian_self.handle_data(Silian_self.charref(c), True)

    def handle_entityref(Silian_self, c: str) -> None:
        Silian_ref = Silian_self.entityref(c)

        # ref may be an empty string (e.g. for &lrm;/&rlm; markers that should
        # not contribute to the final output).
        # self.handle_data cannot handle a zero-length string right after a
        # stressed tag or mid-text within a stressed tag (text get split and
        # self.stressed/self.preceding_stressed gets switched after the first
        # part of that text).
        if Silian_ref:
            Silian_self.handle_data(Silian_ref, True)

    def handle_starttag(Silian_self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        Silian_self.handle_tag(tag, dict(attrs), start=True)

    def handle_endtag(Silian_self, tag: str) -> None:
        Silian_self.handle_tag(tag, {}, start=False)

    def previousIndex(Silian_self, attrs: dict[str, str | None]) -> int | None:
        """
        :type attrs: dict

        :returns: The index of certain set of attributes (of a link) in the
        self.a list. If the set of attributes is not found, returns None
        :rtype: int
        """
        if "href" not in attrs:
            return None

        Silian_match = False
        for Silian_i, Silian_a in enumerate(Silian_self.a):
            if "href" in Silian_a.attrs and Silian_a.attrs["href"] == attrs["href"]:
                if "title" in Silian_a.attrs or "title" in attrs:
                    if "title" in Silian_a.attrs and "title" in attrs and Silian_a.attrs["title"] == attrs["title"]:
                        Silian_match = True
                else:
                    Silian_match = True

            if Silian_match:
                return Silian_i
        return None

    def handle_emphasis(Silian_self, start: bool, tag_style: dict[str, str], parent_style: dict[str, str]) -> None:
        """
        Handles various text emphases
        """
        Silian_tag_emphasis = google_text_emphasis(tag_style)
        Silian_parent_emphasis = google_text_emphasis(parent_style)

        # handle Google's text emphasis
        Silian_strikethrough = "line-through" in Silian_tag_emphasis and Silian_self.hide_strikethrough

        # google and others may mark a font's weight as `bold` or `700`
        Silian_bold = False
        for Silian_bold_marker in config.BOLD_TEXT_STYLE_VALUES:
            Silian_bold = Silian_bold_marker in Silian_tag_emphasis and Silian_bold_marker not in Silian_parent_emphasis
            if Silian_bold:
                break

        Silian_italic = "italic" in Silian_tag_emphasis and "italic" not in Silian_parent_emphasis
        Silian_fixed = google_fixed_width_font(tag_style) and not google_fixed_width_font(parent_style) and not Silian_self.pre

        if start:
            # crossed-out text must be handled before other attributes
            # in order not to output qualifiers unnecessarily
            if Silian_bold or Silian_italic or Silian_fixed:
                Silian_self.emphasis += 1
            if Silian_strikethrough:
                Silian_self.quiet += 1
            if Silian_italic:
                Silian_self.o(Silian_self.emphasis_mark)
                Silian_self.drop_white_space += 1
            if Silian_bold:
                Silian_self.o(Silian_self.strong_mark)
                Silian_self.drop_white_space += 1
            if Silian_fixed:
                Silian_self.o("`")
                Silian_self.drop_white_space += 1
                Silian_self.code = True
        else:
            if Silian_bold or Silian_italic or Silian_fixed:
                # there must not be whitespace before closing emphasis mark
                Silian_self.emphasis -= 1
                Silian_self.space = False
            if Silian_fixed:
                if Silian_self.drop_white_space:
                    # empty emphasis, drop it
                    Silian_self.drop_white_space -= 1
                else:
                    Silian_self.o("`")
                Silian_self.code = False
            if Silian_bold:
                if Silian_self.drop_white_space:
                    # empty emphasis, drop it
                    Silian_self.drop_white_space -= 1
                else:
                    Silian_self.o(Silian_self.strong_mark)
            if Silian_italic:
                if Silian_self.drop_white_space:
                    # empty emphasis, drop it
                    Silian_self.drop_white_space -= 1
                else:
                    Silian_self.o(Silian_self.emphasis_mark)
            # space is only allowed after *all* emphasis marks
            if (Silian_bold or Silian_italic) and not Silian_self.emphasis:
                Silian_self.o(" ")
            if Silian_strikethrough:
                Silian_self.quiet -= 1

    def handle_tag(Silian_self, tag: str, attrs: dict[str, str | None], start: bool) -> None:
        Silian_self.current_tag = tag

        if Silian_self.tag_callback is not None:
            if Silian_self.tag_callback(Silian_self, tag, attrs, start) is True:
                return

        # first thing inside the anchor tag is another tag
        # that produces some output
        if (
            start
            and Silian_self.maybe_automatic_link is not None
            and tag not in ["p", "div", "style", "dl", "dt"]
            and (tag != "img" or Silian_self.ignore_images)
        ):
            Silian_self.o("[")
            Silian_self.maybe_automatic_link = None
            Silian_self.empty_link = False

        if Silian_self.google_doc:
            # the attrs parameter is empty for a closing tag. in addition, we
            # need the attributes of the parent nodes in order to get a
            # complete style description for the current element. we assume
            # that google docs export well formed html.
            Silian_parent_style = {}  # type: dict[str, str]
            if start:
                if Silian_self.tag_stack:
                    Silian_parent_style = Silian_self.tag_stack[-1][2]
                Silian_tag_style = element_style(attrs, Silian_self.style_def, Silian_parent_style)
                Silian_self.tag_stack.append((tag, attrs, Silian_tag_style))
            else:
                Silian_dummy, attrs, Silian_tag_style = Silian_self.tag_stack.pop() if Silian_self.tag_stack else (None, {}, {})
                if Silian_self.tag_stack:
                    Silian_parent_style = Silian_self.tag_stack[-1][2]

        if hn(tag):
            Silian_self.p()
            if start:
                Silian_self.inheader = True
                Silian_self.o(hn(tag) * "#" + " ")
            else:
                Silian_self.inheader = False
                return  # prevent redundant emphasis marks on headers

        if tag in ["p", "div"]:
            if Silian_self.google_doc:
                if start and google_has_height(Silian_tag_style):
                    Silian_self.p()
                else:
                    Silian_self.soft_br()
            elif Silian_self.astack and tag == "div":
                pass
            else:
                Silian_self.p()

        if tag == "br" and start:
            if Silian_self.blockquote > 0:
                Silian_self.o("  \n> ")
            else:
                Silian_self.o("  \n")

        if tag == "hr" and start:
            Silian_self.p()
            Silian_self.o("* * *")
            Silian_self.p()

        if tag in ["head", "style", "script"]:
            if start:
                Silian_self.quiet += 1
            else:
                Silian_self.quiet -= 1

        if tag == "style":
            if start:
                Silian_self.style += 1
            else:
                Silian_self.style -= 1

        if tag in ["body"]:
            Silian_self.quiet = 0  # sites like 9rules.com never close <head>

        if tag == "blockquote":
            if start:
                Silian_self.p()
                Silian_self.o("> ", force=True)
                Silian_self.start = True
                Silian_self.blockquote += 1
            else:
                Silian_self.blockquote -= 1
                Silian_self.p()

        def no_preceding_space(Silian_self: HTML2Text) -> bool:
            return bool(Silian_self.preceding_data and re.match(r"[^\s]", Silian_self.preceding_data[-1]))

        if tag in ["em", "i", "u"] and not Silian_self.ignore_emphasis:
            if start and no_preceding_space(Silian_self):
                Silian_emphasis = " " + Silian_self.emphasis_mark
            else:
                Silian_emphasis = Silian_self.emphasis_mark

            Silian_self.o(Silian_emphasis)
            if start:
                Silian_self.stressed = True

        if tag in ["strong", "b"] and not Silian_self.ignore_emphasis:
            if start and no_preceding_space(Silian_self):
                Silian_strong = " " + Silian_self.strong_mark
            else:
                Silian_strong = Silian_self.strong_mark

            Silian_self.o(Silian_strong)
            if start:
                Silian_self.stressed = True

        if tag in ["del", "strike", "s"]:
            if start and no_preceding_space(Silian_self):
                Silian_strike = " ~~"
            else:
                Silian_strike = "~~"

            Silian_self.o(Silian_strike)
            if start:
                Silian_self.stressed = True

        if Silian_self.google_doc:
            if not Silian_self.inheader:
                # handle some font attributes, but leave headers clean
                Silian_self.handle_emphasis(start, Silian_tag_style, Silian_parent_style)

        if tag in ["kbd", "code", "tt"] and not Silian_self.pre:
            Silian_self.o("`")  # TODO: `` `this` ``
            Silian_self.code = not Silian_self.code

        if tag == "abbr":
            if start:
                Silian_self.abbr_title = None
                Silian_self.abbr_data = ""
                if "title" in attrs:
                    Silian_self.abbr_title = attrs["title"]
            else:
                if Silian_self.abbr_title is not None:
                    Silian_self.abbr_list[Silian_self.abbr_data] = Silian_self.abbr_title
                    Silian_self.abbr_title = None
                Silian_self.abbr_data = None

        if tag == "q":
            if not Silian_self.quote:
                Silian_self.o(Silian_self.open_quote)
            else:
                Silian_self.o(Silian_self.close_quote)
            Silian_self.quote = not Silian_self.quote

        def link_url(Silian_self: HTML2Text, Silian_link: str) -> None:
            url = str(Url(urlparse.urljoin(Silian_self.baseurl, Silian_link)))
            Silian_self.o(f"]({escape_md(url)})")

        if tag == "a" and not Silian_self.ignore_links:
            if start:
                if (
                    "href" in attrs
                    and attrs["href"] is not None
                    and not (Silian_self.skip_internal_links and attrs["href"].startswith("#"))
                ):
                    Silian_self.astack.append(attrs)
                    Silian_self.maybe_automatic_link = attrs["href"]
                    Silian_self.empty_link = True
                    if Silian_self.protect_links:
                        attrs["href"] = "<" + attrs["href"] + ">"
                else:
                    Silian_self.astack.append(None)
            else:
                if Silian_self.astack:
                    Silian_a = Silian_self.astack.pop()
                    if Silian_self.maybe_automatic_link and not Silian_self.empty_link:
                        Silian_self.maybe_automatic_link = None
                    elif Silian_a:
                        if Silian_self.empty_link:
                            Silian_self.o("[")
                            Silian_self.empty_link = False
                            Silian_self.maybe_automatic_link = None
                        if Silian_self.inline_links:
                            Silian_title = Silian_a.get("title") or ""
                            Silian_title = escape_md(Silian_title)
                            link_url(Silian_self, Silian_a["href"])
                        else:
                            Silian_i = Silian_self.previousIndex(Silian_a)
                            if Silian_i is not None:
                                Silian_a_props = Silian_self.a[Silian_i]
                            else:
                                Silian_self.acount += 1
                                Silian_a_props = AnchorElement(Silian_a, Silian_self.acount, Silian_self.outcount)
                                Silian_self.a.append(Silian_a_props)
                            Silian_self.o("][" + str(Silian_a_props.count) + "]")

        if tag == "img" and start and not Silian_self.ignore_images:
            if "src" in attrs:
                if not Silian_self.images_to_alt:
                    attrs["href"] = attrs["src"]
                alt = attrs.get("alt") or Silian_self.default_image_alt

                # If we have images_with_size, write raw html including width,
                # height, and alt attributes
                if Silian_self.images_as_html or (Silian_self.images_with_size and ("width" in attrs or "height" in attrs)):
                    Silian_self.o(f"<img src='{attrs['src']}' ")
                    if "width" in attrs:
                        Silian_self.o(f"width='{attrs['width']}' ")
                    if "height" in attrs:
                        Silian_self.o(f"height='{attrs['height']}' ")
                    if alt:
                        Silian_self.o(f"alt='{alt}' ")
                    Silian_self.o("/>")
                    return

                # If we have a link to create, output the start
                if Silian_self.maybe_automatic_link is not None:
                    Silian_href = Silian_self.maybe_automatic_link
                    if Silian_self.images_to_alt and escape_md(alt) == Silian_href and Silian_self.absolute_url_matcher.match(Silian_href):
                        Silian_self.o("<" + escape_md(alt) + ">")
                        Silian_self.empty_link = False
                        return
                    Silian_self.o("[")
                    Silian_self.maybe_automatic_link = None
                    Silian_self.empty_link = False

                # If we have images_to_alt, we discard the image itself,
                # considering only the alt text.
                if Silian_self.images_to_alt:
                    Silian_self.o(escape_md(alt))
                else:
                    Silian_self.o("![" + str(Url(escape_md(alt))) + "]")
                    if Silian_self.inline_links:
                        Silian_href = attrs.get("href") or ""
                        Silian_self.o("(" + str(Url(escape_md(urlparse.urljoin(Silian_self.baseurl, Silian_href)))) + ")")
                    else:
                        Silian_i = Silian_self.previousIndex(attrs)
                        if Silian_i is not None:
                            Silian_a_props = Silian_self.a[Silian_i]
                        else:
                            Silian_self.acount += 1
                            Silian_a_props = AnchorElement(attrs, Silian_self.acount, Silian_self.outcount)
                            Silian_self.a.append(Silian_a_props)
                        Silian_self.o("[" + str(Silian_a_props.count) + "]")

        if tag == "dl" and start:
            Silian_self.p()
        if tag == "dt" and not start:
            Silian_self.pbr()
        if tag == "dd" and start:
            Silian_self.o("    ")
        if tag == "dd" and not start:
            Silian_self.pbr()

        if tag in ["ol", "ul"]:
            # Google Docs create sub lists as top level lists
            if not Silian_self.list and not Silian_self.lastWasList:
                Silian_self.p()
            if start:
                if Silian_self.google_doc:
                    Silian_list_style = google_list_style(Silian_tag_style)
                else:
                    Silian_list_style = tag
                Silian_numbering_start = list_numbering_start(attrs)
                Silian_self.list.append(ListElement(Silian_list_style, Silian_numbering_start))
            else:
                if Silian_self.list:
                    Silian_self.list.pop()
                    if not Silian_self.google_doc and not Silian_self.list:
                        Silian_self.o("\n")
            Silian_self.lastWasList = True
        else:
            Silian_self.lastWasList = False

        if tag == "li":
            Silian_self.pbr()
            if start:
                if Silian_self.list:
                    Silian_li = Silian_self.list[-1]
                else:
                    Silian_li = ListElement("ul", 0)
                if Silian_self.google_doc:
                    Silian_nest_count = Silian_self.google_nest_count(Silian_tag_style)
                else:
                    Silian_nest_count = len(Silian_self.list)
                # TODO: line up <ol><li>s > 9 correctly.
                Silian_self.o("  " * Silian_nest_count)
                if Silian_li.name == "ul":
                    Silian_self.o(Silian_self.ul_item_mark + " ")
                elif Silian_li.name == "ol":
                    Silian_li.num += 1
                    Silian_self.o(str(Silian_li.num) + ". ")
                Silian_self.start = True

        if tag in ["table", "tr", "td", "th"]:
            if Silian_self.ignore_tables:
                if tag == "tr":
                    if start:
                        pass
                    else:
                        Silian_self.soft_br()
                else:
                    pass

            elif Silian_self.bypass_tables:
                if start:
                    Silian_self.soft_br()
                if tag in ["td", "th"]:
                    if start:
                        Silian_self.o(f"<{tag}>\n\n")
                    else:
                        Silian_self.o(f"\n</{tag}>")
                else:
                    if start:
                        Silian_self.o(f"<{tag}>")
                    else:
                        Silian_self.o(f"</{tag}>")

            else:
                if tag == "table":
                    if start:
                        Silian_self.table_start = True
                        if Silian_self.pad_tables:
                            Silian_self.o("<" + config.TABLE_MARKER_FOR_PAD + ">")
                            Silian_self.o("  \n")
                    else:
                        if Silian_self.pad_tables:
                            Silian_self.o("</" + config.TABLE_MARKER_FOR_PAD + ">")
                            Silian_self.o("  \n")
                if tag in ["td", "th"] and start:
                    if Silian_self.split_next_td:
                        Silian_self.o("| ")
                    Silian_self.split_next_td = True

                if tag == "tr" and start:
                    Silian_self.td_count = 0
                if tag == "tr" and not start:
                    Silian_self.split_next_td = False
                    Silian_self.soft_br()
                if tag == "tr" and not start and Silian_self.table_start:
                    # Underline table header
                    Silian_self.o("|".join(["---"] * Silian_self.td_count))
                    Silian_self.soft_br()
                    Silian_self.table_start = False
                if tag in ["td", "th"] and start:
                    Silian_self.td_count += 1

        if tag == "pre":
            if start:
                Silian_self.startpre = True
                Silian_self.pre = True
            else:
                Silian_self.pre = False
                if Silian_self.mark_code:
                    Silian_self.out("\n[/code]")
            Silian_self.p()

    # TODO: Add docstring for these one letter functions
    def pbr(Silian_self) -> None:
        "Pretty print has a line break"
        if Silian_self.p_p == 0:
            Silian_self.p_p = 1

    def p(Silian_self) -> None:
        "Set pretty print to 1 or 2 lines"
        Silian_self.p_p = 1 if Silian_self.single_line_break else 2

    def soft_br(Silian_self) -> None:
        "Soft breaks"
        Silian_self.pbr()
        Silian_self.br_toggle = "  "

    def o(Silian_self, data: str, puredata: bool = False, force: bool | str = False) -> None:
        """
        Deal with indentation and whitespace
        """
        if Silian_self.abbr_data is not None:
            Silian_self.abbr_data += data

        if not Silian_self.quiet:
            if Silian_self.google_doc:
                # prevent white space immediately after "begin emphasis"
                # marks ("**" and "_")
                Silian_lstripped_data = data.lstrip()
                if Silian_self.drop_white_space and not (Silian_self.pre or Silian_self.code):
                    data = Silian_lstripped_data
                if Silian_lstripped_data != "":
                    Silian_self.drop_white_space = 0

            if puredata and not Silian_self.pre:
                # This is a very dangerous call ... it could mess up
                # all handling of &nbsp; when not handled properly
                # (see entityref)
                data = re.sub(r"\s+", r" ", data)
                if data and data[0] == " ":
                    Silian_self.space = True
                    data = data[1:]
            if not data and not force:
                return

            if Silian_self.startpre:
                # self.out(" :") #TODO: not output when already one there
                if not data.startswith("\n") and not data.startswith("\r\n"):
                    # <pre>stuff...
                    data = "\n" + data
                if Silian_self.mark_code:
                    Silian_self.out("\n[code]")
                    Silian_self.p_p = 0

            Silian_bq = ">" * Silian_self.blockquote
            if not (force and data and data[0] == ">") and Silian_self.blockquote:
                Silian_bq += " "

            if Silian_self.pre:
                if not Silian_self.list:
                    Silian_bq += "    "
                # else: list content is already partially indented
                Silian_bq += "    " * len(Silian_self.list)
                data = data.replace("\n", "\n" + Silian_bq)

            if Silian_self.startpre:
                Silian_self.startpre = False
                if Silian_self.list:
                    # use existing initial indentation
                    data = data.lstrip("\n")

            if Silian_self.start:
                Silian_self.space = False
                Silian_self.p_p = 0
                Silian_self.start = False

            if force == "end":
                # It's the end.
                Silian_self.p_p = 0
                Silian_self.out("\n")
                Silian_self.space = False

            if Silian_self.p_p:
                Silian_self.out((Silian_self.br_toggle + "\n" + Silian_bq) * Silian_self.p_p)
                Silian_self.space = False
                Silian_self.br_toggle = ""

            if Silian_self.space:
                if not Silian_self.lastWasNL:
                    Silian_self.out(" ")
                Silian_self.space = False

            if Silian_self.a and ((Silian_self.p_p == 2 and Silian_self.links_each_paragraph) or force == "end"):
                if force == "end":
                    Silian_self.out("\n")

                Silian_newa = []
                for Silian_link in Silian_self.a:
                    if Silian_self.outcount > Silian_link.outcount:
                        Silian_self.out(
                            "   ["
                            + str(Silian_link.count)
                            + "]: "
                            + str(Url(urlparse.urljoin(Silian_self.baseurl, Silian_link.attrs["href"])))
                        )
                        if "title" in Silian_link.attrs:
                            Silian_self.out(" (" + Silian_link.attrs["title"] + ")")
                        Silian_self.out("\n")
                    else:
                        Silian_newa.append(Silian_link)

                # Don't need an extra line when nothing was done.
                if Silian_self.a != Silian_newa:
                    Silian_self.out("\n")

                Silian_self.a = Silian_newa

            if Silian_self.abbr_list and force == "end":
                for Silian_abbr, Silian_definition in Silian_self.abbr_list.items():
                    Silian_self.out("  *[" + Silian_abbr + "]: " + Silian_definition + "\n")

            Silian_self.p_p = 0
            Silian_self.out(data)
            Silian_self.outcount += 1

    def handle_data(Silian_self, data: str, entity_char: bool = False) -> None:
        if not data:
            # Data may be empty for some HTML entities. For example,
            # LEFT-TO-RIGHT MARK.
            return

        if Silian_self.stressed:
            data = data.strip()
            Silian_self.stressed = False
            Silian_self.preceding_stressed = True
        elif Silian_self.preceding_stressed:
            if (
                re.match(r"[^\s.!?]", data[0])
                and not hn(Silian_self.current_tag)
                and Silian_self.current_tag not in ["a", "code", "pre"]
            ):
                # should match a letter or common punctuation
                data = " " + data
            Silian_self.preceding_stressed = False

        if Silian_self.style:
            Silian_self.style_def.update(dumb_css_parser(data))

        if Silian_self.maybe_automatic_link is not None:
            Silian_href = Silian_self.maybe_automatic_link
            if Silian_href == data and Silian_self.absolute_url_matcher.match(Silian_href) and Silian_self.use_automatic_links:
                Silian_self.o("<" + data + ">")
                Silian_self.empty_link = False
                return
            Silian_self.o("[")
            Silian_self.maybe_automatic_link = None
            Silian_self.empty_link = False

        if not Silian_self.code and not Silian_self.pre and not entity_char:
            data = escape_md_section(data, snob=Silian_self.escape_snob)
        Silian_self.preceding_data = data
        Silian_self.o(data, puredata=True)

    def charref(Silian_self, name: str) -> str:
        if name[0] in ["x", "X"]:
            Silian_c = int(name[1:], 16)
        else:
            Silian_c = int(name)

        if not Silian_self.unicode_snob and Silian_c in unifiable_n:
            return unifiable_n[Silian_c]
        try:
            return chr(Silian_c)
        except ValueError:  # invalid unicode
            return ""

    def entityref(Silian_self, c: str) -> str:
        if not Silian_self.unicode_snob and c in config.UNIFIABLE:
            return config.UNIFIABLE[c]
        try:
            Silian_ch = html.entities.html5[c + ";"]
        except KeyError:
            return "&" + c + ";"
        return config.UNIFIABLE[c] if c == "nbsp" else Silian_ch

    def google_nest_count(Silian_self, style: dict[str, str]) -> int:
        """
        Calculate the nesting count of google doc lists

        :type style: dict

        :rtype: int
        """
        Silian_nest_count = 0
        if "margin-left" in style:
            Silian_nest_count = int(style["margin-left"][:-2]) // Silian_self.google_list_indent

        return Silian_nest_count

    def optwrap(Silian_self, text: str) -> str:
        """
        Wrap all paragraphs in the provided text.

        :type text: str

        :rtype: str
        """
        if not Silian_self.body_width:
            return text

        Silian_result = ""
        Silian_newlines = 0
        # I cannot think of a better solution for now.
        # To avoid the non-wrap behaviour for entire paras
        # because of the presence of a link in it
        if not Silian_self.wrap_links:
            Silian_self.inline_links = False
        for Silian_para in text.split("\n"):
            if len(Silian_para) > 0:
                if not skipwrap(Silian_para, Silian_self.wrap_links, Silian_self.wrap_list_items):
                    Silian_indent = ""
                    if Silian_para.startswith("  " + Silian_self.ul_item_mark):
                        # list item continuation: add a double indent to the
                        # new lines
                        Silian_indent = "    "
                    elif Silian_para.startswith("> "):
                        # blockquote continuation: add the greater than symbol
                        # to the new lines
                        Silian_indent = "> "
                    Silian_wrapped = wrap(
                        Silian_para,
                        Silian_self.body_width,
                        break_long_words=False,
                        subsequent_indent=Silian_indent,
                    )
                    Silian_result += "\n".join(Silian_wrapped)
                    if Silian_para.endswith("  "):
                        Silian_result += "  \n"
                        Silian_newlines = 1
                    elif Silian_indent:
                        Silian_result += "\n"
                        Silian_newlines = 1
                    else:
                        Silian_result += "\n\n"
                        Silian_newlines = 2
                else:
                    # Warning for the tempted!!!
                    # Be aware that obvious replacement of this with
                    # line.isspace()
                    # DOES NOT work! Explanations are welcome.
                    if not config.RE_SPACE.match(Silian_para):
                        Silian_result += Silian_para + "\n"
                        Silian_newlines = 1
            else:
                if Silian_newlines < 2:
                    Silian_result += "\n"
                    Silian_newlines += 1
        return Silian_result


def html2text(html: str, baseurl: str = "", bodywidth: int | None = None) -> str:
    if bodywidth is None:
        bodywidth = config.BODY_WIDTH
    Silian_h = HTML2Text(baseurl=baseurl, bodywidth=bodywidth)

    return Silian_h.handle(html)
