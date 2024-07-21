import re

def lexer(input):
	token_specification = [
		('DIV', r'div:'),
		('STYLE', r'style:'),
		('HEADER', r'header:'),
		('TEXT', r'text='),
		('TEXT_CONTENT', r'[^:\n]+'),  # Matches text content including spaces
		('IDENT', r'[a-zA-Z_][a-zA-Z0-9_]*'),  # Matches identifiers
		('WHITESPACE', r'\s+'),                # Skips whitespace
		('NEWLINE', r'\n'),                    # Skips newlines
		('COLON', r':'),                       # Matches colons
		('UNKNOWN', r'.'),                     # Catches any unexpected characters
	]

	token_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)
	tokens = []
	for mo in re.finditer(token_regex, input):
		kind = mo.lastgroup
		value = mo.group().strip()
		if kind in {'WHITESPACE', 'NEWLINE'}:
			continue
		elif kind == 'UNKNOWN':
			raise RuntimeError(f'Unexpected token: {value}')
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
		node = ASTNode('BLOCK')
		while index < len(tokens):
			kind, value = tokens[index]
			if kind == 'DIV':
				div_node, index = parse_div(index + 1)
				node.add_child(div_node)
			elif kind == 'STYLE':
				style_node, index = parse_style(index + 1)
				node.add_child(style_node)
			elif kind == 'HEADER':
				header_node, index = parse_header(index + 1)
				node.add_child(header_node)
			elif kind == 'TEXT':
				text_node, index = parse_text(index + 1)
				node.add_child(text_node)
			else:
				break
		return node, index

	def parse_div(index):
		node = ASTNode('DIV')
		while index < len(tokens):
			kind, value = tokens[index]
			if kind == 'STYLE':
				style_node, index = parse_style(index + 1)
				node.add_child(style_node)
			elif kind == 'HEADER':
				header_node, index = parse_header(index + 1)
				node.add_child(header_node)
			elif kind == 'TEXT' or kind == 'DIV':
				break
			else:
				index += 1
		return node, index

	def parse_style(index):
		node = ASTNode('STYLE')
		while index < len(tokens):
			kind, value = tokens[index]
			if kind == 'TEXT_CONTENT':
				style_node = ASTNode('STYLE_ITEM', value)
				node.add_child(style_node)
				index += 1
			else:
				break
		return node, index

	def parse_header(index):
		node = ASTNode('HEADER')
		while index < len(tokens):
			kind, value = tokens[index]
			if kind == 'TEXT':
				text_node, index = parse_text(index + 1)
				node.add_child(text_node)
			else:
				break
		return node, index

	def parse_text(index):
		kind, value = tokens[index]
		if kind == 'TEXT_CONTENT':
			node = ASTNode('TEXT', value)
			return node, index + 1
		else:
			raise RuntimeError(f'Unexpected token: {tokens[index]}')

	ast, _ = parse_block(0)
	return ast

def compile_to_html(ast):
	def compile_node(node):
		if node.type == 'BLOCK':
			return ''.join(compile_node(child) for child in node.children)
		elif node.type == 'DIV':
			styles = ""
			for child in node.children:
				if child.type == 'STYLE':
					compiled_styles = compile_styles(child)
					if compiled_styles is not None:
						styles += compiled_styles
				elif child.type == 'BLOCK':
					for child2 in child.children:
						compiled_styles = compile_styles(child2)
						if compiled_styles is not None:
							styles += compiled_styles

			#styles = ''.join(compile_styles(child) for child in node.children if child.type == 'STYLE')
			content = ''.join(compile_node(child) for child in node.children if child.type != 'STYLE')
			return f'<div style="{styles}">{content}</div>'
		elif node.type == 'STYLE':
			return ''  # Styles are handled at the DIV level
		elif node.type == 'STYLE_ITEM':
			styles = {
				'flex': 'display: flex;',
				'column': 'flex-direction: column;',
				'center': 'align-items: center; justify-content: center;',
			}
			return styles.get(node.value, '')
		elif node.type == 'HEADER':
			content = ''.join(compile_node(child) for child in node.children)
			return f'<header>{content}</header>'
		elif node.type == 'TEXT':
			return node.value
		else:
			raise RuntimeError(f'Unknown AST node type: {node.type}')

	def compile_styles(node):
		if node.type == 'STYLE':
			return ''.join(compile_node(child) for child in node.children)


	return compile_node(ast)

def main():
	input_code = """
	div:
		style:
			flex
			column
			center
		header:
			text=hey man
	"""
	tokens = lexer(input_code)
	ast = parser(tokens)
	html = compile_to_html(ast)
	print(html)

if __name__ == '__main__':
	main()
