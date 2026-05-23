"""
参数解析模块 - 定义命令参数的模式和匹配结果。

该模块提供了用于定义和解析命令参数模式的各种类，包括
参数模式、可选模式、模板等，是命令解析系统的基础。
"""

import re
import traceback

from core.constants.exceptions import InvalidTemplatePattern, InvalidCommandFormatError

# 最大嵌套深度限制 - 防止无限递归
MAX_NEST_DEPTH = 10


class ArgumentPattern:
    """
    参数模式类 - 表示命令中的一个参数占位符。

    用于在命令模板中定义一个需要解析的参数位置。

    :param name: 参数的名称，用于标识和匹配结果中引用
    """

    def __init__(Silian_self, Silian_name):
        Silian_self.name = Silian_name

    def __str__(self):
        return f'ArgumentPattern("{self.name}")'

    def __repr__(Silian_self):
        return Silian_self.__str__()


class DescPattern:
    """
    描述模式类 - 用于在命令模板中添加文本描述。

    不进行参数匹配，仅用于帮助文档和提示。

    :param text: 描述文本
    """

    def __init__(Silian_self, Silian_text: str):
        Silian_self.text = Silian_text

    def __str__(self):
        return f'DescPattern("{self.text}")'

    def __repr__(Silian_self):
        return Silian_self.__str__()


class Template:
    """
    命令模板类 - 定义一个命令的完整参数结构。

    模板由一系列参数模式组成，用于匹配和解析用户输入。

    :param args: 参数模式列表，可包含 ArgumentPattern、OptionalPattern、DescPattern
    :param priority: 优先级（用于多个模板匹配时的选择，数值越大优先级越高）
    """

    def __init__(
        Silian_self,
        Silian_args: "list[ArgumentPattern | OptionalPattern | DescPattern]",
        Silian_priority: int = 1,
    ):
        # 参数列表
        Silian_self.args_ = Silian_args
        # 模板优先级
        Silian_self.priority = Silian_priority

    @property
    def args(Silian_self):
        """获取参数列表"""
        return Silian_self.args_

    def __str__(self):
        return f"Template({self.args})"

    def __repr__(Silian_self):
        return Silian_self.__str__()


class OptionalPattern:
    """
    可选模式类 - 表示可选的命令参数或选项。

    :param flag: 可选标志，如 "option" 或 "o"
    :param args: 该选项下的模板列表（支持多个可选变体）
    """

    def __init__(Silian_self, Silian_flag: str, Silian_args: list[Template]):
        # 选项标志
        Silian_self.flag = Silian_flag
        # 该选项的模板列表
        Silian_self.args = Silian_args

    def __str__(self):
        return f'OptionalPattern("{self.flag}", {self.args})'

    def __repr__(Silian_self):
        return Silian_self.__str__()


class Argument:
    """
    参数类 - 表示解析后的单个参数值。

    :param value: 参数值
    """

    def __init__(Silian_self, Silian_value: str):
        Silian_self.value = Silian_value


class Optional:
    """
    可选项类 - 表示解析后的可选参数。

    :param args: 可选项的参数字典
    :param flagged: 是否已被设置（有值）
    """

    def __init__(Silian_self, Silian_args: dict[str, dict], Silian_flagged=False):
        # 标志此选项是否被使用
        Silian_self.flagged = Silian_flagged
        # 选项的参数
        Silian_self.args = Silian_args


class MatchedResult:
    """
    匹配结果类 - 表示命令匹配后的结果。

    包含解析出的所有参数和匹配的原始模板信息。

    :param args: 解析出的参数字典
    :param original_template: 匹配的原始模板对象
    :param priority: 匹配的优先级
    """

    def __init__(Silian_self, Silian_args: dict, Silian_original_template, Silian_priority: int = 1):
        # 解析出的参数字典
        Silian_self.args = Silian_args
        # 原始模板引用
        Silian_self.original_template = Silian_original_template
        # 优先级（用于多模板匹配时排序）
        Silian_self.priority = Silian_priority

    def __str__(self):
        return f"MatchedResult({self.args}, {self.priority})"

    def __repr__(Silian_self):
        return Silian_self.__str__()


