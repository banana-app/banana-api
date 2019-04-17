import multiprocessing as mp
from abc import ABC, abstractmethod

from rx.concurrency import ThreadPoolScheduler, GEventScheduler


class Runnable(ABC):

    @abstractmethod
    def run(self, scheduler):
        pass


class JobExecutor(ABC):

    @abstractmethod
    def submit(self, job: Runnable):
        pass


class JobContext(ABC):

    @abstractmethod
    def type(self) -> str:
        pass

    @abstractmethod
    def id(self) -> str:
        pass


class ThreadPoolJobExecutor(JobExecutor):

    _thread_pool_scheduler = ThreadPoolScheduler(max(mp.cpu_count() - 2, 2))

    def submit(self, job: Runnable):
        job.run(ThreadPoolJobExecutor._thread_pool_scheduler)


class AsyncIOJobExecutor(JobExecutor):

    _async_io_scheduler = GEventScheduler()

    def submit(self, job: Runnable):
        job.run(AsyncIOJobExecutor._async_io_scheduler)


class SimpleJobExecutor(JobExecutor):

    def submit(self, job: Runnable):
        job.run(scheduler=None)
