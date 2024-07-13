import { InputRef } from "antd/lib/input/Input";
import { FilterValue } from "antd/lib/table/interface";
import { RefObject } from "react";

interface PipeTable {
  id: string,
  indexes: string[],
  size: number,
  store_class: string,
  type: string,
}

interface GraphData {
  catalog: {
    [name: string]: PipeTable
  }
  pipeline: Node[]
}

interface BaseNode {
  id: string;
  type: string;
  name: string;
  func?: string;
}

interface TransformNode extends BaseNode {
  type: 'transform';
  inputs: string[];
  outputs: string[];
}

interface MetaNode extends BaseNode {
  type: 'meta';
  graph: GraphData;
}

interface GetDataReq {
  table: string
  page: number
  page_size: number
  focus?: {
    table_name: string,
    items_idx: Record<string, string | number>[]
  }
  filters?: Record<string, string | number>
  order_by?: string
  order?: "asc" | "desc"
}

interface Options {
  total: number;
  page: number;
  pageSize: number;
}

type IdxRow = {
  [name: string]: string | number;
};

interface FocusType {
  table_name: string;
  keys: React.Key[];
  indexes: IdxRow[];
}

interface TableLoadingOptions {
  page?: number;
  pageSize?: number;
  overFocus?: FocusType | null;
  filters?: Record<string, FilterValue | null>;
  orderBy?: string;
  order?: "asc" | "desc";
}

interface Pagination {
  page: number;
  pageSize: number;
}

interface Sorting {
  orderBy?: string;
  order?: "asc" | "desc";
}


interface FilterDropDownComponentProps {
  searchInput: RefObject<InputRef>;
  column: string;
  selectedKeys: any;
  colValue: any;
  setSelectedKeys: (keys: any) => void;
  confirm: any;
  clearFilters: any;
}

interface RunStepWebSocketComponentProps {
  transform: string;
};

type Node = MetaNode | TransformNode
export type { 
  TransformNode,
  MetaNode,
  PipeTable, 
  GraphData, 
  GetDataReq, 
  TableLoadingOptions, 
  Pagination, 
  Sorting, 
  FilterDropDownComponentProps,
  FocusType,
  Options,
  IdxRow,
  RunStepWebSocketComponentProps,
 }

