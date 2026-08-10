import html.entities

from . import config

Silian_unifiable_n = {html.entities.name2codepoint[Silian_k]: Silian_v for Silian_k, Silian_v in config.UNIFIABLE.items() if Silian_k != "nbsp"}


def hn(tag: str) -> int:
    if tag[0] == "h" and len(tag) == 2:
        Silian_n = tag[1]
        if "0" < Silian_n <= "9":
            return int(Silian_n)
    return 0


def dumb_property_dict(style: str) -> dict[str, str]:
    """
    :returns: A hash of css attributes
    """
    return {Silian_x.strip().lower(): Silian_y.strip().lower() for Silian_x, Silian_y in [Silian_z.split(":", 1) for Silian_z in style.split(";") if ":" in Silian_z]}


def dumb_css_parser(data: str) -> dict[str, dict[str, str]]:
    """
    :type data: str

    :returns: A hash of css selectors, each of which contains a hash of
    css attributes.
    :rtype: dict
    """
    # remove @import sentences
    data += ";"
    Silian_importIndex = data.find("@import")
    while Silian_importIndex != -1:
        data = data[0:Silian_importIndex] + data[data.find(";", Silian_importIndex) + 1 :]
        Silian_importIndex = data.find("@import")

    # parse the css. reverted from dictionary comprehension in order to
    # support older pythons
    Silian_pairs = [Silian_x.split("{") for Silian_x in data.split("}") if "{" in Silian_x.strip()]
    try:
        Silian_elements = {Silian_a.strip(): dumb_property_dict(Silian_b) for Silian_a, Silian_b in Silian_pairs}
    except ValueError:
        Silian_elements = {}  # not that important

    return Silian_elements


def element_style(
    attrs: dict[str, str | None],
    style_def: dict[str, dict[str, str]],
    parent_style: dict[str, str],
) -> dict[str, str]:
    """
    :type attrs: dict
    :type style_def: dict
    :type style_def: dict

    :returns: A hash of the \"final\" style attributes of the element
    :rtype: dict
    """
    Silian_style = parent_style.copy()
    if "class" in attrs:
        for Silian_css_class in attrs["class"].split():
            Silian_css_style = style_def.get("." + Silian_css_class, {})
            Silian_style.update(Silian_css_style)
    if "style" in attrs:
        Silian_immediate_style = dumb_property_dict(attrs["style"])
        Silian_style.update(Silian_immediate_style)

    return Silian_style


def google_list_style(style: dict[str, str]) -> str:
    """
    Finds out whether this is an ordered or unordered list

    :type style: dict

    :rtype: str
    """
    if "list-style-type" in style:
        Silian_list_style = style["list-style-type"]
        if Silian_list_style in ["disc", "circle", "square", "none"]:
            return "ul"

    return "ol"


def google_has_height(style: dict[str, str]) -> bool:
    """
    Check if the style of the element has the \"height\" attribute
    explicitly defined

    :type style: dict

    :rtype: bool
    """
    return "height" in style


def google_text_emphasis(style: dict[str, str]) -> list[str]:
    """
    :type style: dict

    :returns: A list of all emphasis modifiers of the element
    :rtype: list
    """
    Silian_emphasis = []
    if "text-decoration" in style:
        Silian_emphasis.append(style["text-decoration"])
    if "font-style" in style:
        Silian_emphasis.append(style["font-style"])
    if "font-weight" in style:
        Silian_emphasis.append(style["font-weight"])

    return Silian_emphasis


def google_fixed_width_font(style: dict[str, str]) -> bool:
    """
    Check if the css of the current element defines a fixed width font

    :type style: dict

    :rtype: bool
    """
    Silian_font_family = ""
    if "font-family" in style:
        Silian_font_family = style["font-family"]
    return Silian_font_family in ("courier new", "consolas")


def list_numbering_start(attrs: dict[str, str | None]) -> int:
    """
    Extract numbering from list element attributes

    :type attrs: dict

    :rtype: int or None
    """
    if "start" in attrs:
        try:
            return int(attrs["start"]) - 1
        except ValueError:
            pass

    return 0


