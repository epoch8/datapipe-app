import React, { useCallback, useEffect, useState } from 'react';
import { Button, Table as AntTable, TablePaginationConfig } from 'antd'
import { ColumnsType } from 'antd/lib/table';
import ReactJson from 'react-json-view';
import { PipeTable } from '../../types';

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

function Table({current}: { current: PipeTable }) {
  const [columns, setColumns] = useState<ColumnsType<any>>([]);
  const [data, setData] = useState<any>();
  const [loading, setLoading] = useState(false);
  const [focus, setFocus] = useState<FocusType>();
  const [options, setOptions] = useState<Options>({
    total: 0,
    page: 1,
    pageSize: 20,
  });

  async function loadTable(page = 1, pageSize?: number, overFocus?: FocusType | null) {
    setLoading(true);
    let response;
    const _focus = overFocus === null ? null : overFocus ?? focus;
    if (_focus && _focus.table_name !== current.id) {
      response = await fetch(process.env['REACT_APP_GET_FOCUS_TABLE_URL'] as string, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          table_name: current.id,
          page: page - 1,
          page_size: pageSize || options.pageSize,
          focus: {
            table_name: _focus.table_name,
            items_idx: Object.entries(_focus.indexes).map(([idx, v]) => {
              return { [idx]: v }
            })
          }
        })
      })
    } else {
      const url = new URLSearchParams();
      url.append('table', current.id);
      url.append('page', String(page - 1));
      url.append('page_size', String(pageSize || options.pageSize));

      response = await fetch(process.env['REACT_APP_GET_TABLE_URL'] as string + `?${url}`);
    }
    const data = await response.json();
    if (data.data.length === 0) {
      setLoading(false);
      setData([]);
      return;
    }

    setColumns(Object.keys(data.data[0]).map(column => {
      return {
        title: column,
        dataIndex: column,
        sorter: typeof data.data[0][column] !== 'object' && (
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
              src={value}/>
          }
          return value;
        }
      }
    }))

    setData(data.data.map((element: any, index: number) => ({...element, index})));
    setLoading(false);
    setOptions({
      total: data.total,
      page: data.page + 1,
      pageSize: data.page_size,
    })
  }

  useEffect(() => {
    loadTable()
  }, [current])

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
      setFocus(newFocus);

      if (focus?.table_name && focus.table_name !== current.id) {
        loadTable(1, options.pageSize, newFocus);
      }
    },
  };

  const changeHandler = useCallback((newPagination: TablePaginationConfig) => {
    if (newPagination.current === options.page && newPagination.pageSize === options.pageSize) return;
    loadTable(newPagination.current, newPagination.pageSize);
  }, [options])

  const clearFocus = useCallback(() => {
    setFocus(undefined);
    if (current.id !== focus?.table_name) {
      loadTable(1, options.pageSize, null)
    }
  }, [current, options, focus])

  return <>
    <div style={{ height: focus ? 60 : 1, opacity: focus ? 1 : 0, transition: '.2s all ease-out', overflow: 'hidden' }}>
        <div style={{ color: 'red' }}>
          <strong>Focus mode</strong>
        </div>
        {focus && <>
        table: <strong>{focus?.table_name}&nbsp;</strong>
        indexes:&nbsp;
        {Object.entries(focus?.indexes || []).map(([idx, v], index) => {
          return <span key={index}>
            <strong>{idx}</strong>=<strong>{v}</strong>&nbsp;
          </span>;
        })}
        &nbsp;<Button size="small" onClick={clearFocus}>Clear</Button>
        </>}
    </div>
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
        selectedRowKeys: focus ? [focus.key] : [],
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
      style={{width: '100%'}}
      columns={columns}
      dataSource={loading ? [] : data}/>
  </>
}

export { Table }
