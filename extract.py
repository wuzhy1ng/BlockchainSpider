import argparse
import logging
import os
import shutil
import sys

import extractors

#
#
# def main():
#     parser = argparse.ArgumentParser()
#     parser.description = 'Extract raw data'
#     parser.add_argument('-i', '--input', help='input raw data folder(str)', dest='in_dir', type=str, default=None)
#     parser.add_argument('-o', '--output', help='output data folder(str)', dest='out_dir', type=str, default=None)
#     parser.add_argument('-e', '-extractor', help='extractor for extraction(str)', dest='extractor', type=str,
#                         default=None)
#     parser.add_argument('-p', '-parallel', help='parallel extraction(bool)', dest='parallel', type=bool, default=False)
#
#     args = parser.parse_args()
#     if args.in_dir is None or args.out_dir is None:
#         logging.error('lost arguments')
#         return
#
#     if not os.path.exists(args.in_dir):
#         logging.error('input folder does not existed ')
#         return
#
#     if not os.path.exists(args.out_dir):
#         os.mkdir(args.out_dir)
#
#     if getattr(extractors, args.extractor) is None:
#         logging.error('this extractor does not existed')
#         return
#
#     if args.parallel == True:
#         import multiprocessing as mp
#         pool = mp.Pool(mp.cpu_count())
#         for fn in os.listdir(args.in_dir):
#             if os.path.isdir(os.path.join(args.in_dir, fn)):
#                 shutil.copytree(
#                     src=os.path.join(args.in_dir, fn),
#                     dst=os.path.join(args.out_dir, fn)
#                 )
#                 continue
#             source = fn.replace('.csv', '')
#             extractor_cls = getattr(extractors, args.extractor)
#             ext = extractor_cls()
#             pool.apply_async(ext, kwds=dict(
#                 in_dir=args.in_dir,
#                 out_dir=args.out_dir,
#                 source=source,
#                 fn=fn,
#             ))
#         pool.close()
#         pool.join()
#     else:
#         for fn in os.listdir(args.in_dir):
#             if os.path.isdir(os.path.join(args.in_dir, fn)):
#                 shutil.copytree(
#                     src=os.path.join(args.in_dir, fn),
#                     dst=os.path.join(args.out_dir, fn)
#                 )
#                 continue
#
#             logging.info('processing of %s' % os.path.join(args.in_dir, fn))
#             source = fn.replace('.csv', '')
#             extractor_cls = getattr(extractors, args.extractor)
#             ext = extractor_cls()
#             ext(
#                 in_dir=args.in_dir,
#                 out_dir=args.out_dir,
#                 source=source,
#                 fn=fn
#             )
router = {
    'deduplicate': extractors.DeduplicateExtractor,
    'localcomm': extractors.LocalCommunityExtractor_
}

if __name__ == '__main__':
    # main()
    argv = sys.argv
    assert len(argv) > 2
    cmd = sys.argv[1]
    sys.argv.remove(cmd)

    cls = router.get(cmd)
    if cls is not None:
        cls().extract()
