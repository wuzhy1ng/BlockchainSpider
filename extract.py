import argparse
import logging
import multiprocessing as mp
import os

import extractors


def main():
    parser = argparse.ArgumentParser()
    parser.description = 'Extract raw data'
    parser.add_argument('-i', '--input', help='input raw data folder', dest='in_dir', type=str, default=None)
    parser.add_argument('-o', '--output', help='output data folder', dest='out_dir', type=str, default=None)
    parser.add_argument('-e', '--extractor', help='extractor for extraction', dest='extractor', type=str, default=None)

    args = parser.parse_args()
    if args.in_dir is None or args.out_dir is None:
        logging.error('lost arguments')
        return

    if not os.path.exists(args.in_dir):
        logging.error('input folder does not existed ')
        return

    if not os.path.exists(args.out_dir):
        os.mkdir(args.out_dir)

    if getattr(extractors, args.extractor) is None:
        logging.error('this extractor does not existed')
        return

    pool = mp.Pool(mp.cpu_count())
    for fn in os.listdir(args.in_dir):
        if os.path.isdir(os.path.join(args.in_dir, fn)):
            continue
        source = fn.replace('.csv', '')
        extractor_cls = getattr(extractors, args.extractor)
        ext = extractor_cls()
        pool.apply_async(ext, kwds=dict(
            in_dir=args.in_dir,
            out_dir=args.out_dir,
            source=source,
            fn=fn,
        ))
    pool.close()
    pool.join()


if __name__ == '__main__':
    main()
