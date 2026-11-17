
export type Fetch = typeof fetch

export interface ErrorResponse {
    error: string
}

const fetchWithHeaders = async (
    fetch: Fetch,
    url: string,
    options: RequestInit = {},
): Promise<Response> => {
    const defaultHeaders = {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        //   'User-Agent': `ollama-js/${version} (${getPlatform()})`,
    }

    if (!options.headers) {
        options.headers = {}
    }

    options.headers = {
        ...defaultHeaders,
        ...options.headers,
    }

    return fetch(url, options)
}

const checkOk = async (response: Response): Promise<void> => {
    if (!response.ok) {
        let message = `Error ${response.status}: ${response.statusText}`
        let errorData = null

        if (response.headers.get('content-type')?.includes('application/json')) {
            try {
                errorData = (await response.json())
                message = errorData.error || message
            } catch (error) {
                console.log('Failed to parse error response as JSON')
            }
        } else {
            try {
                console.log('Getting text from response')
                const textResponse = await response.text()
                message = textResponse || message
            } catch (error) {
                console.log('Failed to get text from error response')
            }
        }

        // throw new ResponseError(message, response.status)
    }
}

export const post = async (
    fetch: Fetch,
    host: string,
    data?: Record<string, unknown> | BodyInit,
    options?: { signal: AbortSignal },
): Promise<Response> => {
    const isRecord = (input: any): input is Record<string, unknown> => {
        return input !== null && typeof input === 'object' && !Array.isArray(input)
    }

    const formattedData = isRecord(data) ? JSON.stringify(data) : data

    const response = await fetchWithHeaders(fetch, host, {
        method: 'POST',
        body: formattedData,
        signal: options?.signal,
    })

    await checkOk(response)

    return response
}

export interface Config {
    host: string
    fetch?: Fetch
    proxy?: boolean
}


export const parseJSON = async function* <T = unknown>(
    itr: ReadableStream<Uint8Array>,
): AsyncGenerator<T> {
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    const reader = itr.getReader()

    while (true) {
        const { done, value: chunk } = await reader.read()

        if (done) {
            break
        }

        buffer += decoder.decode(chunk)

        const parts = buffer.split('\0')

        buffer = parts.pop() ?? ''
        for (const part of parts) {
            try {
                yield JSON.parse(part)
            } catch (error) {
                console.warn('invalid json: ', part)
            }
        }
    }

    for (const part of buffer.split('\0').filter((p) => p !== '')) {
        try {
            yield JSON.parse(part)
        } catch (error) {
            console.warn('invalid json: ', part)
        }
    }
}

export interface Options {
    numa: boolean
    num_ctx: number
    num_batch: number
    num_gpu: number
    main_gpu: number
    low_vram: boolean
    f16_kv: boolean
    logits_all: boolean
    vocab_only: boolean
    use_mmap: boolean
    use_mlock: boolean
    embedding_only: boolean
    num_thread: number

    // Runtime options
    num_keep: number
    seed: number
    num_predict: number
    top_k: number
    top_p: number
    tfs_z: number
    typical_p: number
    repeat_last_n: number
    temperature: number
    repeat_penalty: number
    presence_penalty: number
    frequency_penalty: number
    mirostat: number
    mirostat_tau: number
    mirostat_eta: number
    penalize_newline: boolean
    stop: string[]
}


export interface Message {
    role: string
    content?: string
    images?: Uint8Array[] | string[]
    news_summary?: []
    type?: string
    flag?: string
    refrence?: string
    details?: any
    prompt_aug?: boolean
}

// export interface ChatRequest {
//     model: string
//     messages?: Message[]
//     stream?: boolean
//     format?: string
//     keep_alive?: string | number

//     options?: Partial<Options>
// }

export interface ChatRequest {
    input: string
    user: string
    stream?: boolean
    increase: boolean
    doc_id?: string
    session?: string
    sessionId?: string
    history?: Object[]
}


export interface writingRequest {
    data: {
        input: string
        userId: string
        prompt_aug?: boolean
    }
    stream?: boolean
}

export interface longReportSummarizationRequest {
    input: string
    user: string
    stream?: boolean
    doc_id?: string
    session?: string
    sessionId?: string
    history?: Object[]
    prompt_aug?: boolean
}

export interface PullRequest {
    model: string
    insecure?: boolean
    stream?: boolean
}

export interface ProgressResponse {
    status: string
    digest: string
    total: number
    completed: number
}

export interface uploadRequest {
    file: File
    user: string
    prompt_aug?: boolean
}

// export interface ChatResponse {
//     model: string
//     created_at: Date
//     message: Message
//     done: boolean
//     done_reason: string
//     total_duration: number
//     load_duration: number
//     prompt_eval_count: number
//     prompt_eval_duration: number
//     eval_count: number
//     eval_duration: number
// }
export interface ChatResponse {
    output: string
}

