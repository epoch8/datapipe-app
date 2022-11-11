from typing import Tuple, Optional
from enum import Enum

from datapipe.datatable import DataTable
from datapipe.store.database import TableStoreDB
from sqlalchemy import func, or_, select
from termcolor import colored


class LintStatus(Enum):
    OK = "ok"
    SKIP = "skip"
    FAIL = "fail"


class Lint:
    desc: str

    def check(self, dt: DataTable) -> Tuple[LintStatus, Optional[str]]:
        query = self.check_query(dt)

        if query is None:
            print(colored("S", "grey"), end="")
            return (LintStatus.SKIP, None)

        (cnt,) = dt.meta_table.dbconn.con.execute(query).fetchone()

        if cnt == 0:
            return (LintStatus.OK, None)
        else:
            return (LintStatus.FAIL, f"{cnt} rows")

    def check_query(self, dt: DataTable):
        raise NotImplementedError

    def fix(self) -> None:
        pass


class LintDeleteTSIsNewerThanUpdateOrProcess(Lint):
    lint_id = "DTP001"
    desc = "delete_ts is newer than update_ts or process_ts"

    def check_query(self, dt: DataTable):
        meta_tbl = dt.meta_table.sql_table
        sql = (
            select(func.count())
            .select_from(meta_tbl)
            .where(
                or_(
                    meta_tbl.c.update_ts < meta_tbl.c.delete_ts,
                    meta_tbl.c.process_ts < meta_tbl.c.delete_ts,
                )
            )
        )

        return sql


# class LintDataWOMeta(Lint):
#     desc = "data has rows without meta"

#     def check_query(self, dt: DataTable):
#         if not isinstance(dt.table_store, TableStoreDB):
#             return None

#         meta_tbl = dt.meta_table.sql_table
#         data_tbl = dt.table_store.data_table

#         sql = select(func.cou)
