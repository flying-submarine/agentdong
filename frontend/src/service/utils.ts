import { nextTick, ref, Ref } from 'vue'
import { useTokenStore } from "@/stores/token";
import { useRouter } from 'vue-router';
export interface TableRequest {
    page?: number
    rows?: number
    query?: any
}

export const scrollToBottom = async (chatArea: Ref<HTMLElement | null>, force: boolean = false) => {
    if (!chatArea.value) {
        console.error('chatArea element unexpect:', chatArea)
        return;
    }
    await nextTick()
    chatArea.value.scrollTop = chatArea.value.scrollHeight;
};


export const scrollToTop= async (chatArea: Ref<HTMLElement | null>, force: boolean = false) => {
  if (!chatArea.value) {
      console.error('chatArea element unexpect:', chatArea)
      return;
  }
  if (!force && chatArea.value.scrollHeight - chatArea.value.scrollTop > chatArea.value.clientHeight + 10) {
      return;
  }
  await nextTick()
  chatArea.value.scrollTop = 0;
};

export const storeData=(text, refe = [], ques = [])=>{
    const data = {
      text,
      refe: refe.length ? refe : null,
      ques: ques.length ? ques : null
    };
  
    return JSON.stringify(data);
}


export const retrieveData = (storedString)=>{
    // 替换字符串的前后双引号为单引号
    let newStr = storedString.replace(/^"|"$/g, "'");
    let data;
    try {
        data = JSON.parse(newStr); // 尝试解析 JSON 字符串
    } catch (e) {
        return { text: newStr, refe: [], ques: [] }; 
    }

    // 提取所需数据
    const text = data.text || "";
    const refe = data.refe || [];
    // const ques = Array.isArray(data.ques) ? data.ques.filter(i=>(i!=="null")): [];
    const ques = data.ques || [];
    const {updatedText,updatedReferences} = updateCitationsAndReferences(text,refe) 
    return { 
        text:updatedText,
        refe:updatedReferences, 
        ques 
    };
}

const updateCitationsAndReferences = (text, references) => {
    // 1. 校验入参格式
    if (typeof text !== 'string' || !Array.isArray(references) || references.some(ref => !ref.title || !ref.content)) {
      console.log("text 参数必须是字符串 / references 必须是包含 {title, content} 对象的数组");
      return {
        updatedText: text,
        updatedReferences: references
      };
    }
  
    // 2. 提取并记录引用顺序
    let citationMap = {};
    let citationOrder = [];
  
    text = text.replace(/\[<?citation (\d+)>?\]/g, function(match, number) {
        // 查找是否存在该 citation 对应的 reference
        if (!references.some(ref => ref.title.includes(`[${number}]`))) {
          return ''; // 如果找不到对应的 reference，删除该引用
        }
        
        if (!citationMap[number]) {
          citationMap[number] = citationOrder.length + 1; // 记录新的 citation 编号
          citationOrder.push(number); // 保留出现顺序
        }
        return match;
    });
  
    // 3. 按新顺序更新 citation，且将 [citation N] 替换为 **N**
    let updatedText = text.replace(/\[<?citation (\d+)>?\]/g, function(_, number) {
        return `[${citationMap[number]}]`;
    });
  
    // 4. 更新 references 数组中的编号和顺序，只替换编号
    let updatedReferences = citationOrder.map((oldNumber, index) => {
      // 找到旧的引用内容
      let oldReference = references.find(ref => ref.title.includes(`[${oldNumber}]`));
      if (!oldReference) {
        console.log(`找不到编号为 [${oldNumber}] 的引用`)
      }
      // 更新为新的编号，但保留其他数据不变
      return {
        ...oldReference,
        title: oldReference.title.replace(`[${oldNumber}]`, `[${index + 1}]`), // 仅替换编号部分
      };
    });
    console.log(text, "compareText",updatedText,"updateCitationsAndReferences",references,updatedReferences)
    // 返回更新后的文本和参考文献
    return {
      updatedText,
      updatedReferences
    };
};
  
