interface PipeTable {
  id: string,
  indexes: string[],
  size: number,
  store_class: string
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
  name?: string;
  func?: string;
}

interface TransformNode extends BaseNode {
  type: 'transform';
  inputs: string[];
  outputs: string[];
  step_class: string;
  indexes: string[];
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
}

type Node = MetaNode | TransformNode
export type { TransformNode, MetaNode, PipeTable, GraphData, GetDataReq }