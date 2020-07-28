#!/usr/bin/env python3
"""
Generate an index.html and recipe.html files for each recipe in the ./SITE_DIR/
directory.
"""

import glob
import os
import re
import shutil
import subprocess
from datetime import datetime

import pytz
from pyrfc3339 import generate

SITE_DIR = "public"


def get_recipe_data():
    """glob the recipe dir and return the data"""

    def shortname(name):
        return os.path.splitext(os.path.split(name)[1])[0]

    mdfiles = [(shortname(x), x) for x in sorted(glob.glob("./recipes/*.md"))]
    for index, mdfile in enumerate(mdfiles):
        with open(mdfile[1], "r") as mdfileio:
            line = mdfileio.readline()
            match = re.match(r"# ([^\w]+?) .*", line.strip())
            if match:
                emoji = match.group(1)
            else:
                # fallback emoji
                emoji = "📃"
            mdfiles[index] = (emoji, mdfile[0], mdfile[1])
    return mdfiles


def get_index_lines(recipe_data):
    """get the index entries"""
    index_entry_template = "- [{} {}]({})"
    index_entries = "\n".join(
        [index_entry_template.format(x[0], x[1], x[1] + ".html") for x in recipe_data]
    )
    return index_entries


INDEX_FORMAT = """# 🌮 recipes

{}
"""


def generate_index(recipe_data, outfile_name):
    """generate the index file"""
    # make the entries
    index_entries = get_index_lines(recipe_data)

    data = INDEX_FORMAT.format(index_entries)
    with open(outfile_name, "w") as outfile:
        outfile.write(data)


def generate_site():
    """output the site files"""
    shutil.rmtree(f"./{SITE_DIR}", ignore_errors=True)
    os.makedirs(f"./{SITE_DIR}", exist_ok=True)
    shutil.copytree("./recipes", f"./{SITE_DIR}/recipes")
    shutil.copy("./gh-fork-ribbon.css", f"./{SITE_DIR}/gh-fork-ribbon.css")

    # list of tuples of recipe info
    recipe_data = get_recipe_data()

    # gimme that sweet rfc3339 plz
    rfc3339_now_str = generate(datetime.utcnow().replace(tzinfo=pytz.utc))

    # index
    generate_index(recipe_data, f"./{SITE_DIR}/README.md")
    recipe_data = recipe_data + [
        ("🌮", "index", "README.md"),
    ]

    cmdline = (
        'yasha -o {site_dir}/{name}.html --shortname="{name}" '
        '--favicon="{emoji}" --pathname="{path}" '
        '--timestamp="{rfc3339_now_str}" --isindex={isindex} recipe-template.html.j2'
    )

    # gnu parallel <_<
    cmdlines = "\n".join(
        [
            cmdline.format(
                site_dir=SITE_DIR,
                emoji=emoji,
                name=name,
                path=path,
                rfc3339_now_str=rfc3339_now_str,
                isindex=(name == "index"),
            )
            for emoji, name, path in recipe_data
        ]
    )

    subprocess.check_call(f"parallel -I% % <<EOF\n{cmdlines}\nEOF", shell=True)


if __name__ == "__main__":
    generate_site()
