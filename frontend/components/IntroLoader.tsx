'use client'

import { useEffect, useState } from 'react'

const LINES = [
  '> INITIALIZING TRENCHCOAT...',
  '> CONNECTING TO BIRDEYE DATA...',
  '> LOADING DEV HISTORY INDEX...',
  '> BUNDLE DETECTION READY...',
  '> ALL SYSTEMS OPERATIONAL.',
]

export default function IntroLoader({ onComplete }: { onComplete: () => void }) {
  const [visibleLines, setVisibleLines] = useState<number>(0)
  const [done, setDone] = useState(false)

  useEffect(() => {
    const interval = setInterval(() => {
      setVisibleLines(prev => {
        if (prev >= LINES.length - 1) {
          clearInterval(interval)
          setTimeout(() => {
            setDone(true)
            setTimeout(onComplete, 400)
          }, 800)
          return prev
        }
        return prev + 1
      })
    }, 600)
    return () => clearInterval(interval)
  }, [onComplete])

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 50,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#0a0a0a',
      color: '#f5f5f5',
      opacity: done ? 0 : 1,
      transition: 'opacity 400ms linear',
    }}>
      <div style={{
        width: 'min(720px, calc(100vw - 32px))',
        border: '1px solid #262626',
        background: '#171717',
        padding: '24px',
        fontFamily: 'monospace',
      }}>
        <p style={{
          margin: '0 0 16px',
          color: '#737373',
          fontSize: '12px',
          letterSpacing: '1px',
        }}>
          SYSTEM BOOT
        </p>
        <div style={{ display: 'grid', gap: '10px' }}>
          {LINES.slice(0, visibleLines + 1).map((line) => (
            <p
              key={line}
              style={{
                margin: 0,
                color: line.includes('OPERATIONAL') ? '#22c55e' : '#f5f5f5',
                fontSize: '13px',
                letterSpacing: '0.5px',
              }}
            >
              {line}
            </p>
          ))}
        </div>
      </div>
    </div>
  )
}
