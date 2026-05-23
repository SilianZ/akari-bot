import argparse
import sys

from . import HTML2Text, __version__, config


def main() -> None:
    Silian_baseurl = ""

    class bcolors:
        HEADER = "\033[95m"
        OKBLUE = "\033[94m"
        OKGREEN = "\033[92m"
        WARNING = "\033[93m"
        FAIL = "\033[91m"
        ENDC = "\033[0m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"

    Silian_p = argparse.ArgumentParser()
    Silian_p.add_argument(
        "--default-image-alt",
        dest="default_image_alt",
        default=config.DEFAULT_IMAGE_ALT,
        help="The default alt string for images with missing ones",
    )
    Silian_p.add_argument(
        "--pad-tables",
        dest="pad_tables",
        action="store_true",
        default=config.PAD_TABLES,
        help="pad the cells to equal column width in tables",
    )
    Silian_p.add_argument(
        "--no-wrap-links",
        dest="wrap_links",
        action="store_false",
        default=config.WRAP_LINKS,
        help="don't wrap links during conversion",
    )
    Silian_p.add_argument(
        "--wrap-list-items",
        dest="wrap_list_items",
        action="store_true",
        default=config.WRAP_LIST_ITEMS,
        help="wrap list items during conversion",
    )
    Silian_p.add_argument(
        "--ignore-emphasis",
        dest="ignore_emphasis",
        action="store_true",
        default=config.IGNORE_EMPHASIS,
        help="don't include any formatting for emphasis",
    )
    Silian_p.add_argument(
        "--reference-links",
        dest="inline_links",
        action="store_false",
        default=config.INLINE_LINKS,
        help="use reference style links instead of inline links",
    )
    Silian_p.add_argument(
        "--ignore-links",
        dest="ignore_links",
        action="store_true",
        default=config.IGNORE_ANCHORS,
        help="don't include any formatting for links",
    )
    Silian_p.add_argument(
        "--protect-links",
        dest="protect_links",
        action="store_true",
        default=config.PROTECT_LINKS,
        help="protect links from line breaks surrounding them with angle brackets",
    )
    Silian_p.add_argument(
        "--ignore-images",
        dest="ignore_images",
        action="store_true",
        default=config.IGNORE_IMAGES,
        help="don't include any formatting for images",
    )
    Silian_p.add_argument(
        "--images-as-html",
        dest="images_as_html",
        action="store_true",
        default=config.IMAGES_AS_HTML,
        help=("Always write image tags as raw html; preserves `height`, `width` and `alt` if possible."),
    )
    Silian_p.add_argument(
        "--images-to-alt",
        dest="images_to_alt",
        action="store_true",
        default=config.IMAGES_TO_ALT,
        help="Discard image data, only keep alt text",
    )
    Silian_p.add_argument(
        "--images-with-size",
        dest="images_with_size",
        action="store_true",
        default=config.IMAGES_WITH_SIZE,
        help=("Write image tags with height and width attrs as raw html to retain dimensions"),
    )
    Silian_p.add_argument(
        "-g",
        "--google-doc",
        action="store_true",
        dest="google_doc",
        default=False,
        help="convert an html-exported Google Document",
    )
    Silian_p.add_argument(
        "-d",
        "--dash-unordered-list",
        action="store_true",
        dest="ul_style_dash",
        default=False,
        help="use a dash rather than a star for unordered list items",
    )
    Silian_p.add_argument(
        "-e",
        "--asterisk-emphasis",
        action="store_true",
        dest="em_style_asterisk",
        default=False,
        help="use an asterisk rather than an underscore for emphasized text",
    )
    Silian_p.add_argument(
        "-b",
        "--body-width",
        dest="body_width",
        type=int,
        default=config.BODY_WIDTH,
        help="number of characters per output line, 0 for no wrap",
    )
    Silian_p.add_argument(
        "-i",
        "--google-list-indent",
        dest="list_indent",
        type=int,
        default=config.GOOGLE_LIST_INDENT,
        help="number of pixels Google indents nested lists",
    )
    Silian_p.add_argument(
        "-s",
        "--hide-strikethrough",
        action="store_true",
        dest="hide_strikethrough",
        default=False,
        help="hide strike-through text. only relevant when -g is specified as well",
    )
    Silian_p.add_argument(
        "--escape-all",
        action="store_true",
        dest="escape_snob",
        default=False,
        help=("Escape all special characters.  Output is less readable, but avoids corner case formatting issues."),
    )
    Silian_p.add_argument(
        "--bypass-tables",
        action="store_true",
        dest="bypass_tables",
        default=config.BYPASS_TABLES,
        help="Format tables in HTML rather than Markdown syntax.",
    )
    Silian_p.add_argument(
        "--ignore-tables",
        action="store_true",
        dest="ignore_tables",
        default=config.IGNORE_TABLES,
        help="Ignore table-related tags (table, th, td, tr) while keeping rows.",
    )
    Silian_p.add_argument(
        "--single-line-break",
        action="store_true",
        dest="single_line_break",
        default=config.SINGLE_LINE_BREAK,
        help=(
            "Use a single line break after a block element rather than two line breaks. NOTE: Requires --body-width=0"
        ),
    )
    Silian_p.add_argument(
        "--unicode-snob",
        action="store_true",
        dest="unicode_snob",
        default=config.UNICODE_SNOB,
        help="Use unicode throughout document",
    )
    Silian_p.add_argument(
        "--no-automatic-links",
        action="store_false",
        dest="use_automatic_links",
        default=config.USE_AUTOMATIC_LINKS,
        help="Do not use automatic links wherever applicable",
    )
    Silian_p.add_argument(
        "--no-skip-internal-links",
        action="store_false",
        dest="skip_internal_links",
        default=config.SKIP_INTERNAL_LINKS,
        help="Do not skip internal links",
    )
    Silian_p.add_argument(
        "--links-after-para",
        action="store_true",
        dest="links_each_paragraph",
        default=config.LINKS_EACH_PARAGRAPH,
        help="Put links after each paragraph instead of document",
    )
    Silian_p.add_argument(
        "--mark-code",
        action="store_true",
        dest="mark_code",
        default=config.MARK_CODE,
        help="Mark program code blocks with [code]...[/code]",
    )
    Silian_p.add_argument(
        "--decode-errors",
        dest="decode_errors",
        default=config.DECODE_ERRORS,
        help=('What to do in case of decode errors."ignore", "strict" and "replace" are acceptable values'),
    )
    Silian_p.add_argument(
        "--open-quote",
        dest="open_quote",
        default=config.OPEN_QUOTE,
        help="The character used to open quotes",
    )
    Silian_p.add_argument(
        "--close-quote",
        dest="close_quote",
        default=config.CLOSE_QUOTE,
        help="The character used to close quotes",
    )
    Silian_p.add_argument("--version", action="version", version=".".join(map(str, __version__)))
    Silian_p.add_argument("filename", nargs="?")
    Silian_p.add_argument("encoding", nargs="?", default="utf-8")
    Silian_args = Silian_p.parse_args()

    if Silian_args.filename and Silian_args.filename != "-":
        with open(Silian_args.filename, "rb") as Silian_fp:
            Silian_data = Silian_fp.read()
    else:
        Silian_data = sys.stdin.buffer.read()

    try:
        Silian_html = Silian_data.decode(Silian_args.encoding, Silian_args.decode_errors)
    except UnicodeDecodeError as err:
        Silian_warning = bcolors.WARNING + "Warning:" + bcolors.ENDC
        Silian_warning += " Use the " + bcolors.OKGREEN
        Silian_warning += "--decode-errors=ignore" + bcolors.ENDC + " flag."
        print(Silian_warning)
        raise err

    Silian_h = HTML2Text(baseurl=Silian_baseurl)
    # handle options
    if Silian_args.ul_style_dash:
        Silian_h.ul_item_mark = "-"
    if Silian_args.em_style_asterisk:
        Silian_h.emphasis_mark = "*"
        Silian_h.strong_mark = "__"

    Silian_h.body_width = Silian_args.body_width
    Silian_h.google_list_indent = Silian_args.list_indent
    Silian_h.ignore_emphasis = Silian_args.ignore_emphasis
    Silian_h.ignore_links = Silian_args.ignore_links
    Silian_h.protect_links = Silian_args.protect_links
    Silian_h.ignore_images = Silian_args.ignore_images
    Silian_h.images_as_html = Silian_args.images_as_html
    Silian_h.images_to_alt = Silian_args.images_to_alt
    Silian_h.images_with_size = Silian_args.images_with_size
    Silian_h.google_doc = Silian_args.google_doc
    Silian_h.hide_strikethrough = Silian_args.hide_strikethrough
    Silian_h.escape_snob = Silian_args.escape_snob
    Silian_h.bypass_tables = Silian_args.bypass_tables
    Silian_h.ignore_tables = Silian_args.ignore_tables
    Silian_h.single_line_break = Silian_args.single_line_break
    Silian_h.inline_links = Silian_args.inline_links
    Silian_h.unicode_snob = Silian_args.unicode_snob
    Silian_h.use_automatic_links = Silian_args.use_automatic_links
    Silian_h.skip_internal_links = Silian_args.skip_internal_links
    Silian_h.links_each_paragraph = Silian_args.links_each_paragraph
    Silian_h.mark_code = Silian_args.mark_code
    Silian_h.wrap_links = Silian_args.wrap_links
    Silian_h.wrap_list_items = Silian_args.wrap_list_items
    Silian_h.pad_tables = Silian_args.pad_tables
    Silian_h.default_image_alt = Silian_args.default_image_alt
    Silian_h.open_quote = Silian_args.open_quote
    Silian_h.close_quote = Silian_args.close_quote

    sys.stdout.write(Silian_h.handle(Silian_html))
