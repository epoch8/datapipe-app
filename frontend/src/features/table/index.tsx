import React, { useCallback, useEffect, useState, useRef, SetStateAction, Dispatch, RefObject, FC } from 'react';
import { Button, Table as AntTable, TablePaginationConfig, Input, Space, InputRef } from 'antd'
import { ColumnsType } from 'antd/lib/table';
import ReactJson from 'react-json-view';
import { PipeTable, GetDataReq } from '../../types';
import { FilterValue } from 'antd/lib/table/interface';

interface Options {
  total: number;
  page: number;
  pageSize: number;
}

interface FocusType {
  table_name: string;
  key: string;
  indexes: {
    [name: string]: string | number;
  }
}


interface TableLoadingOptions {
  page?: number;
  pageSize?: number;
  overFocus?: FocusType | null;
  filters?: Record<string, FilterValue | null>;
}

interface Pagination {
  page: number;
  pageSize: number;
}

interface TableState {
  pagination: Pagination;
  focus?: FocusType;
  filter: Record<string, FilterValue | null>
}

interface FilterDropDownComponentProps {
  searchInput: RefObject<InputRef>;
  column: string;
  selectedKeys: any;
  colValue: any;
  setSelectedKeys: (keys: any) => void;
  confirm: any,
  clearFilters: any,
};

