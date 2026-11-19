/**
 * 统一的中台问答服务 —— 把所有对话页接到线上 agentdong.com 的 /api/agt/ask_graph。
 *
 * 线上接口契约（POST /api/agt/ask_graph）：
 *   body: { question: string, session_id: string, role?: string }
 *   resp: { question, session_id, status, answer, refused, sources[], confidence, search_rounds, role }
 *     - status: "done" | "waiting_confirm"
 *     - refused: true 表示拒答
 *     - sources: 来源块 id 数组
 *
 * dev 环境由 vite.config.mjs 的 /api 代理转发到 https://agentdong.com；
 * 生产环境由同域 Nginx 转发（见 README）。
 */

export interface AskGraphResult {
  question: string
  session_id: string
  status: 'done' | 'waiting_confirm'
  answer: string
  refused: boolean
  sources: string[]
  confidence: number
  search_rounds: number
  role?: string | null
}

/** 每个访客一个稳定的 session：多轮记忆(MemorySaver) + 限流(每分钟 10 次)都按它分。 */
export function getDemoSessionId(): string {
  const KEY = 'agt_session_id'
  let sid = ''
  try {
    sid = localStorage.getItem(KEY) || ''
  } catch (_) { /* 无痕模式等场景 localStorage 不可用 */ }
  if (!sid) {
    const rand = Math.random().toString(36).slice(2, 10)
    sid = `web-${Date.now().toString(36)}-${rand}`
    try { localStorage.setItem(KEY, sid) } catch (_) { /* ignore */ }
  }
  return sid
}

/**
 * 调 /api/agt/ask_graph，一次 POST 返回整段 JSON（非流式）。
 * 各页面把它包装成 async iterator，以便复用现有 `for await` 的渲染循环。
 */
export async function askGraph(
  question: string,
  sessionId: string = getDemoSessionId(),
): Promise<AskGraphResult | null> {
  try {
    const res = await fetch('/api/agt/ask_graph', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, session_id: sessionId }),
    })
    if (res.status === 429) {
      return {
        question, session_id: sessionId, status: 'done',
        answer: '问得太快了（演示站限流：每分钟 10 次），等几秒再试。',
        refused: false, sources: [], confidence: 0, search_rounds: 0,
      }
    }
    if (!res.ok) return null
    return await res.json() as AskGraphResult
  } catch (error) {
    console.error('[askGraph] 请求失败:', error)
    return null
  }
}

/** 把结构化结果拼成正文：拒答标注 + 来源 + 置信度；waiting_confirm 给友好提示。 */
export function formatAskGraphAnswer(res: AskGraphResult): string {
  if (res.status === 'waiting_confirm') {
    return '这个请求要删文档，演示站不处理删库操作。'
  }
  let text = res.answer || ''
  if (res.refused) {
    text = '（已拒答）' + text
  } else if (res.sources && res.sources.length) {
    text += '\n\n来源：' + res.sources.join('、') + '（置信度 ' + res.confidence + '）'
  }
  return text
}

/** 失败兜底文案 */
export const ASK_GRAPH_FALLBACK = '请求失败，后端没响应，稍后再试。'

/**
 * 把 askGraph 包装成 async generator，产出 { output } —— 直接喂给原页面的
 * `for await (part of response) { currentOutput += part.output }` 渲染循环，
 * 这样各对话页只改「数据从哪来」，不用动既有 UI / 会话 / 滚动逻辑。
 */
export async function* askGraphStream(question: string): AsyncGenerator<{ output: string }> {
  const res = await askGraph(question)
  yield { output: res ? formatAskGraphAnswer(res) : ASK_GRAPH_FALLBACK }
}

