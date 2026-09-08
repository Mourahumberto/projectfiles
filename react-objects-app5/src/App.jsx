import { useState } from 'react'
import { Tabs } from './components/Tabs'
import { LocalView } from './components/LocalView'
import { S3View } from './components/S3View'
import './App.css'

const TABS = [
  { id: 'local', label: 'Local' },
  { id: 's3', label: 'S3' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('local')

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <p className="app__eyebrow">object store</p>
          <h1>Objects Manager</h1>
        </div>
      </header>

      <Tabs tabs={TABS} active={activeTab} onChange={setActiveTab} />

      {activeTab === 'local' ? <LocalView /> : <S3View />}
    </div>
  )
}
