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
}

interface MetaNode extends BaseNode {
  type: 'meta';
  graph: GraphData;
}

type Node = MetaNode | TransformNode
export type { TransformNode, MetaNode, PipeTable, GraphData }