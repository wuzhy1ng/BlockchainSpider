import argparse
import csv
import json
import os

from matplotlib import pyplot as plt


def gen_linestyle():
    ls = ['-', '-.', '--', ':']
    i = 0
    while True:
        yield ls[i]
        i = (i + 1) % len(ls)


iter_linestyle = gen_linestyle()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.description = 'plot relation between the rank and recall'
    parser.add_argument(
        '-i', '--input',
        help='input data folders(str)',
        dest='in_dirs',
        type=str,
        default=None
    )
    parser.add_argument(
        '-l', '--legend',
        help='plot legend for each folders',
        dest='legends',
        type=str,
        default=None
    )
    parser.add_argument(
        '-k', '--topk',
        help='top k',
        dest='k',
        type=int,
        default=100
    )
    args = parser.parse_args()
    assert args.in_dirs is not None
    assert args.legends is not None
    paths = args.in_dirs.split(',')
    legends = args.legends.split(',')
    assert len(paths) == len(legends)

    cases = dict()
    cases_path = './cases'
    for fn in os.listdir(cases_path):
        fn = os.path.join(cases_path, fn)
        with open(fn, 'r') as f:
            case = json.load(f)
            cases[case['source'][0]['address']] = case

    ranks = dict()
    for i, path in enumerate(paths):
        ranks[legends[i]] = dict()
        for source in cases.keys():
            rank = list()
            fn = os.path.join(path, '%s.csv' % source)
            with open(fn, 'r') as f:
                reader = csv.reader(f)
                _ = next(reader)
                for row in reader:
                    rank.append(dict(
                        node=row[0],
                        rank=float(row[1])
                    ))
            rank.sort(key=lambda x: x['rank'], reverse=True)
            ranks[legends[i]][source] = rank

    targets = dict()
    for source, case in cases.items():
        _targets = [target['address'] for target in case['target']]
        targets[source] = set(_targets)

    legends = list()
    for legend, ranks in ranks.items():
        legends.append(legend)
        recalls = [0 for _ in range(args.k)]
        target_cnt = {source: 0 for source in cases.keys()}
        _recalls = {source: 0 for source in cases.keys()}
        for i in range(len(recalls)):
            for source, rank in ranks.items():
                if len(rank) <= i:
                    continue
                if rank[i]['node'] in targets[source]:
                    target_cnt[source] = target_cnt.get(source, 0) + 1
                _recalls[source] = target_cnt[source] / len(targets[source])
            recalls[i] = sum(_recalls.values()) / len(cases)
        plt.plot(recalls, linestyle=next(iter_linestyle), linewidth=3.0)

    plt.legend(legends, prop={'size': 16})
    plt.xlabel('Top N', fontsize=20)
    plt.ylabel('Average Recall', fontsize=20)
    plt.tick_params(labelsize=17)
    plt.grid()
    plt.tight_layout()
    plt.show()
