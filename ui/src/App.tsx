import React from 'react'
import { useTranslation } from 'react-i18next'

import './App.css'

const App: React.FC = () => {
  const { t } = useTranslation()

  return (
    <div className="agent-nodepack-app">
      <div className="agent-nodepack-header">
        <h1>{t('app.title', 'Agent Node Pack')}</h1>
        <p>
          {t(
            'app.description',
            'AI-powered workflow generation and optimization for ComfyUI'
          )}
        </p>
      </div>
      <div className="agent-nodepack-content">
        <div className="agent-nodepack-card">
          <h2>{t('app.features.title', 'Features')}</h2>
          <ul>
            <li>
              {t('app.features.workflowGeneration', 'Workflow Generation')}
            </li>
            <li>{t('app.features.workflowDebugging', 'Workflow Debugging')}</li>
            <li>
              {t('app.features.workflowOptimization', 'Workflow Optimization')}
            </li>
            <li>{t('app.features.parameterTesting', 'Parameter Testing')}</li>
            <li>{t('app.features.nodeSearch', 'Node Search')}</li>
            <li>{t('app.features.aiAssistant', 'AI Assistant')}</li>
          </ul>
        </div>
        <div className="agent-nodepack-card">
          <h2>{t('app.gettingStarted.title', 'Getting Started')}</h2>
          <p>
            {t(
              'app.gettingStarted.description',
              'Use the tabs in the bottom panel to access different features of the Agent Node Pack.'
            )}
          </p>
          <p>
            {t(
              'app.gettingStarted.shortcuts',
              'You can also use keyboard shortcuts to quickly access features:'
            )}
          </p>
          <ul>
            <li>
              <kbd>Ctrl+Shift+A</kbd> -{' '}
              {t(
                'app.gettingStarted.shortcuts.aiAssistant',
                'Open AI Assistant'
              )}
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default App