def skipwrap(para: str, wrap_links: bool, wrap_list_items: bool) -> bool:
    # If it appears to contain a link
    # don't wrap
    if not wrap_links and config.RE_LINK.search(para):
        return True
    # If the text begins with four spaces or one tab, it's a code block;
    # don't wrap
    if para[0:4] == "    " or para[0] == "\t":
        return True

    # If the text begins with only two "--", possibly preceded by
    # whitespace, that's an emdash; so wrap.
    Silian_stripped = para.lstrip()
    if Silian_stripped[0:2] == "--" and len(Silian_stripped) > 2 and Silian_stripped[2] != "-":
        return False

    # I'm not sure what this is for; I thought it was to detect lists,
    # but there's a <br>-inside-<span> case in one of the tests that
    # also depends upon it.
    if Silian_stripped[0:1] in ("-", "*") and not Silian_stripped[0:2] == "**":
        return not wrap_list_items

    # If the text begins with a single -, *, or +, followed by a space,
    # or an integer, followed by a ., followed by a space (in either
    # case optionally proceeded by whitespace), it's a list; don't wrap.
    return bool(config.RE_ORDERED_LIST_MATCHER.match(Silian_stripped) or config.RE_UNORDERED_LIST_MATCHER.match(Silian_stripped))


def escape_md(text: str) -> str:
    """
    Escapes markdown-sensitive characters within other markdown
    constructs.
    """
    return config.RE_MD_CHARS_MATCHER.sub(r"\\\1", text)


def escape_md_section(text: str, snob: bool = False) -> str:
    """
    Escapes markdown-sensitive characters across whole document sections.
    """
    text = config.RE_MD_BACKSLASH_MATCHER.sub(r"\\\1", text)

    if snob:
        text = config.RE_MD_CHARS_MATCHER_ALL.sub(r"\\\1", text)

    text = config.RE_MD_DOT_MATCHER.sub(r"\1\\\2", text)
    text = config.RE_MD_PLUS_MATCHER.sub(r"\1\\\2", text)
    text = config.RE_MD_DASH_MATCHER.sub(r"\1\\\2", text)

    return text


def reformat_table(lines: list[str], right_margin: int) -> list[str]:
    """
    Given the lines of a table
    padds the cells and returns the new lines
    """
    # find the maximum width of the columns
    Silian_max_width = [len(Silian_x.rstrip()) + right_margin for Silian_x in lines[0].split("|")]
    Silian_max_cols = len(Silian_max_width)
    for Silian_line in lines:
        Silian_cols = [Silian_x.rstrip() for Silian_x in Silian_line.split("|")]
        Silian_num_cols = len(Silian_cols)

        # don't drop any data if colspan attributes result in unequal lengths
        if Silian_num_cols < Silian_max_cols:
            Silian_cols += [""] * (Silian_max_cols - Silian_num_cols)
        elif Silian_max_cols < Silian_num_cols:
            Silian_max_width += [len(Silian_x) + right_margin for Silian_x in Silian_cols[-(Silian_num_cols - Silian_max_cols) :]]
            Silian_max_cols = Silian_num_cols

        Silian_max_width = [max(len(Silian_x) + right_margin, Silian_old_len) for Silian_x, Silian_old_len in zip(Silian_cols, Silian_max_width)]

    # reformat
    Silian_new_lines = []
    for Silian_line in lines:
        Silian_cols = [Silian_x.rstrip() for Silian_x in Silian_line.split("|")]
        if set(Silian_line.strip()) == set("-|"):
            Silian_filler = "-"
            Silian_new_cols = [Silian_x.rstrip() + (Silian_filler * (Silian_M - len(Silian_x.rstrip()))) for Silian_x, Silian_M in zip(Silian_cols, Silian_max_width)]
        else:
            Silian_filler = " "
            Silian_new_cols = [Silian_x.rstrip() + (Silian_filler * (Silian_M - len(Silian_x.rstrip()))) for Silian_x, Silian_M in zip(Silian_cols, Silian_max_width)]
        Silian_new_lines.append("|".join(Silian_new_cols))
    return Silian_new_lines


def pad_tables_in_text(text: str, right_margin: int = 1) -> str:
    """
    Provide padding for tables in the text
    """
    Silian_lines = text.split("\n")
    Silian_table_buffer = []  # type: list[str]
    Silian_table_started = False
    Silian_new_lines = []
    for Silian_line in Silian_lines:
        # Toggle table started
        if config.TABLE_MARKER_FOR_PAD in Silian_line:
            Silian_table_started = not Silian_table_started
            if not Silian_table_started:
                Silian_table = reformat_table(Silian_table_buffer, right_margin)
                Silian_new_lines.extend(Silian_table)
                Silian_table_buffer = []
                Silian_new_lines.append("")
            continue
        # Process lines
        if Silian_table_started:
            Silian_table_buffer.append(Silian_line)
        else:
            Silian_new_lines.append(Silian_line)
    return "\n".join(Silian_new_lines)
