from abc import ABC, abstractmethod

from rx.concurrency import ThreadPoolScheduler, AsyncIOScheduler, GEventScheduler
import multiprocessing as mp


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
    def type(self):
        pass

    @abstractmethod
    def id(self):
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
