import os

os.environ.setdefault("COHORT_OFFLINE", "true")  # tests never call the real API

import pytest

from app.retrieval.index import get_retriever
from app.survey import get_store
from app.tools import Toolbox


@pytest.fixture(scope="session")
def store():
    return get_store()


@pytest.fixture(scope="session")
def retriever():
    return get_retriever()


@pytest.fixture(scope="session")
def toolbox(retriever, store):
    return Toolbox(retriever, store)