export class ChatClient {
    protected readonly fetch: Fetch
    protected readonly config: Config
    private abortController: AbortController

    constructor(config?: Partial<Config>) {
        this.config = {
            host: '',
        }
        if (!config?.proxy) {
            // this.config.host = 'http://11.163.70.215:9004'
        }

        this.fetch = fetch
        if (config?.fetch != null) {
            this.fetch = config.fetch
        }

        this.abortController = new AbortController()
    }

    protected async processStreamableRequest<T extends object>(
        endpoint: string,
        request: { stream?: boolean } & Record<string, any>,
    ): Promise<T | AsyncGenerator<T>> {
        request.stream = request.stream ?? false
        const response = await post(
            this.fetch,
            `${this.config.host}/llm/${endpoint}`,
            {
                ...request,
            },
            { signal: this.abortController.signal },
        )

        if (!response.body) {
            throw new Error('Missing body')
        }


        const itr = parseJSON<T | ErrorResponse>(response.body)
        if (request.stream) {

            return (async function* () {
                for await (const message of itr) {
                    if ('error' in message) {
                        throw new Error(message.error)
                    }
                    if ((message as any).status === 'truncated') {
                        throw new Error('status truncated')
                    }
                    yield message
                    // console.log(message)
                    // message will be done in the case of chat and generate
                    // message will be success in the case of a progress response (pull, push, create)
                    if ((message as any).done || (message as any).status === 'stop') {
                        return
                    }
                }
                // throw new Error('Did not receive done or success response in stream.')
            })()
        } else {
            const message = await itr.next()
            // if (!message.value.done && (message.value as any).status !== 'success') {
            //     throw new Error('Expected a completed response.')
            // }
            console.log(message.value)
            if (message.value.code !== 200) {
                throw new Error('Expected a completed response.')
            }
            // return [message.value.data]
            return message.value
        }
    }
    async chat(request: ChatRequest): Promise<ChatResponse | AsyncGenerator<ChatResponse>> {
        if (request.input) {
            // for (const message of request.input) {
            //     if (message.images) {
            //         message.images = await Promise.all(
            //             message.images.map(this.encodeImage.bind(this)),
            //         )
            //     }
            // }
        }
        return this.processStreamableRequest<ChatResponse>('chat', request)
    }

    async file_qa(request: ChatRequest): Promise<ChatResponse | AsyncGenerator<ChatResponse>> {
        if (request.input) {
            // for (const message of request.input) {
            //     if (message.images) {
            //         message.images = await Promise.all(
            //             message.images.map(this.encodeImage.bind(this)),
            //         )
            //     }
            // }
        }
        return this.processStreamableRequest<ChatResponse>(`docs/${request.doc_id}/chat`, request)
    }

    async writing(request: writingRequest): Promise<ChatResponse | AsyncGenerator<ChatResponse>> {
        return this.processStreamableRequestWriting<ChatResponse>(`/writing/psllm/odw/directWriting/write`, request)
    }

    protected async processStreamableRequestWriting<T extends object>(
        endpoint: string,
        request: { stream?: boolean } & Record<string, any>,
    ): Promise<any> {
        request.stream = request.stream ?? false
        const response = await post(
            this.fetch,
            `${endpoint}`,
            {
                ...request,
            },
            { signal: this.abortController.signal },
        )

        // if (!response.body) {
        //     throw new Error('Missing body')
        // }



        if (request.stream) {
            const itr = parseJSON<T | ErrorResponse>(response.body)
            return (async function* () {
                for await (const message of itr) {
                    if ('error' in message) {
                        throw new Error(message.error)
                    }
                    yield message
                    // message will be done in the case of chat and generate
                    // message will be success in the case of a progress response (pull, push, create)
                    if ((message as any).done || (message as any).status === 'stop') {
                        return
                    }
                }
                // throw new Error('Did not receive done or success response in stream.')
            })()
        } else {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const textData = await response.text(); // 获取纯文本数据
            console.log(textData, '获取文本');
            const chatResponse: ChatResponse = { output: textData };
            // return [message.value.data]
            return chatResponse;
        }
    }

    async longReportSummarization(request: longReportSummarizationRequest): Promise<ChatResponse | AsyncGenerator<ChatResponse>> {
        if (request.input) {
            // for (const message of request.input) {
            //     if (message.images) {
            //         message.images = await Promise.all(
            //             message.images.map(this.encodeImage.bind(this)),
            //         )
            //     }
            // }
        }
        return this.processStreamableRequestLongReportSummarization<ChatResponse>(`/longReportSummarization/llm/docs/${request.doc_id}/chat`, request)
    }

