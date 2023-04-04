import sys

import extractors

router = {
    'deduplicate': extractors.DeduplicateExtractor,
    'localcomm': extractors.LocalCommunityExtractor,
    'merge': extractors.MergeExtractor,
}

if __name__ == '__main__':
    argv = sys.argv
    assert len(argv) > 2
    cmd = sys.argv[1]
    sys.argv.remove(cmd)

    cls = router.get(cmd)
    if cls is not None:
        cls().extract()
