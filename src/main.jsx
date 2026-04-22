import { Component, StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import LandingPage from './pages/LandingPage.jsx'

function isLandingHash() {
  if (typeof window === 'undefined') return false
  return window.location.hash.replace(/^#\/?/, '') === 'landing'
}

function Router() {
  const [showLanding, setShowLanding] = useState(isLandingHash)

  useEffect(() => {
    const onHashChange = () => setShowLanding(isLandingHash())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  if (showLanding) {
    return (
      <LandingPage
        onEnterStudio={() => {
          window.location.hash = ''
          setShowLanding(false)
        }}
      />
    )
  }
  return <App />
}

class RootErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, errorMessage: '' }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error) {
    console.error('Draftelier root render failed:', error)
    this.setState({ errorMessage: error?.message || '' })
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children
    }

    const isDomMutationError = /removeChild|insertBefore/i.test(this.state.errorMessage)

    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#F6F2EA] px-6 text-center text-black">
        <p className="text-[11px] font-bold uppercase tracking-[0.28em]">Draftelier AI</p>
        <div className="mt-6 h-14 w-px animate-pulse bg-black" />
        <p className="mt-6 text-[10px] font-bold uppercase tracking-[0.28em] text-gray-500">
          Workspace Interrupted
        </p>
        <p className="mt-4 max-w-md text-sm leading-relaxed text-gray-600">
          {isDomMutationError
            ? '检测到浏览器翻译或插件改写了页面节点。请关闭自动翻译后刷新页面继续。'
            : '页面加载被打断，请手动刷新后继续。如果问题持续出现，我已经把自动刷新关掉了，这样就不会再反复跳页。'}
        </p>
        {this.state.errorMessage ? (
          <p className="mt-4 max-w-md break-words border border-black/10 bg-white px-4 py-3 text-[11px] leading-relaxed text-gray-500">
            {this.state.errorMessage}
          </p>
        ) : null}
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="mt-6 border border-black bg-black px-5 py-3 text-[10px] font-bold uppercase tracking-[0.2em] text-white transition-colors hover:bg-gray-800"
        >
          Refresh Page / 刷新页面
        </button>
      </div>
    )
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RootErrorBoundary>
      <Router />
    </RootErrorBoundary>
  </StrictMode>,
)
