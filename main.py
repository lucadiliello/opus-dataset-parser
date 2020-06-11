import argparse
import os
import csv
import xml.etree.ElementTree as etree
import utils
import random
import tqdm
import json

LANG_NUMBER = 24

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    # Global level parameters
    parser.add_argument('-i', '--input_corpora_folder', type=str, required=True,
                        help="Input folder as txt files. Structures must be like "
                             "input_corpora_folder/{en/it/de/...}/en-{en/it/de/...}.bicleaner07.XXXX.xml")
    parser.add_argument('-a', '--input_alignments_folder', type=str, required=False,
                        help='Input folder alignments as txt files')
    parser.add_argument('-o', '--output_file', type=str, required=False,
                        help='Output file as txt')
    parser.add_argument('-f', '--force_overwrite', action="store_true",
                        help='Overwrite already existing output file?')
    parser.add_argument('-p', '--consider_percentage', type=float, required=False, default=0.1,
                        help="Consider only sentences with at least the 10% of words with respect to language average sentence length")
    parser.add_argument('-l', '--limit', type=int, default=100000, required=False,
                        help="Limit output file length")
    parser.add_argument('-c', '--consider', type=int, default=LANG_NUMBER, required=False,
                        help="Consider only sentence with translation in at least X languages")
    parser.add_argument('-s', '--output_size', type=int, default=2, required=False,
                        help="Number of output sentences to group at a time")
    parser.add_argument('--lang_dict', type=str, required=True,
                        help="JSON dict with pairs language-id")

    # get NameSpace of paramters
    args = parser.parse_args()

    assert os.path.isdir(args.input_corpora_folder), f"{args.input_corpora_folder} is not a folder"
    assert os.path.isdir(args.input_alignments_folder), f"{args.input_alignments_folder} is not a folder"
    assert not os.path.isfile(args.output_file) or args.force_overwrite, f"{args.output_file} exists but it cannot be overwritten. Use -f option"
    assert os.path.isfile(args.lang_dict), f"{args.lang_dict} does not exist"
    assert args.output_size <= args.consider, f"Cannot create output sequences of sentence of length " \
        "{args.output_size} if considering sequences of length {args.consider}"

    res = dict()
    errors = 0
    with open(args.lang_dict, "r") as f:
        lang_dict = json.loads(f.read())

    for i, alignment_file in enumerate(os.listdir(args.input_alignments_folder)):
        if not alignment_file.startswith("."):
            filepath = os.path.join(args.input_alignments_folder, alignment_file)

            for event, elem in tqdm.tqdm(etree.iterparse(filepath, events=('start', 'end')), desc=f"Processing {alignment_file}"):
                if event == 'start' and elem.tag == "linkGrp":
                    superElem = elem
                    _from = superElem.attrib["fromDoc"] if superElem.attrib["fromDoc"].startswith("en/") else superElem.attrib["toDoc"]
                    _dest = superElem.attrib["toDoc"] if superElem.attrib["fromDoc"].startswith("en/") else superElem.attrib["fromDoc"]
      
                    assert _from.startswith("en/")
                    assert not _dest.startswith("en/")

                    _from_lang = _from[:2]
                    _dest_lang = _dest[:2]
                    assert _dest_lang != "en"

                    if _from.endswith(".gz"):
                        _from = _from[:-3]
                    if _dest.endswith(".gz"):
                        _dest = _dest[:-3]

                    if not _from in res:
                        res[_from] = dict()
                    if not _dest in res[_from]:
                        res[_from][_dest] = []

                    _from = utils.parse_corpora(os.path.join(args.input_corpora_folder, _from))
                    _dest = utils.parse_corpora(os.path.join(args.input_corpora_folder, _dest))

                elif event == 'end' and elem.tag == "link":
                    first, second = elem.attrib["xtargets"].strip().split(";")
                    if first and second:
                        first = [int(x) for x in first.split(" ")]
                        second = [int(x) for x in second.split(" ")]
                        
                        try:
                            sentence_a = " ".join([_from[x] for x in first])
                            sentence_b = " ".join([_dest[x] for x in second])

                            if sentence_a in res:
                                if not _dest_lang in res[sentence_a]:
                                    res[sentence_a][_dest_lang] = []
                                res[sentence_a][_dest_lang].append(sentence_b)
                            elif i <= (LANG_NUMBER - args.consider):
                                res[sentence_a] = {_dest_lang: [sentence_b]}
                            else:
                                pass

                        except:
                            errors += 1

                    elem.clear()

                elif event == 'end' and elem.tag == "linkGrp":
                    superElem.clear()
                    superElem = None

                    del _from
                    del _dest

                elif event == 'end':
                    elem.clear()

                else:
                    pass

            # clean from files entries that did not have all matches
            keys_to_delete = [k for k, v in res.items() if len(v) <= i - (LANG_NUMBER - args.consider)]
            for k in keys_to_delete:
                del res[k]

            print(f"Done alignment, actual size: {len(res)}")

    _id = 0
    with open(args.output_file, "w") as out:
        csv_writer = csv.writer(out, delimiter="\t", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        for k, v in res.items():
            choices = [(k, "en")] + [(random.choice(x), lang) for lang, x in v.items()]
            if args.output_size != -1:
                choices = random.sample(choices, k=args.output_size)

            for sentence, lang in choices:
                csv_writer.writerow([_id, lang_dict[lang], sentence])
            _id += 1

    print("Done!")