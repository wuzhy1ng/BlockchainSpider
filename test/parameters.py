import argparse
import csv
import json
import os
import time

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.description = 'parameters test of ttr on cases'
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

    cases = list()
    cases_path = './test/cases'
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

    using_time = list()
    epsilons = [0.1, 0.05, 0.01, 0.005, 0.001]
    epsilons.reverse()
    for epsilon in epsilons:
        start = time.time()

        for net, cases in net_cases.items():
            with open('./tmp.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'source', 'types', 'start_blk', 'out',
                    'epsilon', 'alpha', 'beta'
                ])
                for case in cases:
                    writer.writerow([
                        case['source'][0]['address'],
                        'external|internal|erc20',
                        case['blockAt'],
                        os.path.join(args.out_dir, 'epsilon_%s' % str(epsilon)),
                        epsilon,
                        0.15,
                        0.7
                    ])
            cmd = 'scrapy crawl txs.%s.ttr -a file=./tmp.csv' % net
            os.system(cmd)

    print([{'epsilon': epsilons[i], 'using time': using_time[i]} for i in range(len(epsilons))])
