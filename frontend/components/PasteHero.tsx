'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function PasteHero() {
  const [input, setInput] = useState('')
  const [chain, setChain] = useState('solana')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = () => {
    const trimmed = input.trim()
    const SOLANA_CA = /^[1-9A-HJ-NP-Za-km-z]{32,50}$/
    const EVM_CA = /^0x[a-fA-F0-9]{40}$/
    if (!SOLANA_CA.test(trimmed) && !EVM_CA.test(trimmed)) {
      setError('INVALID CONTRACT ADDRESS')
      return
    }
    setError('')
    setLoading(true)
    router.push(`/dossier/${trimmed}?chain=${chain}`)
  }

  return (
    <div style={{ width: '100%', maxWidth: '800px' }}>
      <div className="paste-hero-controls" style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          placeholder="PASTE CONTRACT ADDRESS"
          style={{
            flex: 1,
            minWidth: 0,
            height: '52px',
            background: '#171717',
            border: error ? '1px solid #ef4444' : '1px solid #262626',
            color: '#f5f5f5',
            fontFamily: 'monospace',
            fontSize: '13px',
            padding: '0 16px',
            outline: 'none',
            letterSpacing: '0.5px',
          }}
        />
        <select
          className="paste-hero-select"
          value={chain}
          onChange={(e) => setChain(e.target.value)}
          style={{
            height: '52px',
            background: '#171717',
            border: '1px solid #262626',
            color: '#f5f5f5',
            fontFamily: 'monospace',
            fontSize: '13px',
            padding: '0 12px',
            outline: 'none',
            cursor: 'pointer',
          }}
        >
          <option value="solana">SOLANA</option>
          <option value="base">BASE</option>
          <option value="ethereum">ETHEREUM</option>
        </select>
        <button
          className="paste-hero-button"
          onClick={handleSubmit}
          disabled={loading}
          style={{
            height: '52px',
            background: loading ? '#262626' : '#f5f5f5',
            color: loading ? '#737373' : '#0a0a0a',
            fontFamily: 'monospace',
            fontWeight: 'bold',
            fontSize: '14px',
            padding: '0 36px',
            border: 'none',
            cursor: loading ? 'not-allowed' : 'pointer',
            letterSpacing: '2px',
            transition: 'all 0.1s ease',
            minWidth: '120px',
          }}
        >
          {loading ? 'RUNNING...' : 'RUN'}
        </button>
      </div>
      {error && (
        <p style={{
          color: '#ef4444',
          fontFamily: 'monospace',
          fontSize: '11px',
          marginTop: '6px',
          letterSpacing: '1px',
        }}>
          {error}
        </p>
      )}
      <style dangerouslySetInnerHTML={{ __html: `
        @media (max-width: 640px) {
          .paste-hero-controls {
            display: grid !important;
            grid-template-columns: 1fr;
            width: 100%;
          }

          .paste-hero-select,
          .paste-hero-button {
            width: 100%;
          }
        }
      ` }} />
    </div>
  )
}
