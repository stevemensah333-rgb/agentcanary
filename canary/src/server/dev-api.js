import apiHandler from '../../api/[...path].js'
import authHandler from '../../api/auth/[...path].js'

export async function apiMiddleware(req, res, next) {
  if (!req.url?.startsWith('/api/')) return next()
  const url = new URL(req.url, 'http://localhost')
  req.query = Object.fromEntries(url.searchParams)
  res.status = (code) => { res.statusCode = code; return res }
  res.json = (body) => { res.setHeader('content-type', 'application/json'); res.end(JSON.stringify(body)); return res }
  res.send = (body) => { res.end(body); return res }
  res.redirect = (code, location) => { res.statusCode = code; res.setHeader('location', location); res.end() }
  try {
    if (!['GET', 'HEAD'].includes(req.method)) {
      const chunks = []
      let bytes = 0
      for await (const chunk of req) {
        bytes += chunk.length
        if (bytes > 1_000_000) return res.status(413).json({ detail: 'Request body too large.' })
        chunks.push(chunk)
      }
      req.body = bytes ? Buffer.concat(chunks).toString('utf8') : undefined
    }
    await (url.pathname.startsWith('/api/auth/') ? authHandler : apiHandler)(req, res)
  } catch {
    if (!res.headersSent) res.status(500).json({ detail: 'Dashboard API request failed.' })
    else res.end()
  }
}

export function developmentApi() {
  return {
    name: 'canary-development-api',
    configureServer(server) { server.middlewares.use(apiMiddleware) },
  }
}