const FilterDropDownComponent: FC<FilterDropDownComponentProps> = (
  {
    searchInput,
    column, 
    selectedKeys, 
    colValue,
    setSelectedKeys,
    confirm,
    clearFilters,
  }
) => {
  const handleReset = (clearFilters: () => void) => {
    clearFilters();
  };

  return (
    <div style={{padding: 8,}}>
      <Input
        ref={searchInput}
        placeholder={`Search ${column}`}
        value={selectedKeys[0]}
        onChange={
          (e) => {
            switch (typeof colValue) {
              case 'number':
                setSelectedKeys(e.target.value ? [e.target.value] : []) //TODO OnlyNumbers
                break
              case 'string':
                setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
          }
        }
        onPressEnter={() => confirm()}
        style={{
          marginBottom: 8,
          display: 'block',
        }}
      />
      <Space>
        <Button
          type="primary"
          onClick={() => confirm()}
          size="small"
          style={{
            width: 90,
          }}
        >
          Search
        </Button>
        <Button
          onClick={() => { clearFilters && handleReset(clearFilters); confirm(); }}
          size="small"
          style={{
            width: 90,
          }}
        >
          Reset
        </Button>
      </Space>
    </div>
  );
};


const loadTable = async (
  searchInput: RefObject<InputRef>,
  setLoading: Dispatch<SetStateAction<boolean>>,
  setData: Dispatch<SetStateAction<any>>,
  setColumns: Dispatch<SetStateAction<ColumnsType<any>>>,
  setOptions: Dispatch<SetStateAction<Options>>,
  current: PipeTable,
  options: Options,
  loadingsOptions?: TableLoadingOptions,
  tableFocus?: any
) => {
  loadingsOptions = loadingsOptions ?? {} as TableLoadingOptions;
  const page = loadingsOptions.page ?? 1;
  const pageSize = loadingsOptions.pageSize;
  const overFocus = loadingsOptions.overFocus;
  let data: any;

  setLoading(true);
  const _focus = overFocus === null ? null : overFocus ?? tableFocus;

  const postBody = {
    table: current.id,
    page: page - 1,
    page_size: pageSize || options.pageSize
  } as GetDataReq

  if (_focus && _focus.table_name !== current.id) {
    postBody.focus = {
      table_name: _focus.table_name,
      items_idx: Object.entries(_focus.indexes).map(([idx, v]) => {
        return { [idx]: v } as Record<string, string | number>; 
      })
    }
  } else {
    postBody.filters = {};
    const _filters = loadingsOptions.filters;
    if (_filters) {
      const respFilters = {} as { [key: string]: string | number }
      let flag = false;
      Object.entries(_filters).forEach(([tableName, vals]) => {
        if (vals && vals[0] && typeof (vals[0]) !== 'boolean') {
          respFilters[tableName] = vals[0] as string | number;
          flag = true;
        }
      })
      if (flag) {
        postBody.filters = respFilters;
      }
    }
  }

  try {
    let reqUrl: string;
    let body = postBody as any; //quickfix for different (table_name, table) field names
    if(current.type === 'transform') {
      reqUrl = process.env['REACT_APP_GET_METADATA_URL'] as string;
    }
    else if(postBody.focus) {
      reqUrl = process.env['REACT_APP_GET_FOCUS_TABLE_URL'] as string;
      body = postBody;
      body.table_name = body.table;
      body.table = undefined;
    } else {
      reqUrl = process.env['REACT_APP_GET_TABLE_URL'] as string;
    }
    const response = await fetch(`http://localhost:3001${reqUrl}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    })
    data = await response.json();
  }
  catch (er) {
    console.error(er);
  }
  if (!data?.data || data.data.length === 0) {
    setLoading(false);
    setData([]);
    return;
  }

  setColumns(Object.entries(data.data[0]).map(([column, colValue]) => {
    return {
      title: column,
      dataIndex: column,
      //Doesn't make much sense because it only sorts on one page
      sorter: typeof colValue !== 'object' && (
        (a, b) => {
          const v1 = a[column];
          const v2 = b[column];
          if (!v1 || !v2) return 0;
          return parseInt(v1) ? parseInt(v1) - parseInt(v2) :
            v1.localeCompare(v2)
        }),

      render: value => {
        if (value === null) {
          return value;
        }
        if (typeof value === 'object') {
          return <ReactJson
            name={false}
            collapsed
            enableClipboard={false}
            displayDataTypes={false}
            src={value} />
        }
        if (typeof value === 'boolean') {
          return value ? 'True' : 'False';
        }
        return value;
      },
      filterDropdown: typeof colValue !== 'object' && (({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => {
        return <FilterDropDownComponent 
          searchInput={searchInput}
          column={column}
          selectedKeys={selectedKeys}
          colValue={colValue}
          setSelectedKeys={setSelectedKeys}
          confirm={confirm}
          clearFilters={clearFilters}
        />
      }),
      filteredValue: loadingsOptions?.filters ? loadingsOptions.filters[column] : null, 
      onFilterDropdownOpenChange: (visible: any) => {
        if (visible) {
          setTimeout(() => (searchInput.current)?.select(), 100);
        }
      }
    }
  }))

  setData(data.data.map((element: any, index: number) => ({ ...element, index })));
  setLoading(false);
  setOptions({
    total: data.total,
    page: data.page + 1,
    pageSize: data.page_size,
  })
}


function Table({ current }: { current: PipeTable }) {
  const [columns, setColumns] = useState<ColumnsType<any>>([]);
  const [data, setData] = useState<any>();
  const [loading, setLoading] = useState(false);
  const [tableFocus, setTableFocus] = useState<FocusType>();
  const [options, setOptions] = useState<Options>({
    total: 0,
    page: 1,
    pageSize: 20,
  });
  const searchInput = useRef<InputRef>(null);
  const [pagination, setPagination] = useState<Pagination>({
    page: 1,
    pageSize: 20,
  });

  const [filteredInfo, setFilteredInfo] = useState<Record<string, FilterValue | null>>({});

  useEffect(() => {
    setFilteredInfo({});
    // setFocus(undefined);
    setPagination({
      page: 1,
      pageSize: 19
    });
  }, [current])


  const skipRenderFlag = useRef(true);

  useEffect(() => {
    if (skipRenderFlag.current) {
      skipRenderFlag.current = false;
      return;
    }
    loadTable(
      searchInput,
      setLoading,
      setData,
      setColumns,
      setOptions,
      current,
      options,
      {
        page: pagination.page,
        pageSize: pagination.pageSize,
        filters: filteredInfo
      },
    )
  }, [filteredInfo, tableFocus, pagination])

  const rowSelection = {
    onChange: (selectedRowKeys: React.Key[], selectedRows: any[]) => {
      const selected = selectedRows[0];
      const newFocus = {
        table_name: current.id,
        key: selectedRowKeys[0] as string,
        indexes: current.indexes.reduce((acc, index) => {
          acc[index] = selected[index];
          return acc;
        }, {} as FocusType['indexes'])
      }
      skipRenderFlag.current = true;
      setTableFocus(newFocus);
    },
  };

  const changeHandler = useCallback((newPagination: TablePaginationConfig, newFilters: Record<string, FilterValue | null>) => {

    if (newPagination.current && newPagination.pageSize) {
      setPagination({
        page: newPagination.current,
        pageSize: newPagination.pageSize
      });
    }
    setFilteredInfo(newFilters);

  }, [current, options, tableFocus]);

  const clearFocus = useCallback(() => {
    setTableFocus(undefined);
  }, [current, options, tableFocus])

  return <>
    <div style={{ height: tableFocus ? 60 : 1, opacity: tableFocus ? 1 : 0, transition: '.2s all ease-out', overflow: 'hidden' }}>
      <div style={{ color: 'red' }}>
        <strong>Focus mode</strong>
      </div>
      {tableFocus && <>
        table: <strong>{tableFocus?.table_name}&nbsp;</strong>
        indexes:&nbsp;
        {Object.entries(tableFocus?.indexes || []).map(([idx, v], index) => {
          return <span key={index}>
            <strong>{idx}</strong>=<strong>{v}</strong>&nbsp;
          </span>;
        })}
        &nbsp;<Button size="small" onClick={clearFocus}>Clear</Button>
      </>}
    </div>
    {(Object.values(filteredInfo).length > 0 && (!data || data.length === 0)) &&
      <Button onClick={() => {
        setFilteredInfo({});
      }}>Clear filters</Button>
    }
    <AntTable
      loading={loading}
      showHeader={!loading && data?.length > 0}
      onChange={changeHandler}
      rowKey={(record) => {
        const idx_string = current.indexes.reduce((acc, value) => {
          acc += value + '_' + record[value] + '_';
          return acc;
        }, '')
        return `${current.id}_${idx_string}`
      }}
      rowSelection={{
        type: 'radio',
        selectedRowKeys: tableFocus ? [tableFocus.key] : [],
        preserveSelectedRowKeys: true,
        ...rowSelection,
      }}
      size="small"
      pagination={{
        showSizeChanger: true,
        total: options.total,
        pageSize: options.pageSize,
        current: options.page,
        position: ["topRight"]
      }}
      style={{ width: '100%' }}
      columns={columns}
      dataSource={loading ? [] : data} />
  </>
}

export { Table };