export default function Loading() {
  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0a0a',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'monospace',
    }}>
      <div style={{
        color: '#f5f5f5',
        fontSize: '14px',
        letterSpacing: '2px',
        marginBottom: '24px',
      }}>
        SCANNING...
      </div>
      <div style={{
        width: '200px',
        height: '2px',
        background: '#262626',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          height: '100%',
          width: '40%',
          background: '#f5f5f5',
          animation: 'scan 1.2s ease-in-out infinite',
        }} />
      </div>
      <div style={{
        color: '#737373',
        fontSize: '11px',
        letterSpacing: '1px',
        marginTop: '16px',
      }}>
        PULLING DEV HISTORY...
      </div>
      <style>{`
        @keyframes scan {
          0% { left: -40%; }
          100% { left: 100%; }
        }
      `}</style>
    </div>
  )
}
