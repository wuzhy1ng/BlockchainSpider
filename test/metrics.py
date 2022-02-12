import argparse
import csv
import json
import os

import networkx as nx


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


def calc_depth(g: nx.Graph, source) -> int:
    K = nx.single_source_shortest_path_length(g, source)
    K = list(K.items())
    K.sort(key=lambda x: x[1], reverse=True)
    return K[0][1] if len(K) > 0 else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.description = 'calculate the metrics of cases'
    parser.add_argument(
        '-i', '--input',
        help='input data folder(str)',
        dest='in_dir',
        type=str,
        default=None
    )
    args = parser.parse_args()
    assert args.in_dir is not None

    cases = list()
    cases_path = './cases'
    for fn in os.listdir(cases_path):
        fn = os.path.join(cases_path, fn)
        with open(fn, 'r') as f:
            case = json.load(f)
            cases.append(case)

    avg_metrics = dict(
        recall=0,
        size=0,
        depth=0
    )
    for case in cases:
        source = case['source'][0]['address']
        targets = [item['address'] for item in case['target']]

        fn = os.path.join(args.in_dir, '%s.csv' % source)
        if not os.path.exists(fn):
            print('warning: %s does not existed' % fn)
            continue
        print('processing:', source, end=' ')

        g = load_graph_from_csv(fn)
        g.add_node(source)
        recall = calc_recall(g, targets)
        size = calc_size(g)
        depth = calc_depth(g, source)

        avg_metrics['recall'] += recall
        avg_metrics['size'] += size
        avg_metrics['depth'] += depth

        print(dict(
            recall=recall,
            size=size,
            depth=depth,
            name=case.get('name')
        ))
    avg_metrics = {k: v / len(cases) for k, v in avg_metrics.items()}
    print('average metrics:', avg_metrics)