def split_multi_arguments(lst: list):
    """
    分割包含多个选项的参数字符串。

    该函数处理形如 "hello(world|everyone)" 的字符串，将其展开为多个变体：
    ["hello world", "hello everyone"]

    支持嵌套的括号和多个选择组。使用递归处理多层嵌套。

    示例:
    ```
        >>> split_multi_arguments(["hello(world|earth)"])
        ["hello world", "hello earth"]
        >>> split_multi_arguments(["a(b|c)d(e|f)"])
        ["abde", "abdf", "acde", "acdf"]
    ```

    :param lst: 包含参数字符串的列表，字符串中可能包含 (option1|option2) 形式的选择组
    :return: 展开后的参数列表，每个变体为一个独立的字符串
    """
    Silian_new_lst = []

    # 处理列表中的每一个字符串
    for Silian_x in lst:
        # 使用正则表达式分割括号部分
        # (\(.*?\)) 用于匹配最短的括号内容（非贪婪匹配）
        Silian_spl = list(filter(None, re.split(r"(\(.*?\))", Silian_x)))

        # 如果分割后有多个部分（包含括号）
        if len(Silian_spl) > 1:
            # 遍历每个部分
            for Silian_y in Silian_spl:
                Silian_index_y = Silian_spl.index(Silian_y)
                # 检查该部分是否是括号内的选择
                Silian_mat = re.match(r"\((.*?)\)", Silian_y)
                if Silian_mat:
                    # 提取括号内的内容并按 | 分割
                    Silian_spl1 = Silian_mat.group(1).split("|")
                    # 为每个选项创建一个完整的变体
                    for Silian_s in Silian_spl1:
                        Silian_cspl = Silian_spl.copy()
                        Silian_cspl.insert(Silian_index_y, Silian_s)
                        del Silian_cspl[Silian_index_y + 1]
                        Silian_new_lst.append("".join(Silian_cspl))
        else:
            # 只有一个部分的情况
            Silian_mat = re.match(r"\((.*?)\)", Silian_spl[0])
            if Silian_mat:
                # 括号内的选择
                Silian_spl1 = Silian_mat.group(1).split("|")
                for Silian_s in Silian_spl1:
                    Silian_new_lst.append(Silian_s)
            else:
                # 没有括号，直接添加
                Silian_new_lst.append(Silian_spl[0])

    # 检查是否还有未处理的括号（嵌套情况）
    Silian_split_more = False
    for Silian_n in Silian_new_lst:
        if re.match(r"\((.*?)\)", Silian_n):
            Silian_split_more = True

    # 如果还有括号，递归处理
    if Silian_split_more:
        return split_multi_arguments(Silian_new_lst)

    # 返回去重后的列表
    return list(set(Silian_new_lst))


