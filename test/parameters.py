import argparse
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
        default=None
    )
    args = parser.parse_args()
    assert args.out_dir is not None
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)

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

    using_time = list()
    epsilons = [0.1, 0.05, 0.01, 0.005, 0.001, 0.0005, 0.0001, 0.00005]
    epsilons.reverse()
    for epsilon in epsilons:
        out_dir = os.path.join(args.out_dir, 'epsilon_%s' % str(epsilon))
        for net, cases in net_cases.items():
            infos = list()
            for case in cases:
                infos.append({
                    'source': case['source'][0]['address'],
                    'types': 'external,internal,erc20',
                    'start_blk': case['blockAt'],
                    'out': out_dir,
                    'epsilon': epsilon,
                    'alpha': 0.15,
                    'beta': 0.7
                })

            with open('./tmp.json', 'w') as f:
                json.dump(infos, f)
            cmd = 'scrapy crawl txs.%s.ttr -a file=./tmp.json' % net
            os.system(cmd)
