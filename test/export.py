import argparse
import csv
import json
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.description = 'export cases info'
    parser.add_argument(
        '-o', '--output',
        help='output data folder(str)',
        dest='out_dir',
        type=str,
        default=None,
    )
    args = parser.parse_args()
    assert args.out_dir is not None

    cases = list()
    cases_path = './cases'
    for fn in os.listdir(cases_path):
        fn = os.path.join(cases_path, fn)
        with open(fn, 'r') as f:
            case = json.load(f)
            cases.append(case)

    net_cases = dict()
    for case in cases:
        net = case.get('net')
        if net_cases.get(net) is None:
            net_cases[net] = list()
        net_cases[net].append(case)

    for net, cases in net_cases.items():
        fn = os.path.join(args.out_dir, '%s.csv' % net)
        with open(fn, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'source', 'types', 'start_blk', 'out',
                'name'
            ])
            for case in cases:
                writer.writerow([
                    case['source'][0]['address'],
                    'external|internal|erc20',
                    case['blockAt'],
                    '',
                    case['name']
                ])
