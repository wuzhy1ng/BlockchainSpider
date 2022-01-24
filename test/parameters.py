import argparse
import csv
import json
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.description = 'parameters test of ttr'
    parser.add_argument(
        '-o', '--output',
        help='output data folder(str)',
        dest='out_dir',
        type=str,
        default='./data/test/parameters'
    )

    args = parser.parse_args()
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)

    cases_path = './test/cases'
    cases = list()
    for fn in os.listdir(cases_path):
        fn = os.path.join(cases_path, fn)
        with open(fn, 'r') as f:
            case = json.load(f)
            cases.append(case)

    epsilons = [0.1, 0.05, 0.01, 0.005, 0.001]
    epsilons.reverse()
    for epsilon in epsilons:
        for case in cases:
            cmd = [
                'scrapy crawl txs.%s.ttr' % case['net'],
                '-a source=%s' % case['source'][0]['address'],
                '-a out=%s' % os.path.join(args.out_dir, 'epsilon_%s' % str(epsilon)),
                '-a epsilon=%f' % epsilon,
                '-a types=external,internal,erc20',
            ]
            os.system(' '.join(cmd))
