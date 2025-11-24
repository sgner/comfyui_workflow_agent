
import { GripHorizontal, Maximize2, Minimize2, RefreshCw, X, Scaling } from 'lucide-react'
import React, { useCallback, useEffect, useRef, useState } from 'react'

import ChatPanel from './components/ChatPanel'
import SettingsModal from './components/SettingsModal'
import WorkflowVisualizer from './components/WorkflowVisualizer'
import { DEFAULT_WORKFLOW } from './constants'
import { sendMessageToComfyAgent } from './services/aiService'
import { AppSettings, ChatMessage, ComfyNode, ComfyWorkflow, Sender, WorkflowIssue } from './types'
import { t } from './utils/i18n'

interface AppProps {
  displayMode?: 'floating' | 'sidebar'
}

const App: React.FC<AppProps> = () => {
  // --- UI State ---
  const [isVisible, setIsVisible] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)

  // Window Management State
  const [windowPos, setWindowPos] = useState({ x: 100, y: 50 })
  // Initialize size from local storage or default
  const [windowSize, setWindowSize] = useState(() => {
      const saved = localStorage.getItem('comfy_copilot_size');
      if (saved) {
          try { return JSON.parse(saved); } catch (e) { console.error(e); }
      }
      return { width: 950, height: 700 };
  });

  const windowRef = useRef<HTMLDivElement>(null)
  const dragRef = useRef<{ startX: number, startY: number, startLeft: number, startTop: number } | null>(null)
  const resizeRef = useRef<{ startX: number, startY: number, startWidth: number, startHeight: number } | null>(null)

  // --- Application State ---
  const [appSettings, setAppSettings] = useState<AppSettings>(() => {
    const saved = localStorage.getItem('comfy_copilot_settings')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        return { ...parsed, language: parsed.language || 'en' }
      } catch (e) {
        console.error(e)
      }
    }
    return {
      provider: 'google',
      apiKey: (typeof process !== 'undefined' && process.env?.API_KEY) || '',
      modelName: 'gemini-2.5-flash',
      baseUrl: '',
      language: 'en'
    }
  })

  const [workflow, setWorkflow] = useState<ComfyWorkflow>(DEFAULT_WORKFLOW)
  const [issues, setIssues] = useState<WorkflowIssue[]>([]) // Stores AI and System detected issues
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init-1',
      sender: Sender.AI,
      text: t(appSettings.language, 'welcome'),
      timestamp: new Date(),
      metadata: {
        suggestedActions: ['Create Basic TXT2IMG', 'Analyze Current Workflow']
      }
    }
  ])
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)

  // --- ComfyUI Integration Hooks ---
  const app = (window as any).app;

  // --- Widget Name Resolution ---
  // This function determines the names of widgets by comparing the full node definition
  // against the inputs that are currently active as slots.
  const resolveWidgetNames = useCallback((node: ComfyNode): string[] => {
    if (typeof window === 'undefined') return [];
    const lg = (window as any).LiteGraph;
    if (!lg || !lg.registered_node_types) return [];

    // Get the definition for this node type
    const def = lg.registered_node_types[node.type];
    if (!def || !def.nodeData || !def.nodeData.input) return [];

    const inputs = def.nodeData.input;
    const required = inputs.required || {};
    const optional = inputs.optional || {};

    // Get names of inputs that are currently functioning as slots (connected or not, but present in inputs array)
    const slotNames = new Set((node.inputs || []).map(i => i.name));

    const widgetNames: string[] = [];

    // In ComfyUI, widgets are created for inputs that are NOT slots.
    // The order is: Required keys, then Optional keys.

    Object.keys(required).forEach(name => {
        if (!slotNames.has(name)) {
            widgetNames.push(name);
        }
    });

    Object.keys(optional).forEach(name => {
        if (!slotNames.has(name)) {
            widgetNames.push(name);
        }
    });

    return widgetNames;
  }, []);

  useEffect(() => {
    const handleToggle = () => setIsVisible(prev => !prev)
    window.addEventListener("comfy-copilot-toggle", handleToggle)

    const handleExecutionError = (event: any) => {
        if (event.detail) {
            const { node_id, exception_message, exception_type } = event.detail;
            const newIssue: WorkflowIssue = {
                id: `exec-err-${Date.now()}`,
                nodeId: node_id ? parseInt(node_id) : null,
                severity: 'error',
                message: `${exception_type || 'Error'}: ${exception_message}`,
                fixSuggestion: 'Check node configuration and inputs.'
            };
            setIssues(prev => [newIssue, ...prev]);
            if (!isVisible) setIsVisible(true);
        }
    }

    if (app && app.api) {
        app.api.addEventListener('execution_error', handleExecutionError);
    }

    return () => {
        window.removeEventListener("comfy-copilot-toggle", handleToggle)
        if (app && app.api) {
            app.api.removeEventListener('execution_error', handleExecutionError);
        }
    }
  }, [app, isVisible])

  useEffect(() => {
     if (window.innerWidth > 1200) {
         setWindowPos({ x: window.innerWidth - 1000, y: 80 })
     }
  }, [])

  const syncFromCanvas = useCallback(() => {
    if (app && app.graph) {
      const graphData = app.graph.serialize()
      setWorkflow(graphData as unknown as ComfyWorkflow)
    }
  }, [app])

  useEffect(() => {
    if (isVisible) {
        syncFromCanvas();
    }
  }, [isVisible, syncFromCanvas])

  const applyToCanvas = (newWorkflow: any) => {
    if (app) {
      app.loadGraphData(newWorkflow)
      if (
        app.canvas &&
        newWorkflow.nodes &&
        newWorkflow.nodes.length > 0
      ) {
        const nodeId = newWorkflow.nodes[0].id
        const node = app.graph.getNodeById
          ? app.graph.getNodeById(Number(nodeId))
          : null
        if (node) {
          app.canvas.centerOnNode(node)
        }
      }
    }
  }

  const saveSettings = (newSettings: AppSettings) => {
    setAppSettings(newSettings)
    localStorage.setItem('comfy_copilot_settings', JSON.stringify(newSettings))
  }

  const handleManualUpdateWorkflow = (newWorkflow: ComfyWorkflow) => {
    setWorkflow(newWorkflow)
    applyToCanvas(newWorkflow)
  }

  // --- Window Drag Logic ---
  const handleMouseMove = useCallback((e: MouseEvent) => {
      if (!dragRef.current || !windowRef.current) return;
      const dx = e.clientX - dragRef.current.startX;
      const dy = e.clientY - dragRef.current.startY;

      // Direct DOM manipulation prevents re-renders during drag (Performance fix)
      windowRef.current.style.left = `${dragRef.current.startLeft + dx}px`;
      windowRef.current.style.top = `${dragRef.current.startTop + dy}px`;
  }, []);

  const handleMouseUp = useCallback((e: MouseEvent) => {
      if (dragRef.current) {
          const dx = e.clientX - dragRef.current.startX;
          const dy = e.clientY - dragRef.current.startY;
          setWindowPos({
              x: dragRef.current.startLeft + dx,
              y: dragRef.current.startTop + dy
          });
          dragRef.current = null;
      }
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
  }, [handleMouseMove]);

  const handleMouseDown = (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      dragRef.current = {
          startX: e.clientX,
          startY: e.clientY,
          startLeft: windowPos.x,
          startTop: windowPos.y
      };
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      e.preventDefault();
  };

  // --- Resize Logic ---
  const handleResizeMouseMove = useCallback((e: MouseEvent) => {
      if (!resizeRef.current || !windowRef.current) return;
      const dx = e.clientX - resizeRef.current.startX;
      const dy = e.clientY - resizeRef.current.startY;

      const newWidth = Math.max(600, resizeRef.current.startWidth + dx);
      const newHeight = Math.max(400, resizeRef.current.startHeight + dy);

      // Direct DOM manipulation for resize performance
      windowRef.current.style.width = `${newWidth}px`;
      windowRef.current.style.height = `${newHeight}px`;
  }, []);

  const handleResizeMouseUp = useCallback((e: MouseEvent) => {
      if (resizeRef.current) {
          const dx = e.clientX - resizeRef.current.startX;
          const dy = e.clientY - resizeRef.current.startY;
          const newWidth = Math.max(600, resizeRef.current.startWidth + dx);
          const newHeight = Math.max(400, resizeRef.current.startHeight + dy);

          const newSize = { width: newWidth, height: newHeight };
          setWindowSize(newSize);
          localStorage.setItem('comfy_copilot_size', JSON.stringify(newSize));
      }
      resizeRef.current = null;
      document.removeEventListener('mousemove', handleResizeMouseMove);
      document.removeEventListener('mouseup', handleResizeMouseUp);
  }, [handleResizeMouseMove]);

  const handleResizeMouseDown = (e: React.MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();
      resizeRef.current = {
          startX: e.clientX,
          startY: e.clientY,
          startWidth: windowSize.width,
          startHeight: windowSize.height
      };
      document.addEventListener('mousemove', handleResizeMouseMove);
      document.addEventListener('mouseup', handleResizeMouseUp);
  };

  // --- Chat Logic ---
  const handleSendMessage = useCallback(
    async (overrideText?: string) => {
      const textToSend = overrideText || input
      if (!textToSend.trim() || isProcessing) return

      if (!appSettings.apiKey && appSettings.provider === 'custom') {
        setIsSettingsOpen(true)
        return
      }

      if (app && app.graph) {
        const currentGraph = app.graph.serialize()
        setWorkflow(currentGraph as unknown as ComfyWorkflow)
      }

      const userMsg: ChatMessage = {
        id: Date.now().toString(),
        sender: Sender.USER,
        text: textToSend,
        timestamp: new Date()
      }

      setMessages((prev) => [...prev, userMsg])
      setInput('')
      setIsProcessing(true)

      try {
        const historyText = messages
          .slice(-5)
          .map((m) => `${m.sender}: ${m.text}`)

        const response = await sendMessageToComfyAgent(
          workflow,
          textToSend,
          appSettings,
          historyText
        )

        if (response.updatedWorkflow) {
          setWorkflow(response.updatedWorkflow)
          applyToCanvas(response.updatedWorkflow)
        }

        if (response.issues && response.issues.length > 0) {
            setIssues(response.issues);
        }

        const aiMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: Sender.AI,
          text: response.chatResponse,
          timestamp: new Date(),
          metadata: {
            workflowUpdate: !!response.updatedWorkflow,
            missingNodes: response.missingNodes,
            suggestedActions: response.suggestedActions,
            groundingSources: response.groundingSources,
            provider: appSettings.provider
          }
        }

        setMessages((prev) => [...prev, aiMsg])
      } catch (error) {
        console.error(error)
        const errorMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: Sender.SYSTEM,
          text: 'Error: ' + (error as Error).message,
          timestamp: new Date()
        }
        setMessages((prev) => [...prev, errorMsg])
      } finally {
        setIsProcessing(false)
      }
    },
    [
      input,
      isProcessing,
      messages,
      workflow,
      appSettings,
      app
    ]
  )

  const handleActionClick = (action: string) => handleSendMessage(action)
  const isConfigured = (appSettings.provider === 'google') || (!!appSettings.apiKey || appSettings.provider === 'custom')

  if (!isVisible) return null;

  return (
    <div
        id="comfy-workflow-agent-window"
        ref={windowRef}
        className="flex flex-col overflow-hidden bg-slate-950 border border-slate-700 shadow-2xl rounded-xl transition-opacity duration-75"
        style={{
            position: 'fixed',
            left: windowPos.x,
            top: windowPos.y,
            width: isMinimized ? '300px' : `${windowSize.width}px`,
            height: isMinimized ? 'auto' : `${windowSize.height}px`,
            zIndex: 10001,
            pointerEvents: 'auto'
        }}
    >
        {/* Window Header */}
        <div
            onMouseDown={handleMouseDown}
            className="bg-slate-900 border-b border-slate-800 p-3 flex items-center justify-between cursor-move select-none group flex-shrink-0"
        >
            <div className="flex items-center gap-3">
                <div className="text-slate-500 group-hover:text-slate-300 transition-colors">
                    <GripHorizontal size={18} />
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-indigo-500 animate-pulse"></div>
                    <span className="font-bold text-slate-200 text-sm">{t(appSettings.language, 'appName')}</span>
                </div>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
                {!isMinimized && (
                    <button
                        onClick={syncFromCanvas}
                        className="p-1 hover:text-indigo-400 transition-colors"
                        title="Sync from Canvas"
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        <RefreshCw size={14} />
                    </button>
                )}
                <button
                    onClick={() => setIsMinimized(!isMinimized)}
                    className="p-1 hover:text-white transition-colors"
                    onMouseDown={(e) => e.stopPropagation()}
                >
                    {isMinimized ? <Maximize2 size={14} /> : <Minimize2 size={14} />}
                </button>
                <button
                    onClick={() => setIsVisible(false)}
                    className="p-1 hover:text-red-400 transition-colors"
                    onMouseDown={(e) => e.stopPropagation()}
                >
                    <X size={14} />
                </button>
            </div>
        </div>

        {!isMinimized && (
            <>
                <div className="flex-1 flex flex-col overflow-hidden">
                    <SettingsModal
                        isOpen={isSettingsOpen}
                        onClose={() => setIsSettingsOpen(false)}
                        currentSettings={appSettings}
                        onSave={saveSettings}
                    />

                    <div className="flex-1 overflow-hidden relative flex flex-row">
                        {/* Left: Chat Panel (35%) */}
                        <div className="w-[35%] min-w-[300px] border-r border-slate-800 flex flex-col bg-slate-950">
                            <ChatPanel
                                messages={messages}
                                input={input}
                                setInput={setInput}
                                onSend={() => handleSendMessage()}
                                isProcessing={isProcessing}
                                onActionClick={handleActionClick}
                                language={appSettings.language}
                            />
                        </div>

                        {/* Right: Visualizer (Remaining space) */}
                        <div className="flex-1 flex flex-col bg-slate-900 relative min-w-0">
                            <WorkflowVisualizer
                                workflow={workflow}
                                language={appSettings.language}
                                onOpenSettings={() => setIsSettingsOpen(true)}
                                isConfigured={isConfigured}
                                onUpdateWorkflow={handleManualUpdateWorkflow}
                                onAskAi={handleSendMessage}
                                issues={issues}
                                resolveWidgetNames={resolveWidgetNames}
                            />
                        </div>
                    </div>
                </div>

                {/* Resize Handle */}
                <div
                    onMouseDown={handleResizeMouseDown}
                    className="absolute bottom-0 right-0 w-5 h-5 cursor-se-resize z-50 flex items-center justify-center text-slate-600 hover:text-indigo-400 transition-colors"
                >
                    <Scaling size={12} className="transform rotate-90" />
                </div>
            </>
        )}
    </div>
  )
}

export default App
