import { ComfyApp } from '@comfyorg/comfyui-frontend-types'
// Import LiteGraph
import { LiteGraph } from '@comfyorg/litegraph'
import React from 'react'
import ReactDOM from 'react-dom/client'

import App from './App'
import './index.css'
// Initialize i18n
import './utils/i18n'

// Wait for the app to be initialized
const waitForInit = (): Promise<ComfyApp> => {
  return new Promise((resolve) => {
    const checkInterval = setInterval(() => {
      if (window.app) {
        clearInterval(checkInterval)
        resolve(window.app)
      }
    }, 100)
  })
}

// Initialize the extension
const initializeExtension = async () => {
  try {
    const app = await waitForInit()
    console.log('Agent Node Pack extension initializing...')

    // Register the sidebar tab using ComfyUI's extension API
    const sidebarTab = {
      id: 'agent-nodepack',
      icon: 'pi pi-robot', // Using PrimeVue icon
      title: 'Agent Node Pack',
      tooltip: 'AI-powered workflow generation and optimization tools',
      type: 'custom' as const,
      render: (element: HTMLElement) => {
        console.log('Rendering Agent Node Pack Extension')
        // Create a container for our React app
        const container = document.createElement('div')
        container.id = 'agent-nodepack-root'
        container.style.height = '100%'
        element.appendChild(container)

        // Mount the React app to the container
        ReactDOM.createRoot(container).render(
          <React.StrictMode>
            <App />
          </React.StrictMode>
        )
      }
    }

    app.extensionManager.registerSidebarTab(sidebarTab)

    // Register bottom panel tabs for each feature
    const registerBottomPanelTab = (
      id: string,
      title: string,
      content: string
    ) => {
      const tabButton = document.createElement('button')
      tabButton.id = `${id}-tab`
      tabButton.textContent = title
      tabButton.className = 'comfyui-bottom-panel-tab'

      tabButton.addEventListener('click', () => {
        // Check if tab already exists
        let tab = document.querySelector(
          `[data-tab-id="${id}-tab"]`
        ) as HTMLElement

        if (!tab) {
          // Create a new tab
          tab = document.createElement('div')
          tab.className = 'comfyui-tab'
          tab.setAttribute('data-tab-id', `${id}-tab`)
          tab.style.display = 'flex'
          tab.style.flexDirection = 'column'
          tab.style.height = '100%'
          tab.style.padding = '10px'
          tab.style.overflow = 'auto'

          // Add content
          tab.innerHTML = content

          // Add to the bottom panel
          const bottomPanel = document.querySelector('.comfyui-bottom-panel')
          if (bottomPanel) {
            bottomPanel.appendChild(tab)
          }
        }

        // Switch to the new tab
        const tabs = document.querySelectorAll('.comfyui-tab')
        tabs.forEach((t) => {
          ;(t as HTMLElement).style.display = 'none'
        })
        tab.style.display = 'flex'
      })

      // Add to the bottom panel tabs container
      const tabsContainer = document.querySelector('.comfyui-bottom-panel-tabs')
      if (tabsContainer) {
        tabsContainer.appendChild(tabButton)
      }
    }

    // Register bottom panel tabs for each feature
    registerBottomPanelTab(
      'workflow-generation',
      'Workflow Generation',
      `
        <h2>Workflow Generation</h2>
        <div style="margin-bottom: 20px;">
          <label for="workflow-prompt" style="display: block; margin-bottom: 5px;">Describe the workflow you want to create:</label>
          <textarea id="workflow-prompt" style="width: 100%; height: 100px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;" placeholder="E.g., Create a workflow that generates an image from text using Stable Diffusion"></textarea>
        </div>
        <div style="margin-bottom: 20px;">
          <button id="generate-workflow-btn" style="padding: 10px 15px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">Generate Workflow</button>
        </div>
        <div id="workflow-result" style="margin-top: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; min-height: 100px; background-color: #f9f9f9;">
          <p>Generated workflow will appear here...</p>
        </div>
      `
    )

    registerBottomPanelTab(
      'workflow-debug',
      'Workflow Debug',
      `
        <h2>Workflow Debug</h2>
        <div style="margin-bottom: 20px;">
          <button id="debug-workflow-btn" style="padding: 10px 15px; background-color: #ff9800; color: white; border: none; border-radius: 4px; cursor: pointer;">Debug Current Workflow</button>
        </div>
        <div id="debug-result" style="margin-top: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; min-height: 100px; background-color: #f9f9f9;">
          <p>Debug results will appear here...</p>
        </div>
      `
    )

    registerBottomPanelTab(
      'workflow-optimization',
      'Workflow Optimization',
      `
        <h2>Workflow Optimization</h2>
        <div style="margin-bottom: 20px;">
          <label for="optimization-goal" style="display: block; margin-bottom: 5px;">Optimization Goal:</label>
          <select id="optimization-goal" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
            <option value="performance">Performance (faster execution)</option>
            <option value="memory">Memory Usage (lower VRAM)</option>
            <option value="quality">Quality (better output)</option>
          </select>
        </div>
        <div style="margin-bottom: 20px;">
          <button id="optimize-workflow-btn" style="padding: 10px 15px; background-color: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">Optimize Workflow</button>
        </div>
        <div id="optimization-result" style="margin-top: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; min-height: 100px; background-color: #f9f9f9;">
          <p>Optimization results will appear here...</p>
        </div>
      `
    )

    registerBottomPanelTab(
      'parameter-test',
      'Parameter Test',
      `
        <h2>Parameter Test</h2>
        <div style="margin-bottom: 20px;">
          <label for="test-node" style="display: block; margin-bottom: 5px;">Select Node:</label>
          <select id="test-node" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
            <option value="">Select a node...</option>
          </select>
        </div>
        <div style="margin-bottom: 20px;">
          <label for="test-parameter" style="display: block; margin-bottom: 5px;">Select Parameter:</label>
          <select id="test-parameter" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
            <option value="">Select a parameter...</option>
          </select>
        </div>
        <div style="margin-bottom: 20px;">
          <label for="test-value" style="display: block; margin-bottom: 5px;">Test Value:</label>
          <input id="test-value" type="text" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;" placeholder="Enter a value to test">
        </div>
        <div style="margin-bottom: 20px;">
          <button id="test-parameter-btn" style="padding: 10px 15px; background-color: #9C27B0; color: white; border: none; border-radius: 4px; cursor: pointer;">Test Parameter</button>
        </div>
        <div id="test-result" style="margin-top: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; min-height: 100px; background-color: #f9f9f9;">
          <p>Test results will appear here...</p>
        </div>
      `
    )

    registerBottomPanelTab(
      'node-search',
      'Node Search',
      `
        <h2>Node Search</h2>
        <div style="margin-bottom: 20px;">
          <label for="search-query" style="display: block; margin-bottom: 5px;">Search for nodes:</label>
          <input id="search-query" type="text" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;" placeholder="E.g., image generation, text to image, style transfer">
        </div>
        <div style="margin-bottom: 20px;">
          <button id="search-nodes-btn" style="padding: 10px 15px; background-color: #ff9800; color: white; border: none; border-radius: 4px; cursor: pointer;">Search Nodes</button>
        </div>
        <div id="search-result" style="margin-top: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; min-height: 100px; background-color: #f9f9f9;">
          <p>Search results will appear here...</p>
        </div>
      `
    )

    registerBottomPanelTab(
      'ai-assistant',
      'AI Assistant',
      `
        <h2>AI Assistant</h2>
        <div id="chat-messages" style="flex-grow: 1; overflow-y: auto; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 10px; background-color: #f9f9f9; min-height: 200px;">
          <div class="message assistant" style="margin-bottom: 10px;">
            <div style="background-color: #e3f2fd; padding: 10px; border-radius: 10px; max-width: 80%;">
              Hello! I'm your AI assistant for ComfyUI. I can help you with workflow generation, debugging, optimization, parameter testing, and node search. How can I assist you today?
            </div>
          </div>
        </div>
        <div style="display: flex; margin-bottom: 10px;">
          <input id="chat-input" type="text" style="flex-grow: 1; padding: 8px; border: 1px solid #ccc; border-radius: 4px; margin-right: 10px;" placeholder="Type your message here...">
          <button id="send-message-btn" style="padding: 8px 15px; background-color: #26a69a; color: white; border: none; border-radius: 4px; cursor: pointer;">Send</button>
        </div>
      `
    )

    // Add event listeners for the buttons
    document.addEventListener('click', (e) => {
      const target = e.target as HTMLElement

      // Workflow Generation
      if (target.id === 'generate-workflow-btn') {
        const promptInput = document.getElementById(
          'workflow-prompt'
        ) as HTMLTextAreaElement
        const resultDiv = document.getElementById(
          'workflow-result'
        ) as HTMLDivElement

        if (promptInput && resultDiv) {
          if (!promptInput.value) {
            resultDiv.innerHTML =
              '<p style="color: red;">Please enter a description for the workflow.</p>'
            return
          }

          resultDiv.innerHTML =
            '<p>Generating workflow... This may take a moment.</p>'

          fetch('/api/agent/workflow/generate', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              prompt: promptInput.value
            })
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                resultDiv.innerHTML = `
                  <h3>Generated Workflow</h3>
                  <p>${data.message}</p>
                  <button id="apply-workflow-btn" style="padding: 8px 15px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;">Apply to Current Workflow</button>
                `

                // Add event listener for the apply button
                const applyBtn = document.getElementById('apply-workflow-btn')
                if (applyBtn) {
                  applyBtn.addEventListener('click', () => {
                    // Apply the workflow to the current graph
                    app.loadGraphData(data.workflow)
                    app.extensionManager.toast.add({
                      severity: 'success',
                      summary: 'Success',
                      detail: 'Workflow has been applied to the current graph.',
                      life: 3000
                    })
                  })
                }
              } else {
                resultDiv.innerHTML = `<p style="color: red;">Error: ${data.message}</p>`
              }
            })
            .catch((error) => {
              console.error('Error generating workflow:', error)
              resultDiv.innerHTML = `<p style="color: red;">Error: Failed to generate workflow. Please try again.</p>`
            })
        }
      }

      // Workflow Debug
      if (target.id === 'debug-workflow-btn') {
        const resultDiv = document.getElementById(
          'debug-result'
        ) as HTMLDivElement

        if (resultDiv) {
          resultDiv.innerHTML =
            '<p>Debugging workflow... This may take a moment.</p>'

          fetch('/api/agent/workflow/debug', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              workflow: app.graph.serialize()
            })
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                resultDiv.innerHTML = `
                  <h3>Debug Results</h3>
                  <p>${data.message}</p>
                  ${
                    data.issues && data.issues.length > 0
                      ? `<ul>${data.issues.map((issue: string) => `<li>${issue}</li>`).join('')}</ul>`
                      : '<p>No issues found in your workflow.</p>'
                  }
                `
              } else {
                resultDiv.innerHTML = `<p style="color: red;">Error: ${data.message}</p>`
              }
            })
            .catch((error) => {
              console.error('Error debugging workflow:', error)
              resultDiv.innerHTML = `<p style="color: red;">Error: Failed to debug workflow. Please try again.</p>`
            })
        }
      }

      // Workflow Optimization
      if (target.id === 'optimize-workflow-btn') {
        const goalSelect = document.getElementById(
          'optimization-goal'
        ) as HTMLSelectElement
        const resultDiv = document.getElementById(
          'optimization-result'
        ) as HTMLDivElement

        if (goalSelect && resultDiv) {
          resultDiv.innerHTML =
            '<p>Optimizing workflow... This may take a moment.</p>'

          fetch('/api/agent/workflow/optimize', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              workflow: app.graph.serialize(),
              goal: goalSelect.value
            })
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                resultDiv.innerHTML = `
                  <h3>Optimization Results</h3>
                  <p>${data.message}</p>
                  <button id="apply-optimization-btn" style="padding: 8px 15px; background-color: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;">Apply Optimization</button>
                `

                // Add event listener for the apply button
                const applyBtn = document.getElementById(
                  'apply-optimization-btn'
                )
                if (applyBtn) {
                  applyBtn.addEventListener('click', () => {
                    // Apply the optimization to the current graph
                    app.loadGraphData(data.optimized_workflow)
                    app.extensionManager.toast.add({
                      severity: 'success',
                      summary: 'Success',
                      detail:
                        'Optimization has been applied to the current workflow.',
                      life: 3000
                    })
                  })
                }
              } else {
                resultDiv.innerHTML = `<p style="color: red;">Error: ${data.message}</p>`
              }
            })
            .catch((error) => {
              console.error('Error optimizing workflow:', error)
              resultDiv.innerHTML = `<p style="color: red;">Error: Failed to optimize workflow. Please try again.</p>`
            })
        }
      }

      // Parameter Test
      if (target.id === 'test-parameter-btn') {
        const nodeSelect = document.getElementById(
          'test-node'
        ) as HTMLSelectElement
        const paramSelect = document.getElementById(
          'test-parameter'
        ) as HTMLSelectElement
        const valueInput = document.getElementById(
          'test-value'
        ) as HTMLInputElement
        const resultDiv = document.getElementById(
          'test-result'
        ) as HTMLDivElement

        if (nodeSelect && paramSelect && valueInput && resultDiv) {
          if (!nodeSelect.value || !paramSelect.value || !valueInput.value) {
            resultDiv.innerHTML =
              '<p style="color: red;">Please select a node, parameter, and enter a test value.</p>'
            return
          }

          resultDiv.innerHTML =
            '<p>Testing parameter... This may take a moment.</p>'

          fetch('/api/agent/parameter/test', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              node_id: nodeSelect.value,
              parameter: paramSelect.value,
              value: valueInput.value
            })
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                resultDiv.innerHTML = `
                  <h3>Test Results</h3>
                  <p>${data.message}</p>
                  ${data.result ? `<pre>${JSON.stringify(data.result, null, 2)}</pre>` : ''}
                `
              } else {
                resultDiv.innerHTML = `<p style="color: red;">Error: ${data.message}</p>`
              }
            })
            .catch((error) => {
              console.error('Error testing parameter:', error)
              resultDiv.innerHTML = `<p style="color: red;">Error: Failed to test parameter. Please try again.</p>`
            })
        }
      }

      // Node Search
      if (target.id === 'search-nodes-btn') {
        const queryInput = document.getElementById(
          'search-query'
        ) as HTMLInputElement
        const resultDiv = document.getElementById(
          'search-result'
        ) as HTMLDivElement

        if (queryInput && resultDiv) {
          if (!queryInput.value) {
            resultDiv.innerHTML =
              '<p style="color: red;">Please enter a search query.</p>'
            return
          }

          resultDiv.innerHTML =
            '<p>Searching for nodes... This may take a moment.</p>'

          fetch('/api/agent/node/search', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              query: queryInput.value
            })
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                resultDiv.innerHTML = `
                  <h3>Search Results</h3>
                  <p>Found ${data.nodes.length} nodes matching "${queryInput.value}":</p>
                  <div style="margin-top: 10px;">
                    ${data.nodes
                      .map(
                        (node: any) => `
                      <div style="margin-bottom: 15px; padding: 10px; border: 1px solid #eee; border-radius: 4px; background-color: #fff;">
                        <h4 style="margin-top: 0; margin-bottom: 5px;">${node.name} (${node.type})</h4>
                        <p style="margin-top: 0; margin-bottom: 5px; color: #666;">Category: ${node.category}</p>
                        <p style="margin-top: 0; margin-bottom: 10px;">${node.description}</p>
                        <button class="add-node-btn" data-node-type="${node.type}" style="padding: 5px 10px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">Add to Workflow</button>
                      </div>
                    `
                      )
                      .join('')}
                  </div>
                `

                // Add event listeners for the add node buttons
                const addNodeBtns = resultDiv.querySelectorAll('.add-node-btn')
                addNodeBtns.forEach((btn) => {
                  btn.addEventListener('click', () => {
                    const nodeType = btn.getAttribute('data-node-type')
                    if (nodeType) {
                      // Add the node to the workflow
                      const node = LiteGraph.createNode(nodeType)
                      if (node) {
                        app.graph.add(node)
                        app.graph.change()
                        app.extensionManager.toast.add({
                          severity: 'success',
                          summary: 'Success',
                          detail: `Node ${nodeType} has been added to the workflow.`,
                          life: 3000
                        })
                      } else {
                        app.extensionManager.toast.add({
                          severity: 'error',
                          summary: 'Error',
                          detail: `Failed to create node ${nodeType}.`,
                          life: 3000
                        })
                      }
                    }
                  })
                })
              } else {
                resultDiv.innerHTML = `<p style="color: red;">Error: ${data.message}</p>`
              }
            })
            .catch((error) => {
              console.error('Error searching for nodes:', error)
              resultDiv.innerHTML = `<p style="color: red;">Error: Failed to search for nodes. Please try again.</p>`
            })
        }
      }

      // AI Assistant - Send Message
      if (target.id === 'send-message-btn') {
        const chatInput = document.getElementById(
          'chat-input'
        ) as HTMLInputElement
        const chatMessages = document.getElementById('chat-messages')

        if (chatInput && chatMessages && chatInput.value.trim()) {
          // Add user message to the chat
          const userMessage = document.createElement('div')
          userMessage.className = 'message user'
          userMessage.style.marginBottom = '10px'
          userMessage.style.textAlign = 'right'
          userMessage.innerHTML = `
            <div style="background-color: #e8f5e9; padding: 10px; border-radius: 10px; max-width: 80%; display: inline-block; text-align: left;">
              ${chatInput.value}
            </div>
          `
          chatMessages.appendChild(userMessage)

          // Store the user message
          const userMessageText = chatInput.value
          chatInput.value = ''

          // Scroll to the bottom of the chat
          chatMessages.scrollTop = chatMessages.scrollHeight

          // Add a loading indicator
          const loadingMessage = document.createElement('div')
          loadingMessage.className = 'message assistant'
          loadingMessage.style.marginBottom = '10px'
          loadingMessage.innerHTML = `
            <div style="background-color: #e3f2fd; padding: 10px; border-radius: 10px; max-width: 80%;">
              <div class="loading-dots">
                <span>.</span><span>.</span><span>.</span>
              </div>
            </div>
          `
          chatMessages.appendChild(loadingMessage)

          // Scroll to the bottom of the chat
          chatMessages.scrollTop = chatMessages.scrollHeight

          fetch('/api/agent/conversation/send', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              message: userMessageText
            })
          })
            .then((response) => response.json())
            .then((data) => {
              // Remove the loading indicator
              chatMessages.removeChild(loadingMessage)

              if (data.success) {
                // Add assistant response to the chat
                const assistantMessage = document.createElement('div')
                assistantMessage.className = 'message assistant'
                assistantMessage.style.marginBottom = '10px'
                assistantMessage.innerHTML = `
                  <div style="background-color: #e3f2fd; padding: 10px; border-radius: 10px; max-width: 80%;">
                    ${data.response}
                  </div>
                `
                chatMessages.appendChild(assistantMessage)

                // Scroll to the bottom of the chat
                chatMessages.scrollTop = chatMessages.scrollHeight
              } else {
                // Add error message to the chat
                const errorMessage = document.createElement('div')
                errorMessage.className = 'message assistant'
                errorMessage.style.marginBottom = '10px'
                errorMessage.innerHTML = `
                  <div style="background-color: #ffebee; padding: 10px; border-radius: 10px; max-width: 80%;">
                    Error: ${data.message}
                  </div>
                `
                chatMessages.appendChild(errorMessage)

                // Scroll to the bottom of the chat
                chatMessages.scrollTop = chatMessages.scrollHeight
              }
            })
            .catch((error) => {
              console.error('Error sending message:', error)

              // Remove the loading indicator
              chatMessages.removeChild(loadingMessage)

              // Add error message to the chat
              const errorMessage = document.createElement('div')
              errorMessage.className = 'message assistant'
              errorMessage.style.marginBottom = '10px'
              errorMessage.innerHTML = `
                <div style="background-color: #ffebee; padding: 10px; border-radius: 10px; max-width: 80%;">
                  Error: Failed to send message. Please try again.
                </div>
              `
              chatMessages.appendChild(errorMessage)

              // Scroll to the bottom of the chat
              chatMessages.scrollTop = chatMessages.scrollHeight
            })
        }
      }
    })

    // Add event listener for Enter key in chat input
    document.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const target = e.target as HTMLElement
        if (target.id === 'chat-input') {
          const sendBtn = document.getElementById('send-message-btn')
          if (sendBtn) {
            sendBtn.click()
          }
        }
      }
    })

    // Register the extension using the correct ComfyUI API
    app.registerExtension({
      name: 'Agent.NodePack',
      commands: [
        {
          id: 'agent-nodepack.show-info',
          label: 'Show Agent Node Pack Info',
          function: () => {
            // Use a simple alert instead of dialog.info
            alert(
              'Agent Node Pack\n\nAgent Node Pack is a powerful extension for ComfyUI that provides AI-powered workflow generation, debugging, optimization, parameter testing, and node search capabilities.\n\nVersion: 1.0.0\nAuthor: Agent Node Pack Team\nLicense: MIT'
            )
          }
        },
        {
          id: 'agent-nodepack.generate-workflow',
          label: 'Generate Workflow',
          function: () => {
            // Click the workflow generation tab button
            const button = document.getElementById('workflow-generation-tab')
            if (button) {
              button.click()
            }
          }
        },
        {
          id: 'agent-nodepack.debug-workflow',
          label: 'Debug Workflow',
          function: () => {
            // Click the workflow debug tab button
            const button = document.getElementById('workflow-debug-tab')
            if (button) {
              button.click()
            }
          }
        },
        {
          id: 'agent-nodepack.optimize-workflow',
          label: 'Optimize Workflow',
          function: () => {
            // Click the workflow optimization tab button
            const button = document.getElementById('workflow-optimization-tab')
            if (button) {
              button.click()
            }
          }
        },
        {
          id: 'agent-nodepack.test-parameters',
          label: 'Test Parameters',
          function: () => {
            // Click the parameter test tab button
            const button = document.getElementById('parameter-test-tab')
            if (button) {
              button.click()
            }
          }
        },
        {
          id: 'agent-nodepack.search-nodes',
          label: 'Search Nodes',
          function: () => {
            // Click the node search tab button
            const button = document.getElementById('node-search-tab')
            if (button) {
              button.click()
            }
          }
        },
        {
          id: 'agent-nodepack.ai-assistant',
          label: 'AI Assistant',
          function: () => {
            // Click the AI assistant tab button
            const button = document.getElementById('ai-assistant-tab')
            if (button) {
              button.click()
            }
          }
        }
      ],
      keybindings: [
        {
          combo: {
            key: 'A',
            ctrl: true,
            shift: true
          },
          commandId: 'agent-nodepack.ai-assistant'
        }
      ]
    })

    console.log('Agent Node Pack extension initialized successfully')
  } catch (error) {
    console.error('Failed to initialize Agent Node Pack extension:', error)
  }
}

// Start initialization
void initializeExtension()
