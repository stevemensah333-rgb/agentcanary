import { createServer } from 'node:http'
import { readFile } from 'node:fs/promises'
import { resolve, extname, sep } from 'node:path'
import { apiMiddleware } from './dev-api.js'

const root = resolve('dist')
const types = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.mp4': 'video/mp4' }
createServer((req, res) => {
  apiMiddleware(req, res, async () => {
    try {
      const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname)
      const path = resolve(root, `.${pathname}`)
      if (path !== root && !path.startsWith(root + sep)) { res.writeHead(400); return res.end() }
      let content
      let extension = extname(path)
      try { content = await readFile(path) } catch {
        if (extension) { res.writeHead(404); return res.end() }
        content = await readFile(resolve(root, 'index.html'))
        extension = '.html'
      }
      res.writeHead(200, { 'content-type': types[extension] || 'application/octet-stream' })
      res.end(req.method === 'HEAD' ? undefined : content)
    } catch { res.writeHead(500); res.end() }
  }).catch(() => { if (!res.headersSent) res.writeHead(500); res.end() })
}).listen(Number(process.env.PORT || 8000), process.env.HOST || '127.0.0.1')
