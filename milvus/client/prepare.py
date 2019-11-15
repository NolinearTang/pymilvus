from .types import MetricType
from ..grpc_gen import milvus_pb2 as grpc_types
from ..grpc_gen import status_pb2
from .exceptions import ParamError
from .utils import check_pass_param, is_legal_array
from .abstract import Range


class Prepare:

    @classmethod
    def table_name(cls, table_name):

        check_pass_param(table_name=table_name)
        return grpc_types.TableName(table_name=table_name)

    @classmethod
    def table_schema(cls, param):
        """
        :type param: dict
        :param param: (Required)

            `example param={'table_name': 'name',
                            'dimension': 16,
                            'index_file_size': 1024
                            'metric_type': MetricType.L2
                            }`

        :return: ttypes.TableSchema object
        """
        if isinstance(param, grpc_types.TableSchema):
            return param

        if not isinstance(param, dict):
            raise ParamError('Param type incorrect, expect {} but get {} instead '.format(
                type(dict), type(param)
            ))

        if 'index_file_size' not in param:
            param['index_file_size'] = 1024
        if 'metric_type' not in param:
            param['metric_type'] = MetricType.L2

        _param = {
            'table_name': param['table_name'],
            'dimension': param['dimension'],
            'index_file_size': param['index_file_size'],
            'metric_type': param['metric_type']
        }

        check_pass_param(**_param)

        return grpc_types.TableSchema(status=status_pb2.Status(error_code=0, reason='Client'),
                                      table_name=_param["table_name"],
                                      dimension=_param["dimension"],
                                      index_file_size=_param["index_file_size"],
                                      metric_type=_param["metric_type"])

    @classmethod
    def range(cls, start_date, end_date):
        """
        Parser a 'yyyy-mm-dd' like str or date/datetime object to Range object

            `Range: (start_date, end_date]`

            `start_date : '2019-05-25'`

        :param start_date: start date
        :type  start_date: str, date, datetime
        :param end_date: end date
        :type  end_date: str, date, datetime

        :return: Range object
        """
        temp = Range(start_date, end_date)

        return grpc_types.Range(start_value=temp.start_date,
                                end_value=temp.end_date)

    @classmethod
    def ranges(cls, ranges):
        """
        prepare query_ranges

        :param ranges: prepare query_ranges
        :type  ranges: [[str, str], (str,str)], iterable

            `Example: [[start, end]], ((start, end), (start, end)), or
                    [(start, end)]`

        :return: list[Range]
        """
        res = []
        for _range in ranges:
            if not isinstance(_range, grpc_types.Range):
                res.append(Prepare.range(_range[0], _range[1]))
            else:
                res.append(_range)
        return res

    @classmethod
    def insert_param(cls, table_name, vectors, ids=None):

        check_pass_param(table_name=table_name)

        if ids is None:
            _param = grpc_types.InsertParam(table_name=table_name)
        else:
            check_pass_param(ids=ids)

            if len(vectors) != len(ids):
                raise ParamError("length of vectors do not match that of ids")

            _param = grpc_types.InsertParam(table_name=table_name, row_id_array=ids)

        for vector in vectors:
            if is_legal_array(vector):
                _param.row_record_array.add(vector_data=vector)
            else:
                raise ParamError('Vectors should be 2-dim array!')

        return _param

    @classmethod
    def index(cls, index_type, nlist):
        """

        :type index_type: IndexType
        :param index_type: index type

        :type  nlist:
        :param nlist:

        :return:
        """
        check_pass_param(index_type=index_type, nlist=nlist)

        return grpc_types.Index(index_type=index_type, nlist=nlist)

    @classmethod
    def index_param(cls, table_name, index_param):

        if not isinstance(index_param, dict):
            raise ParamError('Param type incorrect, expect {} but get {} instead '.format(
                type(dict), type(index_param)
            ))

        check_pass_param(table_name=table_name, **index_param)

        _index = Prepare.index(**index_param)

        return grpc_types.IndexParam(status=status_pb2.Status(error_code=0, reason='Client'),
                                     table_name=table_name,
                                     index=_index)

    @classmethod
    def search_param(cls, table_name, query_records, query_ranges, topk, nprobe):
        query_ranges = Prepare.ranges(query_ranges) if query_ranges else None

        check_pass_param(table_name=table_name, topk=topk, nprobe=nprobe)

        search_param = grpc_types.SearchParam(
            table_name=table_name,
            query_range_array=query_ranges,
            topk=topk,
            nprobe=nprobe
        )

        for vector in query_records:
            if is_legal_array(vector):
                search_param.query_record_array.add(vector_data=vector)
            else:
                raise ParamError('Vectors should be 2-dim array!')

        return search_param

    @classmethod
    def search_vector_in_files_param(cls, table_name, query_records,
                                     query_ranges, topk, nprobe, ids):
        _search_param = Prepare.search_param(table_name, query_records,
                                             query_ranges, topk, nprobe)

        return grpc_types.SearchInFilesParam(
            file_id_array=ids,
            search_param=_search_param
        )

    @classmethod
    def cmd(cls, cmd):
        check_pass_param(cmd=cmd)

        return grpc_types.Command(cmd=cmd)

    @classmethod
    def delete_param(cls, table_name, start_date, end_date):

        range_ = Prepare.range(start_date, end_date)

        check_pass_param(table_name=table_name)

        return grpc_types.DeleteByRangeParam(range=range_, table_name=table_name)