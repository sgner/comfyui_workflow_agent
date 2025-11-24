
import {
  AlertTriangle,
  Cpu,
  Key,
  Languages,
  Save,
  Server,
  X
} from 'lucide-react'
import React, { useEffect, useState } from 'react'

import { AppSettings, Language } from '../types'
import { t } from '../utils/i18n'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  currentSettings: AppSettings
  onSave: (settings: AppSettings) => void
}

const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  currentSettings,
  onSave
}) => {
  const [settings, setSettings] = useState<AppSettings>(currentSettings)

  useEffect(() => {
    setSettings(currentSettings)
  }, [currentSettings, isOpen])

  if (!isOpen) return null

  const handleSave = () => {
    onSave(settings)
    onClose()
  }

  const currentLang = settings.language

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-900">
          <div className="flex items-center gap-2">
            <Cpu className="text-indigo-500" size={20} />
            <h2 className="text-lg font-semibold text-slate-100">
              {t(currentLang, 'settingsTitle')}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 h-[60vh] overflow-y-auto custom-scrollbar">
          {/* Language Selection */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-xs font-medium text-slate-300">
              <Languages size={14} />
              {t(currentLang, 'language')}
            </label>
            <select
              value={settings.language}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  language: e.target.value as Language
                })
              }
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="en">English</option>
              <option value="zh">中文 (Chinese)</option>
              <option value="ja">日本語 (Japanese)</option>
              <option value="ko">한국어 (Korean)</option>
            </select>
          </div>

          <hr className="border-slate-800" />

          {/* Provider Selection */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              {t(currentLang, 'provider')}
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() =>
                  setSettings({ ...settings, provider: 'google', baseUrl: '' })
                }
                className={`p-3 rounded-xl border flex items-center justify-center gap-2 transition-all
                                    ${
                                      settings.provider === 'google'
                                        ? 'bg-indigo-600/20 border-indigo-500 text-indigo-200'
                                        : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                                    }`}
              >
                <span className="font-medium">
                  {t(currentLang, 'googleGemini')}
                </span>
              </button>
              <button
                onClick={() => setSettings({ ...settings, provider: 'custom' })}
                className={`p-3 rounded-xl border flex items-center justify-center gap-2 transition-all
                                    ${
                                      settings.provider === 'custom'
                                        ? 'bg-emerald-600/20 border-emerald-500 text-emerald-200'
                                        : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                                    }`}
              >
                <span className="font-medium">
                  {t(currentLang, 'customLocal')}
                </span>
              </button>
            </div>
          </div>

          {/* Dynamic Form Fields */}
          <div className="space-y-4">
            {/* API Key only for Custom provider */}
            {settings.provider === 'custom' && (
              <div className="space-y-1">
                <label className="flex items-center gap-2 text-xs font-medium text-slate-300">
                  <Key size={14} />
                  {t(currentLang, 'apiKey')}
                </label>
                <input
                  type="password"
                  value={settings.apiKey}
                  onChange={(e) =>
                    setSettings({ ...settings, apiKey: e.target.value })
                  }
                  placeholder="sk-..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50"
                />
                <p className="text-[10px] text-slate-500">
                  {t(currentLang, 'apiKeyOptional')}
                </p>
              </div>
            )}

            <div className="space-y-1">
              <label className="flex items-center gap-2 text-xs font-medium text-slate-300">
                <Cpu size={14} />
                {t(currentLang, 'modelName')}
              </label>
              <input
                type="text"
                value={settings.modelName}
                onChange={(e) =>
                  setSettings({ ...settings, modelName: e.target.value })
                }
                placeholder={
                  settings.provider === 'google'
                    ? 'gemini-2.5-flash'
                    : 'llama3:latest'
                }
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50"
              />
              <p className="text-[10px] text-slate-500">
                {settings.provider === 'google'
                  ? t(currentLang, 'modelHintGoogle')
                  : t(currentLang, 'modelHintCustom')}
              </p>
            </div>

            {settings.provider === 'custom' && (
              <div className="space-y-1">
                <label className="flex items-center gap-2 text-xs font-medium text-slate-300">
                  <Server size={14} />
                  {t(currentLang, 'baseUrl')}
                </label>
                <input
                  type="text"
                  value={settings.baseUrl}
                  onChange={(e) =>
                    setSettings({ ...settings, baseUrl: e.target.value })
                  }
                  placeholder="http://localhost:11434/v1"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 font-mono"
                />
                <div className="bg-amber-950/30 border border-amber-900/50 rounded-lg p-3 flex gap-2 mt-2">
                  <AlertTriangle
                    className="text-amber-500 flex-shrink-0"
                    size={14}
                  />
                  <p className="text-[10px] text-amber-200/80 leading-relaxed">
                    {t(currentLang, 'corsWarning')}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-5 bg-slate-900 border-t border-slate-800 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            {t(currentLang, 'settingsCancel')}
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-900/20 flex items-center gap-2 transition-colors"
          >
            <Save size={16} />
            {t(currentLang, 'settingsSave')}
          </button>
        </div>
      </div>
    </div>
  )
}

export default SettingsModal
