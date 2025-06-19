from pathlib import Path
import sys

package = Path(__file__).parents[2].resolve().joinpath("src", "pchemdb")
sys.path.append(str(package))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.duration",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.imgconverter",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_click",
    "sphinx_copybutton",
    "sphinxcontrib.apidoc",
    "sphinxext.opengraph",
]
source_suffix = ".rst"
root_doc = "index"
project = "PChemDB"
version = release = "0.0.1"
author = "Ugochukwu Nwosu"
year = "2025"
copyright = f"{year}, {author}"
exclude_patterns = ["build"]
modindex_common_prefix = ["pchemdb."]
extlinks = {
    "issue": (
        "https://github.com/ugognw/pchemdb/-/issues/%s",
        "issue %s",
    ),
    "mr": (
        "https://github.com/ugognw/pchemdb/-/merge_requests/%s",
        "MR %s",
    ),
    "gitref": (
        "https://github.com/ugognw/pchemdb/-/commit/%s",
        "commit %s",
    ),
}

# -- Options for apidoc ------------------------------------------------------
apidoc_extra_args = ["-H", "Package Index 📖"]
apidoc_module_dir = "../../src/pchemdb"
apidoc_module_first = True
apidoc_output_dir = "reference"

# -- Options for sphinx.ext.autodoc ------------------------------------------
autoclass_content = "both"

# -- Options for sphinx.ext.intersphinx --------------------------------------
intersphinx_mapping = {
    "ase": ("https://wiki.fysik.dtu.dk/ase/", None),
    "matplotlib": ("https://matplotlib.org/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pymatgen": ("https://pymatgen.org/", None),
    "python": ("https://docs.python.org/3", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "pyEQL": ("https://pyeql.readthedocs.io/en/latest/index.html", None),
}

# -- Options for Napoleon ----------------------------------------------------
napoleon_google_docstring = True
napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_custom_sections = [("Keys", "Attributes")]
napoleon_use_admonition_for_examples = True

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]
html_last_updated_fmt = "%a, %d %b %Y %H:%M:%S"
html_theme_options = {
    "sidebar_hide_name": True,
    "source_repository": "https://github.com/ugognw/pchemdb/",
    "source_branch": "main",
    "source_directory": "docs/source",
    "light_logo": "pchemdb_light.png",
    "dark_logo": "pchemdb_dark.png",
    "light_css_variables": {
        "color-brand-primary": "#2A0226",
        "color-brand-content": "#AED1CB",
    },
}
pygments_style = "sphinx"
pygments_dark_style = "monokai"

gitlab_url = "https://github.com/ugognw/pchemdb"

smartquotes = True
html_split_index = False
html_short_title = f"{project}-{version}"


# -- Options for sphinx_copybutton -------------------------------------------
copybutton_exclude = ".linenos, .gp, .go"
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True
