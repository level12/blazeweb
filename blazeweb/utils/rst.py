try:
    from docutils.core import publish_parts
    have_docutils =  True
except ImportError:
    have_docutils = False

# see http://docutils.sourceforge.net/docs/user/config.html
default_rst_opts = {
    'no_generator': True,
    'no_source_link': True,
    'tab_width': 4,
    'stylesheet_path': None,
    'halt_level': 5,
    'doctitle_xform': False,
}

def rst2html(rst, opts=None):
    """
        Convert a reStructuredText string into a unicode HTML fragment.
    """
    if not have_docutils:
        raise ImportError('docutils library is required to use reStructuredText conversion')

    rst_opts = default_rst_opts.copy()
    if opts:
        rst_opts.update(opts)

    # apply options that should not be overridden
    rst_opts['raw_enabled'] = False
    rst_opts['traceback'] = True
    rst_opts['file_insertion_enabled'] = False

    return publish_parts(rst, writer_name='html', settings_overrides=rst_opts)['body']
