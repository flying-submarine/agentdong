import { v4 as uuidv4 } from 'uuid'
import { serviceFetch } from '@/service/utils';

const history_to_message = (chat: any[]) => {
    return chat.map((x: { user: any; bot: any;feedbackId:any; }) => {
        return [
            { role: 'user', content: x.user },
            { role: 'agent', content: x.bot,feedbackId: x?.feedbackId},
        ]
    }).flat()
}

const service_data = {
    current_session: {},
    create_session_handler: (_ss: any, _: any) => { },
    change_session_handler: (_ss: any) => { },
    refresh_session_handler: () => { }
}

export class RagSessionService {
    static async get(_: string, change=true) {
        const to_title = (item: { ChatRecords: any[]; }) => {
            const record = item.ChatRecords[0]
            return (record.History && record.History.length > 0) ? record.History[0].user : record.UserInput
        }

        const to_chat = (item: { ChatRecords: any[]; }) => {
            const record = item.ChatRecords[0]
            const h = record.History ? record.History : []
            return [...h, { user: record.UserInput, bot: record.Output,feedbackId:record.FeedbackId }]
        }
        const response = await serviceFetch(`/gpt/llm/rag/history`,{})
        if (response.ok) {
            const res = await response.json()
            if (res.data && res.data.length > 0) {
                let newData = res.data
                const data = newData.map((x: { ID: any; CreatedAt: any; }) => ({ 
                    id: x.ID, 
                    title: to_title(x), 
                    chat: to_chat(x), 
                    create: x.CreatedAt 
                }))
                data.sort((a: { create: number; }, b: { create: number; }) => (a.create > b.create ? -1 : 1))
                change && RagSessionService.change_session(data[0])
                return data
            }
        }
        return []
    }

    static async getFbackList(sid) {
        const response = await serviceFetch(`/gpt/llm/feedback/list?sessionId=${sid}`,{})
        if (response.ok) {
            const res = await response.json()
            if (res.data && res.data.length > 0) {
                return res.data
            }
        }
        return []
    }

    static async chat(url: string, param: { input: any; sessionId: string; history: any[]; stream: boolean; increase: boolean; feedbackId:string}) {
        try {
            const response = await serviceFetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(param),
            });
    
            // 检查响应是否成功
            if (!response.ok) {
                // throw new Error(`HTTP error! status: ${response.status}`);
            }
    
            // 定义一个生成器函数来解析 JSON 数据流
            const parseJSON = async function* (itr: ReadableStream<Uint8Array>) {
                const decoder = new TextDecoder('utf-8');
                let buffer = '';
                const reader = itr.getReader();
    
                while (true) {
                    const { done, value: chunk } = await reader.read();
    
                    if (done) {
                        break;
                    }
    
                    buffer += decoder.decode(chunk);
    
                    // 将缓冲区中的数据按 '\0' 分割，并处理每个 JSON 部分
                    const parts = buffer.split('\0');
    
                    // 最后一个部分可能不完整，将其保留到下一个循环
                    buffer = parts.pop() ?? '';
    
                    for (const part of parts) {
                        try {
                            yield JSON.parse(part);
                        } catch (error) {
                            console.warn('Invalid JSON: ', part);
                        }
                    }
                }
    
                // 处理剩余的未解析数据
                for (const part of buffer.split('\0').filter((p) => p !== '')) {
                    try {
                        yield JSON.parse(part);
                    } catch (error) {
                        console.warn('Invalid JSON: ', part);
                    }
                }
            };
            // 使用生成器解析响应体
            const itr = parseJSON(response.body);
            
            // 返回一个异步迭代器，供外部消费
            return (async function* () {
                for await (const message of itr) {
                    if ('error' in message) {
                        yield { output: message.error,status:"generating"} 
                    }
                    yield message;
    
                    // 如果流结束或状态为 'stop'，则停止迭代
                    if (message.done || message.status === 'stop') {
                        return;
                    }
                }
                // 如果没有收到 'done' 或 'stop' 的响应，抛出错误
                // throw new Error('Did not receive done or stop response in stream.');
            })();
    
        } catch (error) {
            console.error('Error in chat method:', error);
            // throw error; // 向调用者抛出错误
        }
    }

    static async delete(sid: any) {
        return await serviceFetch(`/gpt/llm/chat/deleteSession?sessionId=${sid}`, { method: 'DELETE' })
    }

    static add_session(refresh_sessions_handler: () => void) {
        service_data.create_session_handler(uuidv4(), refresh_sessions_handler)
    }

    static change_session(ss: { chat: any; message: any; feedbackId:any}) {
        const message = history_to_message(ss.chat)
        ss.message = message
        service_data.change_session_handler(ss)
    }

    static on_change_session(fn: { (ss: any): void; (_ss: any): void; }) {
        service_data.change_session_handler = fn
    }

    static on_add_session(fn: { (sid: any, fn: any): void; (_ss: any, _: any): void; }) {
        service_data.create_session_handler = fn
    }
}