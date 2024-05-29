from .enginefacade import _AbstractTransactionFactory
import asyncio
from oslo_db import exception
from oslo_db import options
from oslo_db.sqlalchemy import engines
from oslo_db.sqlalchemy import orm
from oslo_db import warning
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

class _AsyncioTransactionFactory(_AbstractTransactionFactory):
    """A factory for :class:`._AsyncioTransactionContext` objects.

    By default, there is just one of these, set up
    based on CONF, however instance-level :class:`._TransactionFactory`
    objects can be made, as is the case with the
    :class:`._TestTransactionFactory` subclass used by the oslo.db test suite.
    """

    _start_lock: asyncio.Lock

    _writer_engine: AsyncEngine
    _reader_engine: AsyncEngine

    def _make_lock(self):
        return asyncio.Lock()

    if TYPE_CHECKING:
        def get_writer_engine(self) -> AsyncEngine:
            """Return the writer engine for this factory.

            Implies start.
            """
            ...

        def get_reader_engine(self) -> AsyncEngine:
            """Return the reader engine for this factory.

            Implies start.
            """
            ...

        def get_writer_maker(self) -> async_sessionmaker:
            """Return the writer sessionmaker for this factory.

            Implies start.
            """
            ...

        def get_reader_maker(self) -> async_sessionmaker:
            """Return the reader sessionmaker for this factory.

            Implies start.
            """
            ...

    async def dispose_pool(self):
        """Call engine.pool.dispose() on underlying AsyncEngine objects."""
        async with self._start_lock:
            if not self._started:
                return

            self._writer_engine.pool.dispose()
            if self._reader_engine is not self._writer_engine:
                self._reader_engine.pool.dispose()

    def _setup_for_connection(
        self, sql_connection, engine_kwargs, maker_kwargs,
    ):
        if sql_connection is None:
            raise exception.CantStartEngineError(
                "No sql_connection parameter is established")
        engine = engines.create_engine(
            sql_connection=sql_connection, **engine_kwargs)
        for hook in self._facade_cfg['on_engine_create']:
            hook(engine)
        sessionmaker = orm.get_maker(engine=engine, **maker_kwargs)
        return engine, sessionmaker