    protected async processStreamableRequestLongReportSummarization<T extends object>(
        endpoint: string,
        request: { stream?: boolean } & Record<string, any>,
    ): Promise<T | AsyncGenerator<T>> {
        request.stream = request.stream ?? false
        const response = await post(
            this.fetch,
            `${endpoint}`,
            {
                ...request,
            },
            { signal: this.abortController.signal },
        )

        if (!response.body) {
            throw new Error('Missing body')
        }


        const itr = parseJSON<T | ErrorResponse>(response.body)
        if (request.stream) {

            return (async function* () {
                for await (const message of itr) {
                    if ('error' in message) {
                        throw new Error(message.error)
                    }
                    yield message

                    // message will be done in the case of chat and generate
                    // message will be success in the case of a progress response (pull, push, create)
                    if ((message as any).done || (message as any).status === 'stop') {
                        return
                    }
                }
                // throw new Error('Did not receive done or success response in stream.')
            })()
        } else {
            const message = await itr.next()
            // if (!message.value.done && (message.value as any).status !== 'success') {
            //     throw new Error('Expected a completed response.')
            // }
            console.log(message.value)
            if (message.value.code !== 200) {
                throw new Error('Expected a completed response.')
            }
            // return [message.value.data]
            return message.value
        }
    }

    async upload(request: uploadRequest): Promise<ChatResponse | AsyncGenerator<ChatResponse>> {

        return this.processStreamableRequestUpload<ChatResponse>(request)
    }

    protected async processStreamableRequestUpload<T extends object>(
        request: Record<string, any>,
    ): Promise<T | AsyncGenerator<T>> {
        request.stream = request.stream ?? false
        // const response = await post(
        //     this.fetch,
        //     `${endpoint}`,
        //     {
        //         ...request,
        //     },
        //     { signal: this.abortController.signal },
        // )
        let formData = new FormData()
        formData.append('file', request.file);
        formData.append('prompt_aug', request.prompt_aug);
        const response = await fetch(`/longReportSummarization/llm/docs?user=${request.user}`, {
            method: 'POST',
            body: formData,
        });
        if (!response.body) {
            throw new Error('Missing body')
        }


        const itr = parseJSON<T | ErrorResponse>(response.body)
        // if (request.stream) {

        return (async function* () {
            for await (const message of itr) {
                if ('error' in message) {
                    throw new Error(message.error)
                }
                yield message
                // console.log(message)
                // message will be done in the case of chat and generate
                // message will be success in the case of a progress response (pull, push, create)
                if ((message as any).done || (message as any).status === 'stop') {
                    return
                }
            }
            // throw new Error('Did not receive done or success response in stream.')
        })()
    }


    async pull(
        request: PullRequest,
    ): Promise<ProgressResponse | AsyncGenerator<ProgressResponse>> {
        return this.processStreamableRequest<ProgressResponse>('pull', {
            name: request.model,
            stream: request.stream,
            insecure: request.insecure,
        })
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }


    async fetchChatGPT() {
        try {
            const response = await fetch('/llm/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    input: "Who is the fastest people in the world?",
                    user: "guest",
                    stream: true,
                    increase: true
                })
            });
            const data = await response.body;
            // return data.choices[0].text.trim();
            return parseJSON<ChatResponse>(data)
        } catch (error) {
            console.error('Error:', error);
            return 'An error occurred. Please try again.';
        }
    }

    async create_session() {
        return await fetch('/chat/session', { method: 'POST' })
    }

    static async fetchStream() {
        // const response = await fetch('http://11.163.70.215:9004/stream');
        const response = await fetch('/llm/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input: "Who is the fastest people in the world?",
                user: "guest",
                stream: true,
                increase: true
            })
        });
        const reader = response.body?.getReader();

        const decoder = new TextDecoder();
        // const contentDiv = document.getElementById('content');

        function readChunk() {
            reader?.read().then(({ done, value }) => {
                if (done) {
                    console.log("Stream complete");
                    return;
                }

                const chunk = decoder.decode(value, { stream: true });
                // contentDiv.innerHTML += chunk.replace(/\n/g, '<br>');  // 将新内容添加到页面
                console.log('read stream message:', chunk)
                readChunk();
            }).catch(error => {
                console.error("Error reading stream:", error);
            });
        }

        readChunk();
    }


    // {
    //     const inputField = document.getElementById('user-input');
    //     const userMessage = inputField.value;
    //     if (!userMessage) return;

    //     appendMessage('You', userMessage);
    //     inputField.value = '';

    //     const response = await fetchChatGPT(userMessage);

    //     appendMessage('ChatGPT', response);
    // }

}