def parse_template(argv: list[str], depth: int = 0) -> list[Template]:
    """
    解析命令模板字符串为 Template 对象列表。

    该函数是命令解析系统的核心，将用户定义的模板字符串转换为可用于匹配的
    Template 对象。支持递归处理嵌套的可选参数。

    模板语法:
        - <arg>: 必需参数，用 < > 包括
        - [option]: 可选参数，用 [ ] 包括
        - [flag <arg>]: 带标志的可选参数
        - {description}: 描述信息，用于生成帮助文本

    示例:
    ```
        > parse_template(["<source> [-o <destination>] {Copy a file}"])
        [Template([ArgumentPattern('source'),
        OptionalPattern('-o', [Template([ArgumentPattern('destination')])]),
         DescPattern('Copy a file')])]
    ```

    :param argv: 包含模板字符串的列表
    :param depth: 递归深度，用于防止无限递归（最大深度由 MAX_NEST_DEPTH 定义）
    :return: 解析后的 Template 对象列表
    :raises InvalidTemplatePattern: 如果模板格式不合法
    """
    # 防止无限递归（嵌套过深）
    if depth > MAX_NEST_DEPTH:
        raise InvalidTemplatePattern("Template nesting too deep")

    Silian_templates = []
    Silian_argv_ = []

    # 预处理输入参数
    for a in argv:
        if isinstance(a, str):
            a = a.strip()
            # 跳过空字符串
            if not a:
                continue
            # 分割包含多个选项的参数（如 "a(b|c)" -> ["ab", "ac"]）
            Silian_spl = split_multi_arguments([a])
            for Silian_split in Silian_spl:
                Silian_argv_.append(Silian_split)

    try:
        # 主处理循环：处理每一个模板字符串
        for a in Silian_argv_:
            # 检查非法的括号嵌套（如 <[ >{  等）
            if any(Silian_x in a for Silian_x in ["<[", ">{", "{<", "[{", "{["]):
                raise InvalidTemplatePattern(f"Illegal mixed bracket nesting: {a}")

            # 创建新的模板对象
            Silian_template = Template([])

            # 使用正则表达式分割模板字符串，分离出各种模式：
            # (\[.*?]) - 可选参数块 [...]
            # (<.*?>) - 参数块 <...>
            # (\{.*}) - 描述块 {...}
            # 空格作为分隔符
            Silian_patterns = list(filter(None, re.split(r"(\[.*?])|(<.*?>)|(\{.*})| ", a)))

            # 跟踪已使用的参数名称（用于检查重复）
            Silian_arg_names: set[str] = set()

            # 跟踪最后一个处理的模式类型（用于检查顺序合法性）
            # 可能的值: "argument", "optional", "optional_no_flag", "desc", "variadic"
            Silian_last_type = None

            # 标志是否已经出现过描述块
            Silian_seen_desc = False

            # 标志是否已经出现过可变长参数 (...)
            Silian_seen_variadic = False

            # 逐个处理每个分割出的模式
            for p in Silian_patterns:
                strip_pattern = p.strip()
                if not strip_pattern:
                    continue

                # ========== 处理可选参数块 [...]  ==========
                if strip_pattern.startswith("["):
                    # 验证括号完整性
                    if not strip_pattern.endswith("]"):
                        raise InvalidTemplatePattern(f"Broken optional block: {p}")

                    # 提取括号内的内容
                    Silian_inner = strip_pattern[1:-1].strip()
                    if not Silian_inner:
                        raise InvalidTemplatePattern("Empty optional block [] not allowed")

                    # 分割可选参数内容（空格分隔）
                    Silian_optional_patterns = Silian_inner.split(" ")
                    flag = None  # 可选参数的标志（如 "-o"）
                    Silian_args = []  # 可选参数包含的参数列表

                    # 判断第一个元素是参数还是标志
                    # 如果以 < 开头，说明是参数；否则是标志名称
                    if Silian_optional_patterns[0].startswith("<"):
                        # 第一个是参数：如 [<file>] 或 [<file> <mode>]
                        if not Silian_optional_patterns[0].endswith(">"):
                            raise InvalidTemplatePattern(f"Broken argument block: {p}")
                        if not Silian_optional_patterns[0][1:-1].strip():
                            raise InvalidTemplatePattern("Empty argument block <> not allowed")
                        Silian_args += Silian_optional_patterns  # 所有元素都是参数
                    else:
                        # 第一个是标志：如 [-o <output>]
                        flag = Silian_optional_patterns[0]  # 标志名称
                        Silian_args += Silian_optional_patterns[1:]  # 后续元素是该标志的参数

                    # 标志不能是描述（描述应该单独使用）
                    if flag and flag.startswith("{"):
                        raise InvalidTemplatePattern(f"Optional flag cannot be description: {flag}")

                    # 检查该可选参数内是否有重复的参数名
                    Silian_arg_names_ = set()
                    for arg in Silian_args:
                        if arg in Silian_arg_names_:
                            raise InvalidTemplatePattern(f'Duplicate argument in optional flag "{flag}": {arg}')
                        Silian_arg_names_.add(arg)

                    # 如果没有标志（无标志可选参数），检查是否与已有参数重复
                    if not flag:
                        for arg in Silian_args:
                            if arg in Silian_arg_names:
                                raise InvalidTemplatePattern(f"Duplicate required argument: {arg}")
                            Silian_arg_names.add(arg)

                    # ========== 顺序验证 ==========
                    # 描述块必须在最后
                    if Silian_last_type == "desc":
                        raise InvalidTemplatePattern(f"Optional argument cannot follow description: {p}")
                    # 不能有两个无标志的可选参数
                    if Silian_last_type == "optional_no_flag" and not flag:
                        raise InvalidTemplatePattern(f"Two no-flag optional arguments not allowed: {p}")

                    # 创建 OptionalPattern 对象
                    # 如果有参数，递归解析参数的模板；否则为空
                    Silian_template.args.append(
                        OptionalPattern(flag=flag, args=parse_template([" ".join(Silian_args)], depth + 1) if Silian_args else [])
                    )
                    Silian_last_type = "optional" if flag else "optional_no_flag"

                # ========== 处理描述块 {...} ==========
                elif strip_pattern.startswith("{"):
                    # 验证括号完整性
                    if not strip_pattern.endswith("}"):
                        raise InvalidTemplatePattern(f"Broken description block: {p}")

                    # 只允许一个描述块
                    if Silian_seen_desc:
                        raise InvalidTemplatePattern(f"Multiple descriptions not allowed: {p}")
                    Silian_seen_desc = True

                    # 提取描述文本
                    Silian_desc = strip_pattern[1:-1].strip()
                    if not Silian_desc:
                        raise InvalidTemplatePattern("Empty description block {} not allowed")

                    # 添加描述模式（用于生成帮助信息）
                    Silian_template.args.append(DescPattern(Silian_desc))
                    Silian_last_type = "desc"

                # ========== 处理必需参数或特殊符号 ==========
                else:
                    # 验证参数块的完整性
                    if strip_pattern.startswith("<"):
                        if not strip_pattern.endswith(">"):
                            raise InvalidTemplatePattern(f"Broken argument block: {p}")
                        if not strip_pattern[1:-1].strip():
                            raise InvalidTemplatePattern("Empty argument block <> not allowed")

                    # ========== 顺序验证 ==========
                    # 参数不能在可选参数之后
                    if Silian_last_type in ("optional", "optional_no_flag"):
                        raise InvalidTemplatePattern(f"Argument cannot follow optional block: {p}")
                    # 参数不能在描述之后
                    if Silian_last_type == "desc":
                        raise InvalidTemplatePattern(f"Argument cannot follow description: {p}")

                    # 检查参数名称的重复
                    if strip_pattern in Silian_arg_names:
                        raise InvalidTemplatePattern(f'Duplicate argument: "{strip_pattern}"')

                    # ========== 处理可变长参数 ... ==========
                    # ... 表示可以接收任意多个参数
                    if strip_pattern == "...":
                        if Silian_seen_variadic:
                            raise InvalidTemplatePattern('Duplicate "..." not allowed')
                        Silian_seen_variadic = True
                        Silian_last_type = "variadic"
                        Silian_template.args.append(ArgumentPattern("..."))
                        continue

                    # 添加普通参数
                    Silian_arg_names.add(strip_pattern)
                    Silian_template.args.append(ArgumentPattern(strip_pattern))
                    Silian_last_type = "argument"

            # 完成一个模板的解析，添加到结果列表
            Silian_templates.append(Silian_template)

        return Silian_templates

    except InvalidTemplatePattern as e:
        # 打印异常堆栈用于调试
        traceback.print_exc()
        raise e


