import argparse
import csv
import json
import os
import networkx as nx

from matplotlib import pyplot as plt


def load_graph_from_csv(fn: str) -> nx.Graph:
    g = nx.Graph()

    with open(fn, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            item = {headers[i]: row[i] for i in range(len(row))}
            g.add_edge(item.get('from'), item.get('to'))

    return g


def calc_recall(g: nx.Graph, targets: list) -> float:
    assert len(targets) > 0

    # upbit savior related to all target nodes of upbit hacker, which must be masked
    upbit_saviors = [
        '0x83053c32b7819f420dcfed2d218335fe430fe3b5',
        '0x4f16bf5d775eb08f8792f38aca8898abd2be7603'
    ]
    for savior in upbit_saviors:
        if g.has_node(savior):
            g.remove_node(savior)

    target_cnt = 0
    for target in targets:
        if g.has_node(target):
            target_cnt += 1

    return target_cnt / len(targets)


def calc_size(g: nx.Graph) -> int:
    return g.number_of_nodes()


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
        '-x', '--xdata',
        help='xdata for plot',
        dest='x',
        type=str,
        default=None
    )
    args = parser.parse_args()
    assert args.in_dirs is not None
    assert args.x is not None

    cases = list()
    cases_path = './cases'
    for fn in os.listdir(cases_path):
        fn = os.path.join(cases_path, fn)
        with open(fn, 'r') as f:
            case = json.load(f)
            cases.append(case)

    recalls, sizes = list(), list()
    epsilons = [x for x in args.x.split(',')]
    for in_dir in args.in_dirs.split(','):
        avg_metrics = dict(
            recall=0,
            size=0,
        )
        for case in cases:
            source = case['source'][0]['address']
            targets = [item['address'] for item in case['target']]

            fn = os.path.join(in_dir, '%s.csv' % source)
            if not os.path.exists(fn):
                print('warning: %s does not existed' % fn)
                continue
            print('processing:', fn)

            g = load_graph_from_csv(fn)
            g.add_node(source)
            recall = calc_recall(g, targets)
            size = calc_size(g)

            avg_metrics['recall'] += recall
            avg_metrics['size'] += size

        avg_metrics = {k: v / len(cases) for k, v in avg_metrics.items()}
        recalls.append(avg_metrics.get('recall', 0))
        sizes.append(avg_metrics.get('size', 0))

    fig = plt.figure()
    ax = fig.add_subplot(111)
    lns2 = ax.plot(epsilons, recalls, '-r', label='Recall', marker='v', linewidth=3.0, markersize=13)
    ax2 = ax.twinx()
    lns3 = ax2.plot(epsilons, sizes, '--', label='Nodes', marker='v', linewidth=3.0, markersize=13)

    lns = lns2 + lns3
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, prop={'size': 16})
    ax.grid()
    ax.set_xlabel("Epsilon", fontsize=20)
    ax.set_ylabel(r"Recall", fontsize=20)
    ax.tick_params(labelsize=16)
    ax2.set_ylabel(r"Number of nodes", fontsize=20)
    ax2.tick_params(labelsize=16)
    plt.tight_layout()
    plt.show()
