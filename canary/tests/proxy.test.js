import test from 'node:test'
import assert from 'node:assert/strict'
import { createServer } from 'node:http'
import { apiMiddleware } from '../src/server/dev-api.js'

const listen = (server) => new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(`http://127.0.0.1:${server.address().port}`)))
const close = (server) => new Promise((resolve) => server.close(resolve))

test('local auth and API proxy hold credentials server-side and enforce production auth', async () => {
  let received
  const backend = createServer(async (req, res) => {
    let body = ''
    for await (const chunk of req) body += chunk
    received = { token: req.headers.authorization, url: req.url, body }
    if (req.url === '/api/events') {
      res.writeHead(200, { 'content-type': 'text/event-stream' })
      res.write('data: first\n\n')
      setTimeout(() => res.end('data: final\n\n'), 50)
    } else {
      res.setHeader('content-type', 'application/json')
      res.end('{"ok":true}')
    }
  })
  const dashboard = createServer((req, res) => apiMiddleware(req, res, () => { res.statusCode = 404; res.end() }))
  const previous = { ...process.env }
  try {
    process.env.CANARY_API_URL = await listen(backend)
    process.env.CANARY_API_TOKEN = 'server-only-test-token'
    process.env.AUTH_REQUIRED = 'false'
    process.env.NODE_ENV = 'development'
    const base = await listen(dashboard)
    assert.equal((await (await fetch(`${base}/api/auth/session`)).json()).authenticated, true)
    const result = await fetch(`${base}/api/projects?limit=2`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: '{"name":"local"}' })
    assert.deepEqual(await result.json(), { ok: true })
    assert.deepEqual(received, { token: 'Bearer server-only-test-token', url: '/api/projects?limit=2', body: '{"name":"local"}' })
    assert.equal((await fetch(`${base}/api/projects`, { headers: { origin: 'https://untrusted.example' } })).status, 403)
    const stream = await fetch(`${base}/api/events`)
    const reader = stream.body.getReader()
    const first = await reader.read()
    assert.match(new TextDecoder().decode(first.value), /data: first/)
    let tail = ''
    while (true) { const item = await reader.read(); if (item.done) break; tail += new TextDecoder().decode(item.value) }
    assert.match(tail, /data: final/)
    process.env.NODE_ENV = 'production'
    process.env.CANARY_DEV_BYPASS = 'true'
    assert.equal((await fetch(`${base}/api/projects`)).status, 401)
    assert.equal((await (await fetch(`${base}/api/auth/session`)).json()).authenticated, false)
  } finally {
    for (const key of ['CANARY_API_URL','CANARY_API_TOKEN','AUTH_REQUIRED','NODE_ENV','CANARY_DEV_BYPASS']) {
      if (previous[key] === undefined) delete process.env[key]
      else process.env[key] = previous[key]
    }
    await Promise.all([close(backend),close(dashboard)])
  }
})
