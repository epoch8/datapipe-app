import React, { FC, useEffect, useRef, useState } from 'react';
import Cytoscape from 'cytoscape';
import CytoscapeComponent from 'react-cytoscapejs'
import "cytoscape-context-menus/cytoscape-context-menus.css";
import Hammer from 'react-hammerjs';

// @ts-ignore
import nodeHtmlLabel from 'cytoscape-node-html-label';
import dagre from 'cytoscape-dagre';
import contextMenus from 'cytoscape-context-menus';

import './style.css';
import { reprocessData } from './process';
import { stylesheet } from './stylesheet';
import { Table } from '../table';
import { Alert, AlertProps, Drawer, InputRef, Progress, Spin } from 'antd';
import { PipeTable, RunStepWebSocketComponentProps } from '../../types';
import { FilterValue } from 'antd/lib/table/interface';

Cytoscape.use(nodeHtmlLabel);
Cytoscape.use(dagre);
Cytoscape.use(contextMenus);


const RunStepWebSocketComponent: FC<RunStepWebSocketComponentProps> = (transform) => {
 const [socket, setSocket] = useState<WebSocket | null>(null);
 const [data, setData] = useState<any[]>([]);
 const [status, setStatus] = useState<"active" | "normal" | "exception" | "success" | undefined>("active")

 useEffect(() => {
  const ws = new WebSocket(`${process.env['REACT_APP_RUN_STEP_URL']}${transform}/run-status`);
  setSocket(ws);

  ws.onmessage = (event) => {
    setData((prevMessages) => [...prevMessages, event.data]);
  };

  ws.onerror = (event) => {
    setStatus("exception")
    console.error('WebSocket error:', event);
  };

  return () => {
    ws.close();
  };
 }, []);

 return (<>
  <Progress status={status} size="small"></Progress>
 </>);
}

function Cy() {
  const [drawerWidth, setWidth] = useState(600);
  const [visible, setVisible] = useState(false);
  const [graphData, setGraphData] = useState<Cytoscape.ElementDefinition[]>([]);
  const [currentTable, setCurrentTable] = useState<PipeTable>();
  const [loading, setLoading] = useState(false);
  const [cy, setCy] = useState<Cytoscape.Core>();
  const [alertMsg, setAlertMsg] = useState<AlertProps | null>(null);
  const [currentStep, isCurrentStep] = useState<string>("");
  const [isWebSocket, setIsWebSocket] = useState<boolean>(false);

  const closeAlert = () => {
    setAlertMsg(null);
  }

  useEffect(() => {
    async function loadGraph() {
      setLoading(true);
      const response = await fetch(`http://localhost:3001${process.env['REACT_APP_GET_GRAPH_URL']}` as string);
      const data = await response.json();
      const {nodes, edges} = reprocessData(data);
      const elements: Cytoscape.ElementDefinition[] = Array.from(
        nodes.entries()
      ).map(([nodeId, options]) => ({
        selectable: options.type !== "group",
        data: {
          id: nodeId,
          label: options.name,
          ...options,
        },
      }));

      edges.forEach(edge => {
        elements.push({
          grabbable: false,
          data: edge
        })
      })
      setGraphData(elements);
      setLoading(false);
    }

    loadGraph()
  }, []);

  useEffect(() => {
    if (cy === undefined) return;
    if (cy.elements().length === 0) return;
    if (loading) return;
    cy.layout({
      name: 'dagre',
      nodeDimensionsIncludeLabels: true,
      spacingFactor: 1,
      nodeSep: 20,
      rankSep: 20,
    } as dagre.DagreLayoutOptions).run();

    // @ts-ignore
    // cy.contextMenus({
    //   evtType: "cxttap",
    //   menuItems: [
    //     {
    //       id: "details",
    //       content: "View Details...",
    //       tooltipText: "View Details",
    //       selector: 'node[type = "table"]',
    //       onClickFunction: function (event: Cytoscape.EventObject) {
    //         setCurrentTable(event.target.data());
    //         setVisible(true);
    //       },
    //       hasTrailingDivider: true
    //     },
    //   ],
    //   menuItemClasses: ["custom-menu-item", "custom-menu-item:hover"],
    //   contextMenuClasses: ["custom-context-menu"]
    // });

    cy.on('tap', event => {
      const node = event.target;
      if (node === cy) {
        setVisible(false);
        return;
      }
    });

    cy.on('select', 'node', selected => {
      const node = selected.target;
      if (node === cy) {
        setVisible(false);
        return;
      }
      setCurrentTable(node.data());
      setVisible(true);

      node.connectedEdges().forEach((edge: any) => {
        if (edge.target().id() !== node.id()) {
          edge.select()
        }
      });
    });

    // @ts-ignore
    cy.nodeHtmlLabel([
      {
        query: 'node',
        halign: 'center',
        valign: 'center',
        halignBox: 'center',
        valignBox: 'center',
        tpl(data: Cytoscape.NodeDataDefinition) {
          if (data.type === 'table') {
            return `
              <div class="node-core" style="width: ${
              Math.max(
                data.name.length * 10,
                (data.indexes || []).join(', ').length * 6
              )
            }; height: 70px">
                  <div class="icon icon-table"></div>
                  <div class="name">${data.name}</div>
                  ${data.indexes ? `<div class="indexes">${data.indexes.join(', ')}</div>` : ''}
                  ${data.size ? `<div class="indexes">size: ${data.size}</div>` : ''}
                  ${data.store_class ? `<div class="store">${data.store_class}</div>` : ''}
              </div>
            `
          } else {
            return `
              <div class="node-core" style="width: ${
              Math.max(
                data.name.length * 10,
                (data.indexes || []).join(', ').length * 6
              )
            }; height: 70px">
                  <div class="name">${data.name}</div>
                  ${data.indexes ? `<div class="indexes">${data.indexes.join(', ')}</div>` : ''}
                  ${data.total_idx_count | data.changed_idx_count ? `<div class="indexes">total/changed: ${data.total_idx_count}/${data.changed_idx_count}</div>` : ''}
                  <div class="transform-type">${data.transform_type}</div>
              </div>
            `
          }
        }
      },
    ])
  }, [cy, loading])

  return (
    <>
      {alertMsg && <Alert message={alertMsg.message} type={alertMsg.type} closable afterClose={closeAlert} />}
      {isWebSocket && <RunStepWebSocketComponent transform={currentStep}/>}
      {loading && <Spin className="spin" spinning={true} />}
      <Drawer
        mask={false}
        autoFocus={false}
        width={drawerWidth} title={<>Table: <span style={{ color: 'blue' }}>{currentTable?.id}</span></>} onClose={() => setVisible(false)} visible={visible}>
        <Hammer
          direction={'DIRECTION_HORIZONTAL'}
          onPan={(pan) => {
            setWidth(Math.max(window.innerWidth - pan.center.x, 600))
          }}>
          <div className="dragger">
            <div className="drag-badge">=</div>
          </div>
        </Hammer>
        {currentTable &&
          <Table
            current={currentTable}
            setAlertMsg={setAlertMsg}
          />
        }
      </Drawer>
      <CytoscapeComponent
        stylesheet={stylesheet}
        cy={setCy}
        autoungrabify
        maxZoom={4}
        minZoom={0.2}
        elements={graphData}
        className="cy-container"/>
    </>
  )
}

export default Cy;