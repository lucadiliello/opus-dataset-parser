import argparse
import os
import csv
import xml.etree.ElementTree as etree
import utils
from tqdm import tqdm

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    # Global level parameters
    parser.add_argument('-i', '--input_corpora_files', type=str, required=True, nargs='+',
                        help="Input folder as txt files")
    # get NameSpace of paramters
    args = parser.parse_args()

    all_files = dict()

    for corpora_file in tqdm(args.input_corpora_files, desc="Reading files"):
        if not corpora_file.startswith("."):
            filename = os.path.basename(corpora_file)
            print(f"Reading file {filename}")
            res = [sentence.strip() for _id, sentence in utils.parse_corpora(corpora_file)]
            print("Sentences extracted, transforming in set")
            all_files[filename] = set(res)

    print("Statistics")
    print("\nSentences lenght:")
    for k, v in all_files.items():
        print(f"File {k} has {len(v)} sentences")

    for k_1, v_1 in all_files.items():
        for k_2, v_2 in all_files.items():
            if k_1 != k_2:
                print(f"Files {k_1} and {k_2} have {len(v_1.intersection(v_2))} sentences in common")