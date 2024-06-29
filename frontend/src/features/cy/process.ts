import { omit } from 'lodash';
import { GraphData } from '../../types';
import Cytoscape from 'cytoscape';

function reprocess_data(data: GraphData) {
  const nodes = new Map<string, Cytoscape.NodeDataDefinition>();
  const edges = new Set<Cytoscape.EdgeDataDefinition>();
  (function process_data(data: GraphData, grouped?: string) {
    if (grouped) {
      nodes.set(grouped, {
        selectable: false
      })
    }

    for (const [table, properties] of Object.entries(data.catalog)) {
      nodes.set(table, {
        type: 'table',
        ...nodes.get(table),
        ...properties,
      })

      if (grouped) {
        nodes.set(table, {
          type: 'group',
          ...nodes.get(table),
          parent: grouped
        })
      }
    }

    for (const pipe of data.pipeline) {
      const nodeName = pipe.name;
      if (pipe.type !== 'meta') {
        nodes.set(nodeName, {
          ...omit(pipe, ['inputs', 'outputs'])
        });

        if (grouped) {
          nodes.set(nodeName, {
            ...nodes.get(nodeName),
            parent: grouped
          })
        }

        (pipe.inputs || []).forEach((input: string) => {
          edges.add({source: input, target: nodeName});
        });

        (pipe.outputs || []).forEach((output: string) => {
          edges.add({source: nodeName, target: output});
        })
      } else {
        process_data(pipe.graph, pipe.name)
      }
    }
  }(data))

  return {
    nodes,
    edges
  }
}

export { reprocess_data }