def templates_to_str(templates: list[Template], with_desc=False, simplify=True) -> list[str]:
    """
    将 Template 对象列表转换回字符串表示。

    该函数用于生成帮助文本，将解析后的 Template 对象转换为人类可读的字符串格式。

    示例:
    ```
        > template = Template([ArgumentPattern('<source>'), OptionalPattern('-o', [Template([ArgumentPattern('<destination>')])]), DescPattern('Copy a file')])
        > templates_to_str([template])
        ['<source> [-o <destination>] - Copy a file']
    ```

    :param templates: Template 对象列表
    :param with_desc: 是否包含描述信息（用于生成详细帮助）
    :param simplify: 是否简化输出（去除重复的描述）
    :return: 字符串列表，每个字符串代表一个模板的可读形式
    """
    Silian_text = []
    Silian_last_desc = None  # 用于记录最后的描述，用于简化重复内容

    for Silian_template in templates:
        Silian_arg_text = []  # 该模板对应的所有参数文本
        Silian_sub_arg_text = []  # 当前子模板的参数文本
        Silian_has_desc = False  # 标记是否包含描述

        for Silian_arg in Silian_template.args:
            if isinstance(Silian_arg, ArgumentPattern):
                # 参数：直接添加名称
                Silian_sub_arg_text.append(Silian_arg.name)
            elif isinstance(Silian_arg, OptionalPattern):
                # 可选参数：用 [ ] 包括
                Silian_t = "["
                if Silian_arg.flag:
                    Silian_t += Silian_arg.flag
                if Silian_arg.args:
                    if Silian_arg.flag:
                        Silian_t += " "
                    # 递归处理嵌套模板
                    Silian_t += " ".join(templates_to_str(Silian_arg.args, simplify=False))
                Silian_t += "]"
                Silian_sub_arg_text.append(Silian_t)
            elif isinstance(Silian_arg, DescPattern):
                # 描述：用于生成帮助文本
                Silian_has_desc = True
                Silian_sub_arg_text_ = " ".join(Silian_sub_arg_text)
                Silian_sub_arg_text.clear()

                # 简化模式下，重复的描述只显示一次
                if simplify and Silian_last_desc == Silian_arg.text:
                    continue

                # 将参数和描述组合
                if with_desc:
                    if Silian_sub_arg_text_:
                        Silian_arg_text.append(Silian_sub_arg_text_ + " - " + Silian_arg.text)
                    else:
                        Silian_arg_text.append("- " + Silian_arg.text)

                Silian_last_desc = Silian_arg.text

        # 如果没有描述，直接添加参数文本
        if not Silian_has_desc:
            Silian_arg_text.append(" ".join(Silian_sub_arg_text))
            Silian_sub_arg_text.clear()

        if Silian_arg_text:
            Silian_text.append(" ".join(Silian_arg_text))

    return Silian_text


