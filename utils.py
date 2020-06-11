import argparse
import os
import csv
import xml.etree.ElementTree as etree
from tqdm import tqdm

def _get_filename(path):
    """
    :path: path-like string
    :return: filename
    """
    return os.path.basename(path)

def _get_bare_filename(path):
    """
    :path: path-like string
    :return: filename w/o extensions (e.g. removes .xml.gz and not only .gz)
    """
    while '.' in path:
        path = os.path.splitext(os.path.basename(path))[0]
    return path

def _get_extensions(path):
    """
    :path: path-like string
    :return: list of extensions (e.g. returns .xml.gz and not only .gz)
    """
    ext = []
    while '.' in path:
        ext.append(os.path.splitext(os.path.basename(path))[1])
        path = os.path.splitext(os.path.basename(path))[0]
    return ''.join(reversed(ext))

def concat_generators(*args):
    for gen in args:
        yield from gen    

def add_to_dict(src, dest):
    for k, v in dest.items():
        if k in src:
            if isinstance(v, dict) == isinstance(src[k], dict):
                add_to_dict(src[k], v)
            else:
                assert not isinstance(v, dict) and not isinstance(src[k], dict), "Dicts has not same shape"
                assert src[k] == v
        else:
            src[k] = v

def parse_corpora_ids(input_file):
    """
    :input_file: input XML filename
    :return: generate pairs (id, sentence)
    """
    res = []
    for event, elem in etree.iterparse(input_file, events=('end', )):
        if event == 'end' and elem.tag == "s":
            # sentence = " ".join([token.text for token in elem.iter(tag='w')])
            res.append(int(elem.attrib["id"]))
            elem.clear()
    return res

def parse_corpora(input_file):
    """
    :input_file: input XML filename
    :return: generate dict: id -> sentence
    """
    res = dict()
    for event, elem in etree.iterparse(input_file, events=('end', )):
        if event == 'end' and elem.tag == "s":
            res[int(elem.attrib["id"])] = elem.text.strip()
            elem.clear()
    return res

def parse_alignment(input_file):
    """
    :input_file: input XML filename
    :return: dict with form
    {
        "fromDoc": {
            "toDoc": [
                ([14], [10, 11])
            ],
            ...
        },
        ...
    }
    """
    res = dict()
    for event, elem in tqdm(etree.iterparse(input_file, events=('start', 'end')), desc=f"Processing {input_file}"):
        if event == 'start' and elem.tag == "linkGrp":
            superElem = elem
            _from = superElem.attrib["fromDoc"] if superElem.attrib["fromDoc"].startswith("en/") else superElem.attrib["toDoc"]
            _dest = superElem.attrib["toDoc"] if superElem.attrib["fromDoc"].startswith("en/") else superElem.attrib["fromDoc"]

            assert _from.startswith("en/")
            assert not _dest.startswith("en/")

            if _from.endswith(".gz"):
                _from = _from[:-3]
            if _dest.endswith(".gz"):
                _dest = _dest[:-3]

            if not _from in res:
                res[_from] = dict()
            if not _dest in res[_from]:
                res[_from][_dest] = []

        elif event == 'end' and elem.tag == "link":
            first, second = elem.attrib["xtargets"].strip().split(";")
            if first and second:
                first = [int(x) for x in first.split(" ")]
                second = [int(x) for x in second.split(" ")]
                res[_from][_dest].append((first, second))
            elem.clear()

        elif event == 'end' and elem.tag == "linkGrp":
            superElem.clear()
            superElem = None

        elif event == 'end':
            elem.clear()

        else:
            pass
    return res