export const upload_req = async (url: string, file, process) => {
    return new Promise<any>((resolve, reject) => {
        if (!file) {
            console.error('file invalid')
            reject()
        }
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                process && process(percentComplete)
            }
        }

        xhr.onload = () => {
            if (xhr.status != 200) {
                reject(xhr.status)
            }
            const res = JSON.parse(xhr.response)
            resolve({ process: 100, data: res, code: xhr.status })
        }

        xhr.onerror = reject;

        const formData = new FormData();
        formData.append('file', file);
        xhr.send(formData);
    })
}


export const get_local_file = async () => {
    const el = document.createElement('input')
    el.type = 'file'
    el.click()

    return new Promise((resolve, _) => {
        el.addEventListener('change', _ => (resolve(el.files)))
    })
}

export interface StreamRequest {
    url: string,
    data: any,
}

// 用于处理流式请求返回的数据，使每一块的数据按照完整的json返回
export const json_chunk_handler = async function* (data) {
    let buffer = ''
    for await (let chunk of data) {
        buffer += chunk
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
}


// 用于流式的数据请求
// const data = {
//     input: "Who is the fastest people in the world?",
//     user: "guest",
//     stream: true,
//     increase: true
// }
// const response = await stream_req({ url: '/llm/chat', data })
// for await (let data of response) {
//     console.log('read:', data)
// }
export const stream_req = async (req: StreamRequest) => {
    const response = await serviceFetch(req.url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(req.data)
    });
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    return (async function* () {
        while (true) {
            const { done, value } = await reader.read()
            if (done) break
            yield decoder.decode(value);
        }
    })()
}


export const get_chunk_data = async (url, start, end) => {
    const headers = { 'Range': `bytes=${start}-${end}` }
    const response = await fetch(url, { headers })
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    const { done, value } = await reader.read()
    return decoder.decode(value);
}

export const get_content_length = async (url, buffer_size = 10240) => {
    const response = await fetch(url, { method: 'HEAD' })
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }

    const len = response.headers.get('Content-Length');
    const file_length = len ? parseInt(len) : 0
    // const chunks = Math.floor(file_length / buffer_size) + 1
    return file_length
}

export const lazy_load_text = async (url) => {
    const buffer_size = 10240

    const ctx = { buffer: '', bindex: 0, data_buffer: [], total: -1 }


    const file_length = await get_content_length(url, buffer_size)
    const load_data = async () => {
        const bstart = ctx.bindex * buffer_size
        const bend = (++ctx.bindex) * buffer_size - 1
        if (bend > file_length + buffer_size) {
            return true
        }
        ctx.buffer += await get_chunk_data(url, bstart, bend)
        const content = ctx.buffer.split('\n')
        ctx.buffer = content.pop()
        ctx.data_buffer = [...ctx.data_buffer, ...content]
        return false
    }


    return async (page, rows, header = true) => {
        const header_offset = header ? 1 : 0
        const start = page * rows + (page != 0 ? header_offset : 0);
        const end = start + rows + (page == 0 ? header_offset : 0);
        let load_flag = false
        if (end > ctx.data_buffer.length) {
            load_flag = await load_data()
        }

        // const total = Math.ceil(ctx.data_buffer.length * file_length / buffer_size) + 1
        const total = load_flag ? ctx.data_buffer.length : ctx.data_buffer.length + 1

        return { data: ctx.data_buffer.slice(start, end) ?? [], total }
    }
}

export const serviceFetch = async (url, params={})=>{
  const tokenStore = useTokenStore();
  const res = await fetch(url, {
    ...params, 
    headers: {
      ...params.headers,
      Authorization: "Bearer "+tokenStore.token
    }
  });
  if(res.status===401) {
    window.location.href = '/login'
    return Promise.reject();
  }
  return res;
}


export const calcNumber = (text)=>{
  const strText = text.replace(/[*_`~\[\]!#\-\.\(\)]/g, '');
  const words = strText.split(' ');
  return words? words.length:0;
}