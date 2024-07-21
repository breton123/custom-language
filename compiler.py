import re


def lexer(input):
    token_specification = [
        ("DIV", r"div:"),
        ("HEAD", r"head:"),
        ("TITLE", r"title="),
        ("SCRIPT", r"script:"),
        ("BODY", r"body:"),
        ("CLASS", r"class="),
        ("LINK", r"link:"),
        ("META", r"meta:"),
        ("STYLE", r"style:"),
        ("HEADER", r"header:"),
        ("TEXT", r"text="),
        ("PLACEHOLDER", r"placeholder="),
        ("INPUT", r"input:"),
        ("TEXT_CONTENT", r"[^:\n]+"),  # Matches text content including spaces
        ("IDENT", r"[a-zA-Z_][a-zA-Z0-9_]*"),  # Matches identifiers
        ("WHITESPACE", r"\s+"),  # Skips whitespace
        ("NEWLINE", r"\n"),  # Skips newlines
        ("COLON", r":"),  # Matches colons
        ("UNKNOWN", r"."),  # Catches any unexpected characters
    ]

    token_regex = "|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in token_specification)
    tokens = []
    for mo in re.finditer(token_regex, input):
        kind = mo.lastgroup
        value = mo.group().strip()
        if kind in {"WHITESPACE", "NEWLINE"}:
            continue
        elif kind == "UNKNOWN":
            raise RuntimeError(f"Unexpected token: {value}")
        tokens.append((kind, value))
    return tokens


class ASTNode:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
        self.children = []

    def add_child(self, child):
        self.children.append(child)


def parser(tokens):
    def parse_block(index):
        node = ASTNode("BLOCK")
        while index < len(tokens):
            kind, value = tokens[index]
            if kind == "DIV":
                div_node, index = parse_div(index + 1)
                node.add_child(div_node)
            elif kind == "HEADER":
                header_node, index = parse_header(index + 1)
                node.add_child(header_node)
            elif kind == "INPUT":
                input_node, index = parse_input(index + 1)
                node.add_child(input_node)
            else:
                break
        return node, index

    def parse_div(index):
        node = ASTNode("DIV")
        while index < len(tokens):
            kind, value = tokens[index]
            if kind == "STYLE":
                style_node, index = parse_style(index + 1)
                node.add_child(style_node)
            elif kind == "HEADER":
                header_node, index = parse_header(index + 1)
                node.add_child(header_node)
            elif kind == "INPUT":
                input_node, index = parse_input(index + 1)
                node.add_child(input_node)
            elif kind == "DIV":
                div_node, index = parse_div(index + 1)
                node.add_child(div_node)
            elif kind == "CLASS":
                placeholder_node, index = parse_setting(index + 1, "CLASS")
                node.add_child(placeholder_node)
            elif kind == "TEXT" or kind == "PLACEHOLDER":
                break
            else:
                index += 1
        return node, index
   
    def parse_input(index):
        node = ASTNode("INPUT")
        while index < len(tokens):
            kind, value = tokens[index]
            if kind == "TEXT":
                text_node, index = parse_setting(index + 1, "TEXT")
                node.add_child(text_node)
            elif kind == "PLACEHOLDER":
                placeholder_node, index = parse_setting(index + 1, "PLACEHOLDER")
                node.add_child(placeholder_node)
            elif kind == "STYLE":
                style_node, index = parse_style(index + 1)
                node.add_child(style_node)
            elif kind == "CLASS":
                placeholder_node, index = parse_setting(index + 1, "CLASS")
                node.add_child(placeholder_node)
            else:
                break
        return node, index

    def parse_style(index):
        node = ASTNode("STYLE")
        while index < len(tokens):
            kind, value = tokens[index]
            if kind == "TEXT_CONTENT":
                style_node = ASTNode("STYLE_ITEM", value)
                node.add_child(style_node)
                index += 1
            else:
                break
        return node, index

    def parse_header(index):
        node = ASTNode("HEADER")
        while index < len(tokens):
            kind, value = tokens[index]
            if kind == "TEXT":
                text_node, index = parse_setting(index + 1, "TEXT")
                node.add_child(text_node)
            elif kind == "STYLE":
                style_node, index = parse_style(index + 1)
                node.add_child(style_node)
            elif kind == "CLASS":
                placeholder_node, index = parse_setting(index + 1, "CLASS")
                node.add_child(placeholder_node)
            else:
                break
        return node, index

    def parse_setting(index, type):
        kind, value = tokens[index]
        if kind == "TEXT_CONTENT":
            node = ASTNode(type, value)
            return node, index + 1
        else:
            raise RuntimeError(f"Unexpected token: {tokens[index]}")


    ast, _ = parse_block(0)
    return ast


def compile_to_html(ast):
    def compile_node(node):
         
        if node.type == "BLOCK":
            return "".join(compile_node(child) for child in node.children)
       
        elif node.type == "DIV":
            styles = ''.join(compile_styles(child) for child in node.children if child.type == 'STYLE')
            content = "".join(
                compile_node(child) for child in node.children if child.type != "STYLE"
            )
            settings = "".join(compile_node(child) for child in node.children if child.type == "CLASS")
            return f'<div {settings} style="{styles}">{content}</div>'
       
        elif node.type == "STYLE":
            return ""  # Styles are handled at the DIV level
       
        elif node.type == "STYLE_ITEM":
            styles = {
                "flex": "display: flex;",
                "column": "flex-direction: column;",
                "center": "align-items: center; justify-content: center;",
            }
		
            return styles.get(node.value, "")
       
        elif node.type == "HEADER":
            styles = ''.join(compile_styles(child) for child in node.children if child.type == 'STYLE')
            content = "".join(compile_node(child) for child in node.children if child.type == 'TEXT')
            settings = "".join(compile_node(child) for child in node.children if child.type != "TEXT")
            return f'<header {settings} style="{styles}">{content}</header>'
       
        elif node.type == "INPUT":
             styles = ''.join(compile_styles(child) for child in node.children if child.type == 'STYLE')
             content = "".join(compile_node(child) for child in node.children if child.type == "TEXT")
             settings = "".join(compile_node(child) for child in node.children if child.type != "TEXT")
             return f'<input {settings} style="{styles}">{content}</input>'
        
        elif node.type == "TEXT":
            return node.value
       
        elif node.type == "PLACEHOLDER":
            return f'placeholder="{node.value}" '
        
        elif node.type == "CLASS":
            return f'class="{node.value}" '
        else:
            raise RuntimeError(f"Unknown AST node type: {node.type}")

    def compile_styles(node):
        if node.type == "STYLE":
            return "".join(compile_node(child) for child in node.children)
     

    return compile_node(ast)


def main():
    input_code = """
	div:
        class=mainDIV
		style:
			flex
			column
			center
		header:
			text=hey man
		input:
            class=main
			style:
				flex
			text=inputhere
			placeholder=yoo bro
	"""
    ## Assigns types to everything
    tokens = lexer(input_code)
    #print(tokens)
    ast = parser(tokens)
    html = compile_to_html(ast)
    print(html)


if __name__ == "__main__":
    main()
