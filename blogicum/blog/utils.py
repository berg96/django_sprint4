from datetime import datetime


def published(cls):
    return cls.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=datetime.now(),
    )
