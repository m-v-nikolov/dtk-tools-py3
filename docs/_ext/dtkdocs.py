"""
Sphinx plugins for Django documentation.
"""
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.domains.std import Cmdoption
from sphinx.util.compat import Directive
from sphinx.util.nodes import set_source_info


def setup(app):
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )

    app.add_description_unit(
        directivename="dtk-cmd",
        rolename="dtk-cmd",
        indextemplate="pair: %s; dtk-cmd command",
        parse_node=parse_dtk_cmd_node,
    )
    app.add_directive('dtk-cmd-option', Cmdoption)


    # register the snippet directive
    app.add_directive('snippet', SnippetWithFilename)
    # register a node for snippet directive so that the xml parser
    # knows how to handle the enter/exit parsing event
    app.add_node(snippet_with_filename,
                 html=(visit_snippet, depart_snippet_literal),
                 latex=(visit_snippet_latex, depart_snippet_latex),
                 man=(visit_snippet_literal, depart_snippet_literal),
                 text=(visit_snippet_literal, depart_snippet_literal),
                 texinfo=(visit_snippet_literal, depart_snippet_literal))
    return {'parallel_read_safe': True}


def parse_dtk_cmd_node(env, sig, signode):
    command = sig.split(' ')[0]
    env.ref_context['std:program'] = command
    title = "dtk %s" % sig
    signode += addnodes.desc_name(title, title)
    return command

class snippet_with_filename(nodes.literal_block):
    """
    Subclass the literal_block to override the visit/depart event handlers
    """
    pass


def visit_snippet_literal(self, node):
    """
    default literal block handler
    """
    self.visit_literal_block(node)


def depart_snippet_literal(self, node):
    """
    default literal block handler
    """
    self.depart_literal_block(node)


def visit_snippet(self, node):
    """
    HTML document generator visit handler
    """
    lang = self.highlightlang
    linenos = node.rawsource.count('\n') >= self.highlightlinenothreshold - 1
    fname = node['filename']
    highlight_args = node.get('highlight_args', {})
    if 'language' in node:
        # code-block directives
        lang = node['language']
        highlight_args['force'] = True
    if 'linenos' in node:
        linenos = node['linenos']

    def warner(msg):
        self.builder.warn(msg, (self.builder.current_docname, node.line))

    highlighted = self.highlighter.highlight_block(node.rawsource, lang,
                                                   warn=warner,
                                                   linenos=linenos,
                                                   **highlight_args)
    starttag = self.starttag(node, 'div', suffix='',
                             CLASS='highlight-%s' % lang)
    self.body.append(starttag)
    self.body.append('<div class="snippet-filename"><em>%s</em></div>\n''' % (fname,))
    self.body.append(highlighted)
    self.body.append('</div>\n')
    raise nodes.SkipNode


def visit_snippet_latex(self, node):
    """
    Latex document generator visit handler
    """
    code = node.rawsource.rstrip('\n')

    lang = self.hlsettingstack[-1][0]
    linenos = code.count('\n') >= self.hlsettingstack[-1][1] - 1
    fname = node['filename']
    highlight_args = node.get('highlight_args', {})
    if 'language' in node:
        # code-block directives
        lang = node['language']
        highlight_args['force'] = True
    if 'linenos' in node:
        linenos = node['linenos']

    def warner(msg):
        self.builder.warn(msg, (self.curfilestack[-1], node.line))

    hlcode = self.highlighter.highlight_block(code, lang, warn=warner,
                                              linenos=linenos,
                                              **highlight_args)

    self.body.append(
        '\n{\\colorbox[rgb]{0.9,0.9,0.9}'
        '{\\makebox[\\textwidth][l]'
        '{\\small\\texttt{%s}}}}\n' % (
            # Some filenames have '_', which is special in latex.
            fname.replace('_', r'\_'),
        )
    )

    if self.table:
        hlcode = hlcode.replace('\\begin{Verbatim}',
                                '\\begin{OriginalVerbatim}')
        self.table.has_problematic = True
        self.table.has_verbatim = True

    hlcode = hlcode.rstrip()[:-14]  # strip \end{Verbatim}
    hlcode = hlcode.rstrip() + '\n'
    self.body.append('\n' + hlcode + '\\end{%sVerbatim}\n' %
                     (self.table and 'Original' or ''))

    # Prevent rawsource from appearing in output a second time.
    raise nodes.SkipNode


def depart_snippet_latex(self, node):
    """
    Latex document generator depart handler.
    """
    pass


class SnippetWithFilename(Directive):
    """
    The 'snippet' directive that allows to add the filename (optional)
    of a code snippet in the document. This is modeled after CodeBlock.
    """
    has_content = True
    optional_arguments = 1
    option_spec = {'filename': directives.unchanged_required}

    def run(self):
        code = '\n'.join(self.content)

        literal = snippet_with_filename(code, code)
        if self.arguments:
            literal['language'] = self.arguments[0]
        literal['filename'] = self.options['filename']
        set_source_info(self, literal)
        return [literal]

