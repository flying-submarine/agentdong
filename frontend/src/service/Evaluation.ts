import { upload_req, TableRequest } from './utils'




const table_filter = (data = [], search) => {
    const column = search?.column?.label ?? ''
    if (!column) {
        return data
    }

    const kw = search?.keywords
    if (!kw) {
        return data
    }
    return data.filter(x => ((x[column] + '').indexOf(kw) > -1))
}

export class EvaluationService {
    static async add_data(data, process) {
        return await upload_req(`/llm/evaluation/upload?user=${data.user}&type=${data.type}&name=${data.name}`, data.file, process)
    }

    static async get_data(req: TableRequest): Promise<any> {
        const response = await fetch(`/llm/evaluation/`)

        if (!response.ok) {
            return { items: [], total: 0 }
        }

        const result = await response.json()
        let data = result.data.map(x => ({ name: x.FileName, details: x.DataSetDetails, type: x.FileType, id: x.ID, time: x.CreatedAt, user: x.User }))
        if (req.query && req.query['type'] && req.query['type'].length > 0) {
            data = data.filter(x => (req.query['type'].indexOf(x.type) == 0))
        }

        return new Promise((resolve, reject) => {
            const start = req?.page * req?.rows;
            const end = start + req?.rows;
            resolve({ items: data.slice(start, end), total: data.length })
        })
    }

    static async get_preview_data(data, req: TableRequest) {
        const start = req?.page * req?.rows;
        const end = start + req?.rows;

        const get_gt = (x)=>{
            if(x.gt){
                return x.gt
            }
            return (x?.gt ?? {}).answer ? x.gt.answer : x.gt
        }
        const items = data.details.map((x, i) => ({ id: i + 1, input: x.input, gt: get_gt(x) }))
        return new Promise((resolve, reject) => {
            resolve({ items: items.slice(start, end), total: items.length })
        })
    }

    static async delete_data(id) {
        return await fetch(`/llm/evaluation/${id}`, { method: 'DELETE' })
    }

    static async delete_evaluation_result(id, taskType) {
        const response = await fetch(`/llm/evaluation/task/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id,
                taskType,
            })
        })
        return response
    }

    static async add_evaluation(data) {
        const response = await fetch(`/llm/evaluation/task`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user: data.user,
                datasetId: data.id,
                taskType: data.type,
                promptAug: data.promptAug,
            })
        })

        return response
    }

    static async get_result(req) {
        const response = await fetch(`/llm/evaluation/task?taskType=${req?.query?.taskType}`)
        if (!response.ok) {
            return { items: [], total: 0 }
        }
        const start = req?.page * req?.rows;
        const end = start + req?.rows;
        const res = await response.json()

        const sort = req?.query?.sort ?? {};
        sort.sortField && sort.sortOrder && res.data.sort((a, b) => {
            const ak = a[sort.sortField]
            const bk = b[sort.sortField]
            if (ak === 'NA') return 1
            if (bk === 'NA') return -1
            return ak > bk ? sort.sortOrder : sort.sortOrder * -1
        })
        const data = table_filter(res.data, req?.query?.search)
        const columns = data.length > 0 ? Object.keys(data[0]).filter(x => (x.indexOf('Evaluation') == -1)) : []
        return { items: data.slice(start, end), total: data.length, columns }
    }

    static async get_preview_result(req: TableRequest) {
        const item = req?.query ?? {}
        const dk = Object.keys(item).filter(k => (k.indexOf('Evaluation') != -1))
        const details = dk.length > 0 ? item[dk[0]] : []
        const columns = details.length > 0 ? Object.keys(details[0]) : []

        return new Promise((resolve, reject) => {
            const start = req?.page * req?.rows;
            const end = start + req?.rows;
            resolve({ items: details.slice(start, end), total: details.length, columns })
        })
    }


    static async get_data_type() {
        const dataset_type_options = [
            { name: 'News' },
            { name: 'Chat with RAG' },
            { name: 'Long Report Summarization/S' },
            { name: 'Long Report Summarization/QA' },
            { name: 'Writting' },
            { name: 'CopilotWritting' },
            { name: 'TableQA' },
            { name: 'MultipleTableQA' },
        ]
        return new Promise((resolve, reject) => {
            resolve(dataset_type_options)
        })
    }

}