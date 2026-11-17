import { v4 as uuidv4 } from 'uuid'

const history_to_message = (chat) => {
    return chat.map(x => ([
        { role: 'user', content: x.user },
        { role: 'agent', content: x.bot },
    ])).flat()
}

const service_data = {
    current_session: {},
    create_session_handler: (_ss, _) => { },
    change_session_handler: (_ss) => { },
    refresh_session_handler: () => { }
}

export class WritingSessionService {
    static async get(user, change: boolean = true) {
        const to_title = (item) => {
            const record = item.ChatRecords[0]
            return (record.History && record.History.length > 0) ? record.History[0].user : record.UserInput
        }

        const to_chat = (item) => {
            const record = item.ChatRecords[0]
            const h = record.History ? record.History : []
            return [...h, { user: record.UserInput, bot: record.Output }]
        }
        const response = await fetch(`/llm/writing/history?user=${user}`)
        if (response.ok) {
            const res = await response.json()
            if (res.data && res.data.length > 0) {
                const data = res.data.map(x => ({ id: x.ID, title: to_title(x), chat: to_chat(x), create: x.CreatedAt }))
                data.sort((a, b) => (a.create > b.create ? -1 : 1))
                change && WritingSessionService.change_session(data[0])
                return data
            }
        }
        return []
    }

    static async add_history(data) {
        const response = await fetch("/llm/writing", {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(data) 
          })
        console.log(data,'存储的值');
        return response
    }

    static async delete(sid) {
        return await fetch(`/llm/writing/deleteSession?sessionId=${sid}`, { method: 'DELETE' })
    }

    static add_session(refresh_sessions_handler) {
        service_data.create_session_handler(uuidv4(), refresh_sessions_handler)
    }

    static change_session(ss) {
        const message = history_to_message(ss.chat)
        ss.message = message
        service_data.change_session_handler(ss)
    }

    static on_change_session(fn) {
        service_data.change_session_handler = fn
    }

    static on_add_session(fn) {
        service_data.create_session_handler = fn
    }
}