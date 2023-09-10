import logging


def log_debug_tracing(func):
    def wrapper(self, *args, **kwargs):
        func_name = '%s.%s' % (self.__class__.__name__, func.__name__)
        self.log(
            message='On {}, body {}, kwargs {}'.format(
                func_name, args[0].request.body, str(kwargs)
            ),
            level=logging.DEBUG
        )
        return func(self, *args, **kwargs)

    return wrapper
