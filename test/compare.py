import argparse
import json
import os
import time

parameters = {
    'bfs': {
        'core': 'bfs',
        'depth': 2,
    },
    'poison': {
        'core': 'poison',
        'depth': 2,
    },
    'haircut': {
        'core': 'haircut',
        'min_weight': 1e-3,
    },
    'appr': {
        'core': 'appr',
        'epsilon': 1e-3,
        'alpha': 0.15
    },
    'ttr': {
        'core': 'ttr',
        'strategy': 'TTRRedirect',
        'epsilon': 1e-3,
        'alpha': 0.15,
        'beta': 0.7,
    },
    'ttr_time': {
        'core': 'ttr',
        'strategy': 'TTRTime',
        'epsilon': 1e-3,
        'alpha': 0.15,
        'beta': 0.7,
    }
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.description = 'compare test on cases'
    parser.add_argument(
        '-o', '--output',
        help='output data folder(str)',
        dest='out_dir',
        type=str,
        default=None
    )
    parser.add_argument(
        '-m', '--method',
        help='method for tracing',
        dest='method',
        type=str,
        default=None
    )
    args = parser.parse_args()
    assert args.out_dir is not None
    assert args.method is not None
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)

    # load cases
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

    # load parameters
    params = parameters[args.method]
    core = params['core']
    del params['core']

    # start task for crawling raw data
    start = time.time()
    not_token_core = {'haircut', 'appr', 'ttr_base', 'ttr_weight', 'ttr_time'}
    for net, cases in net_cases.items():
        infos = list()
        for case in cases:
            infos.append({
                'source': case['source'][0]['address'],
                'types': 'external,internal,erc20' if core not in not_token_core else 'external,internal',
                'start_blk': case['blockAt'],
                'out': os.path.join(args.out_dir, 'raw'),
                **params
            })
        with open('./tmp.json', 'w') as f:
            json.dump(infos, f)
        cmd = 'scrapy crawl txs.%s.%s -a file=./tmp.json' % (net, core)
        os.system(cmd)

    # save using time
    with open('./using_time', 'w') as f:
        f.write(str(time.time() - start))

    # deduplicate for raw data
    cmd = 'python extract.py deduplicate -i %s -o %s' % (
        os.path.join(args.out_dir, 'raw'),
        os.path.join(args.out_dir, 'deduplicated'),
    )
    os.system(cmd)

    # local community discovery
    phi = 1e-3
    localcomm_methods = {'appr', 'ttr_base', 'ttr_weight', 'ttr_time', 'ttr_aggregate'}
    if args.method in localcomm_methods:
        cmd = 'python extract.py localcomm -i %s -o %s' % (
            os.path.join(args.out_dir, 'deduplicated'),
            os.path.join(args.out_dir, 'localcomm'),
        )
