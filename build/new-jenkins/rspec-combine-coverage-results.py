#!/usr/bin/env python3

import json
import os
import glob

def fp(message):
    print(message, flush=True)

def main():
    results = {}
    for file in glob.glob('./**/.resultset.json', recursive=True):
        fp(f"copying results file: {file}")
        with open(file) as json_file:
            resultset = json.load(json_file)
        for process in resultset:
            node = file.split("/")[-2]
            key = f"{node}:{process}"
            fp(f" > found key: {key}")
            results[key] = resultset[process]
    for process in results:
        fp(process)
    with open('./coverage_nodes/.resultset.json', 'w') as results_file:
        json.dump(results, results_file)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        fp("")