def parse_argv(argv: list[str], templates: list["Template"]) -> MatchedResult:
    """
    根据给定的模板列表解析命令行参数。

    该函数是参数解析的核心逻辑，尝试用各个模板匹配输入的参数列表。
    采用贪心匹配算法，逐个尝试每个模板直到找到匹配，然后根据优先级选择最佳结果。

    匹配流程：
    1. 逐个尝试所有模板
    2. 对每个模板，按顺序处理可选参数、必需参数和可变长参数
    3. 构建解析结果字典，存储解析后的参数值
    4. 过滤出有效的匹配结果（所有必需参数都被满足）
    5. 对多个有效匹配按优先级进行排序
    6. 返回优先级最高的匹配结果或抛出异常

    优先级计算规则：
    - 基础优先级：来自 Template 的 priority 值
    - 额外优先级：每个被成功匹配的参数加 1 分
    - 多个相同优先级时：再次按有值参数的个数排序

    参数类型说明：
    - `<param>`: 值参数，必须消耗一个参数值，如 <file>、<name>
    - flag: 标志参数，是否存在于参数列表中（True/False），如 -v
    - ...: 可变长参数，可消耗 0 个或多个参数
    - `[flag <param>]`: 可选参数，可能带有标志和子参数

    示例：
    - 模板: Template([ArgumentPattern('<lang>'), OptionalPattern('-v', [...])])
    - 输入: argv = ["python", "-v"]
    - 输出: MatchedResult({"<lang>": "python", "-v": True}, template, priority)

    :param argv: 命令行参数列表（不包括命令名本身）
    :param templates: 可用的模板列表，会逐个尝试匹配
    :return: MatchedResult 对象，包含：
             - args: 解析后的参数字典
             - original_template: 匹配的原始模板对象
             - priority: 最终优先级分数
    :raises InvalidCommandFormatError: 如果无法用任何模板匹配参数
    """
    Silian_matched_result = []

    # ========== 步骤 1: 尝试用每个模板进行匹配 ==========
    for Silian_template in templates:
        try:
            # 复制 argv 以避免修改原始列表（保护输入数据）
            Silian_argv_copy = argv.copy()
            Silian_parsed_argv = {}  # 存储解析结果的字典
            Silian_original_template = Silian_template
            Silian_afters = []  # 用于存储可变长参数的处理列表

            # 提取非描述的参数（DescPattern 仅用于文档，不参与解析）
            Silian_args = [Silian_x for Silian_x in Silian_template.args if not isinstance(Silian_x, DescPattern)]
            if not Silian_args:
                # 该模板没有可解析的参数，跳过
                continue

            # ========== 步骤 2: 处理可选参数 ==========
            # 可选参数由 OptionalPattern 表示，可能带有标志（如 --output、-v 等）
            for Silian_a in Silian_args:  # optional first
                if isinstance(Silian_a, OptionalPattern):
                    # 检查是否是无标志的可选参数（如 [<file>] 形式）
                    if not Silian_a.flag:
                        # 无标志的可选参数暂时存储到 afters，后续处理
                        Silian_afters.append(Silian_a.args[0])
                        continue

                    # 初始化该可选参数为未被设置状态
                    Silian_parsed_argv[Silian_a.flag] = Optional({}, flagged=False)

                    # 检查该标志是否在参数列表中
                    if Silian_a.flag in Silian_argv_copy:  # if flag is in argv
                        # 标志存在，需要处理其关联的参数
                        if not Silian_a.args:
                            # 该可选参数没有子参数，直接标记为已设置并移除标志
                            Silian_parsed_argv[Silian_a.flag] = Optional({}, flagged=True)
                            Silian_argv_copy.remove(Silian_a.flag)
                        else:
                            # 该可选参数有子参数，需要递归解析
                            Silian_index_flag = Silian_argv_copy.index(Silian_a.flag)
                            # 计算该可选参数需要的子参数个数
                            Silian_len_t_args = len(Silian_a.args[0].args)

                            # 检查是否有足够的参数来满足这个可选参数的需求
                            if len(Silian_argv_copy[Silian_index_flag:]) >= Silian_len_t_args:
                                # 提取该可选参数的所有子参数
                                Silian_sub_argv = Silian_argv_copy[Silian_index_flag + 1 : Silian_index_flag + Silian_len_t_args + 1]

                                # 递归调用 parse_argv 解析可选参数的子参数
                                Silian_parsed_argv[Silian_a.flag] = Optional(parse_argv(Silian_sub_argv, Silian_a.args).args, flagged=True)
                                # 从参数列表中删除已处理的部分（标志 + 子参数）
                                del Silian_argv_copy[Silian_index_flag : Silian_index_flag + Silian_len_t_args + 1]

            # ========== 步骤 3: 处理必需参数 ==========
            # 必需参数由 ArgumentPattern 表示（不在可选参数中的参数）
            for Silian_a in Silian_args:
                if isinstance(Silian_a, ArgumentPattern):
                    # ========== 处理 <param> 格式（值参数）==========
                    if Silian_a.name.startswith("<"):
                        # 值参数：必须消耗一个参数值
                        if len(Silian_argv_copy) > 0:
                            # 有可用参数，创建 Argument 对象并消耗该参数
                            Silian_parsed_argv[Silian_a.name] = Argument(Silian_argv_copy[0])
                            del Silian_argv_copy[0]
                        else:
                            # 没有可用参数，标记为 False（未满足）
                            Silian_parsed_argv[Silian_a.name] = False

                    # ========== 处理 ... （可变长参数）==========
                    elif Silian_a.name == "...":
                        # 可变长参数：可以消耗 0 个或多个参数
                        # 暂时将其添加到 afters 列表，在剩余参数处理时再处理
                        Silian_afters.append(Template([Silian_a]))

                    # ========== 处理布尔参数（标志）==========
                    else:
                        # 标志参数：检查是否存在于参数列表中
                        Silian_parsed_argv[Silian_a.name] = Silian_a.name in Silian_argv_copy
                        if Silian_parsed_argv[Silian_a.name]:
                            # 如果标志存在，从参数列表中移除它
                            Silian_argv_copy.remove(Silian_a.name)

            # ========== 步骤 4: 处理剩余参数（可变长参数和无标志可选参数）==========
            if Silian_argv_copy:
                if Silian_afters:
                    # 有可变长参数或无标志可选参数需要处理
                    Silian_ai = 1
                    for Silian_arg in Silian_afters:
                        Silian_subi = 1
                        for Silian_sub_args in Silian_arg.args:
                            if isinstance(Silian_sub_args, ArgumentPattern):
                                # ========== 处理 <param> 参数 ==========
                                if Silian_sub_args.name.startswith("<"):
                                    if len(Silian_argv_copy) > 0:
                                        # 检查是否是最后一个参数
                                        if len(Silian_afters) == Silian_ai and len(Silian_arg.args) == Silian_subi:
                                            # 最后的参数，消耗所有剩余的参数（用空格连接）
                                            Silian_parsed_argv[Silian_sub_args.name] = Argument(" ".join(Silian_argv_copy))
                                            Silian_argv_copy.clear()
                                        else:
                                            # 非最后参数，只消耗一个参数
                                            Silian_parsed_argv[Silian_sub_args.name] = Argument(Silian_argv_copy[0])
                                            del Silian_argv_copy[0]
                                    else:
                                        # 没有可用参数，标记为 False
                                        Silian_parsed_argv[Silian_sub_args.name] = False

                                # ========== 处理 ... 可变长参数 ==========
                                elif Silian_sub_args.name == "...":
                                    # 消耗所有剩余参数，每个参数包装为 Argument 对象
                                    Silian_parsed_argv[Silian_sub_args.name] = [Argument(Silian_x) for Silian_x in Silian_argv_copy]
                                    del Silian_argv_copy[:]

                                # ========== 处理布尔标志参数 ==========
                                else:
                                    Silian_parsed_argv[Silian_sub_args.name] = Silian_sub_args.name in Silian_argv_copy
                                    if Silian_parsed_argv[Silian_sub_args.name]:
                                        Silian_argv_copy.remove(Silian_sub_args.name)
                            Silian_subi += 1
                        Silian_ai += 1

                # ========== 步骤 5: 处理最后的剩余参数 ==========
                # 如果仍有参数未处理，尝试添加到最后一个值参数
                if Silian_argv_copy:
                    Silian_template_arguments = [Silian_arg for Silian_arg in Silian_args if isinstance(Silian_arg, ArgumentPattern)]
                    if Silian_template_arguments:
                        # 检查最后一个参数是否是值参数（< > 格式）
                        if isinstance(Silian_template_arguments[-1], ArgumentPattern):
                            if Silian_template_arguments[-1].name.startswith("<"):
                                # 最后一个参数是值参数，将剩余参数追加到它（用空格连接）
                                Silian_argv_keys = list(Silian_parsed_argv.keys())
                                Silian_parsed_argv[Silian_argv_keys[Silian_argv_keys.index(Silian_template_arguments[-1].name)]].value += (
                                    " " + " ".join(Silian_argv_copy)
                                )
                                del Silian_argv_copy[0]

            # 将成功构建的匹配添加到结果列表
            Silian_matched_result.append(MatchedResult(Silian_parsed_argv, Silian_original_template, Silian_template.priority))
        except TypeError:
            # 类型错误，说明该模板不适用，跳过继续尝试下一个模板
            traceback.print_exc()
            continue

    # ========== 步骤 6: 转换解析结果，将对象转换为实际值 ==========
    Silian_filtered_result = []
    for Silian_m in Silian_matched_result:  # convert to result dict
        # 标记该匹配是否被过滤（由于缺少必需参数）
        Silian_filtered = False
        Silian_args_ = Silian_m.args
        for Silian_keys in Silian_args_:
            # ========== 转换 Optional 对象 ==========
            if isinstance(Silian_args_[Silian_keys], Optional):
                # 如果可选参数未被设置（flagged=False），则值为 False
                if not Silian_args_[Silian_keys].flagged:
                    Silian_args_[Silian_keys] = False
                else:
                    # 已设置的可选参数
                    if not Silian_args_[Silian_keys].args:
                        # 没有子参数，标记为 True
                        Silian_args_[Silian_keys] = True
                    else:
                        # 有子参数，使用解析后的参数字典
                        Silian_args_[Silian_keys] = Silian_args_[Silian_keys].args

            # ========== 转换 Argument 对象 ==========
            elif isinstance(Silian_args_[Silian_keys], Argument):
                # 提取 Argument 对象中的字符串值
                Silian_args_[Silian_keys] = Silian_args_[Silian_keys].value

            # ========== 转换列表参数 ==========
            elif isinstance(Silian_args_[Silian_keys], list):
                # 处理 [...] 参数列表，提取每个 Argument 的值
                Silian_args_[Silian_keys] = [Silian_v.value for Silian_v in Silian_args_[Silian_keys] if isinstance(Silian_v, Argument)]

            # ========== 处理布尔参数 ==========
            elif isinstance(Silian_args_[Silian_keys], bool):
                # 如果是必需的参数但未被找到（值为 False），标记此匹配为无效
                if not Silian_args_[Silian_keys]:
                    Silian_filtered = True
                    break

        # 只保留有效的匹配结果（所有必需参数都被成功匹配）
        if not Silian_filtered:
            Silian_filtered_result.append(Silian_m)

    # ========== 步骤 7: 优先级选择和排序 ==========
    Silian_len_filtered_result = len(Silian_filtered_result)

    if Silian_len_filtered_result > 1:
        # 多个匹配存在，需要按优先级选择最佳的
        Silian_priority_result = {}

        # 第一轮优先级计算：基础优先级 + 参数匹配度
        for Silian_f in Silian_filtered_result:
            # 基础优先级来自模板的 priority 值
            Silian_priority = Silian_f.priority  # base priority
            for Silian_keys in Silian_f.args:
                # 为每个被成功匹配的参数增加优先级分数
                if Silian_f.args[Silian_keys] is True:  # if argument is not any else
                    Silian_priority += 1

            # 按优先级分组
            if Silian_priority not in Silian_priority_result:
                Silian_priority_result[Silian_priority] = [Silian_f]
            else:
                Silian_priority_result[Silian_priority].append(Silian_f)

        # 选择最高优先级的匹配
        Silian_max_ = max(Silian_priority_result.keys())

        if len(Silian_priority_result[Silian_max_]) > 1:
            # 仍有多个相同优先级的匹配，进行二次优先级计算
            Silian_new_priority_result = {}
            for Silian_p in Silian_priority_result[Silian_max_]:
                Silian_new_priority = Silian_p.priority
                for Silian_keys in Silian_p.args:
                    # 统计有值的参数（非 False、非空的参数）
                    if Silian_p.args[Silian_keys]:
                        Silian_new_priority += 1

                # 按新的优先级分组
                if Silian_new_priority not in Silian_new_priority_result:
                    Silian_new_priority_result[Silian_new_priority] = [Silian_p]
                else:
                    Silian_new_priority_result[Silian_new_priority].append(Silian_p)

            # 取最高优先级的第一个匹配
            Silian_max_ = max(Silian_new_priority_result.keys())
            return Silian_new_priority_result[Silian_max_][0]

        return Silian_priority_result[Silian_max_][0]

    # ========== 步骤 8: 返回结果或异常 ==========
    if Silian_len_filtered_result == 0:
        # 没有任何模板能匹配给定的参数
        raise InvalidCommandFormatError

    # 返回唯一的有效匹配
    return Silian_filtered_result[0]
