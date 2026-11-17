import { TableRequest } from './utils'
const menu_items = [
    {
        label: 'Athltics_Men_40m_Hurdles',
        items: [
            {
                label: 'Athltics_Men_40m_Hurdles',
                items: [
                    {
                        label: 'Athltics_Men_40m_Hurdles',
                    },
                    {
                        label: 'Athltics_Men_40m_Hurdles',
                    }
                ]
            },
            {
                label: 'Athltics_Men_40m_Hurdles',
                items: [
                    {
                        label: 'Athltics_Men_40m_Hurdles',
                    }
                ]
            }
        ]
    },
    {
        label: 'Athltics_Men_40m_Hurdles',
        items: [
            {
                label: 'Athltics_Men_40m_Hurdles',
            },
            {
                label: 'Athltics_Men_40m_Hurdles',
            },
            {
                label: 'Athltics_Men_40m_Hurdles',
            }
        ]
    }
];

const data = Array.from({ length: 100 }, (_, i) => ({
    Year: ` ${2015 + i % 5}`,
    Olympic_Country: `Olympic_Country ${20 + (i % 10)}`,
    Olympic_City: `Olympic_City ${i + 1}`,
    Name: `Name ${i + 1}`,
    General: `General ${i + 1}`,
    Injuries: `Injuries ${i + 1}`,
}));

export class TableQAService {
    static async get_table_data(req: TableRequest): Promise<any> {
        // const response = await fetch()
        return new Promise((resolve, reject) => {
            const start = req?.page * req?.rows;
            const end = start + req?.rows;
            resolve({ items: data.slice(start, end), total: data.length })
        })
    }

    static async delete_menu_item(id): Promise<any> {
        const response = await fetch(`/llm/tableqa/${id}`, { method: 'DELETE' })
        if (!response.ok) {
            return []
        }
        const res = await response.json()
        console.log(res)
    }

    static async get_menu_items(): Promise<any> {
        const response = await fetch(`/llm/tableqa`)
        const data = [
            { title: '100_meters_men', input: 'What is bolt\'s best results in men\'s 100 meters', url: '/csv/100_meters_men.csv' },
            { title: '100_meters_breaststroke_men', input: 'who is the best palyer in this event', url: '/csv/100_meters_breaststroke_men.csv' },
            { title: 'athlete_events', input: 'Who has won the most gold medals', url: '/csv/athlete_events.csv' },
            {
                title: 'diving_10m_men', input: '', urls: [
                    { title: 'Diving_European_Championships', url: "/csv/Diving_European_Championships.csv", },
                    { title: 'Diving_Olympic_Games', input: '', url: "/csv/Diving_Olympic_Games.csv", },
                    { title: 'Diving_World_Championships', input: '', url: "/csv/Diving_World_Championships.csv", },
                    { title: 'Diving_World_Cup', input: '', url: "/csv/Diving_World_Cup.csv", },
                    { title: 'Diving_World_Series', input: '', url: "/csv/Diving_World_Series.csv", },
                ]
            },
        ]
        if (!response.ok) {
            return data
        }
        const res = await response.json()
        const server_data = (res?.data ?? []).map(x => ({ title: x.FileName, input: '', url: x.FileUrl, id: x.ID }))

        return new Promise((resolve, reject) => {
            resolve([...data, ...server_data])
        })
    }

    static async table_qa({ table_name, input }) {
        const response = await fetch(`/ChatBI/TableQA/generator`, { method: 'POST', body: JSON.stringify({ table_name, input }) })
        if (!response.ok) {
            console.log('table qa failed')
            return
        }
        const res = await response.json()
        return res.data.output
    }

    static async bi({ table_name, input }) {
        const response = await fetch(`/ChatBI/BI/generator`, { method: 'POST', body: JSON.stringify({ table_name, input }) })
        if (!response.ok) {
            console.log('table bi failed')
            return
        }
        const res = await response.json()
        // let res = {
        //     "code": "200",
        //     "data": {
        //         "input": "What are the top three results in the men's 100m final in Olympic history?",
        //         "output": {
        //             "answer": "Based on the **provided database**, the top three results in the men's 100m final in Olympic history are as follows:\n\n1. **Usain Bolt** from Jamaica achieved a time of **9.63 seconds** at the 2012 London Olympics, setting a new Olympic record.\n\n2. The same athlete, **Usain Bolt**, also holds the second-fastest time with **9.69 seconds** at the 2008 Beijing Olympics.\n\n3. **Yohan Blake**, another Jamaican sprinter, recorded the third-fastest time of **9.75 seconds** at the 2012 London Olympics.\n\nThese times represent the pinnacle of performance in this event and highlight the dominance of Jamaican sprinters in recent Olympic history.",
        //             "few_shots": "The question is: What was Usain Bolt's best result in the finals of the men's 100m event at the Olympics? The SQL query is: SELECT min(\"Final Score\") FROM \"100_metres_Men\" WHERE \"Final Score\" IS NOT NULL and Name = 'Usain Bolt';\nThe question is: What was Usain Bolt's worst result in the semifinals of the men's 100m event at the Olympics? The SQL query is: SELECT max(\"Semifinal Score\") FROM \"100_metres_Men\" WHERE \"Semifinal Score\"!='NA' and Name = 'Usain Bolt';\nThe question is: Which athlete had the slowest time in the final of the men's 100m event among all the Olympic champions? The SQL query is: SELECT \"Name\", \"Final Score\" FROM \"100_metres_Men\" WHERE \"Medal\" = 'Gold' and \"Final Score\" IS NOT NULL ORDER BY \"Final Score\" DESC LIMIT 1;",
        //             "fig_path": "https://city-brain-vendor.oss-cn-hangzhou.aliyuncs.com/saudi_gpt/web_app/BI/1722853150387.png?OSSAccessKeyId=LTAI5tBwX9b9oBbxxZP2Acng&Expires=1738405150&Signature=YB0zsOhfmocgLxYbXQh8DLy%2FY34%3D",
        //             "guidelines": "Pay attention to replace (') by ('') in the value string.\nPay attention to make sql query ending with (;).\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.",
        //             "instruction": "You are a SQLite expert. Given an input question, please create a syntactically correct *sqlite3* query to run. You must query only the columns that are needed to answer the question.",
        //             "python_code": "```python\nimport seaborn as sns\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\n# solution plan\n# i. Create a bar plot using seaborn to visualize the top three results.\n# ii. Add a title, x-axis label, y-axis label, and legend to the plot.\n\ndef plot(data: pd.DataFrame):\n    # Rename columns for clarity\n    data.columns = ['Final_Result', 'Name']\n\n    # Sort the data by Final_Result in ascending order\n    data.sort_values(by='Final_Result', inplace=True)\n\n    # Create a bar plot using seaborn to visualize the top three results\n    ax = sns.barplot(x=data[\"Final_Result\"], y=data[\"Name\"], palette='viridis')\n\n    # Add a title, x-axis label, y-axis label, and legend to the plot\n    plt.title('Top Three Results in Men\\'s 100m Final in Olympic History', wrap=True)\n    plt.xlabel('Time (seconds)')\n    plt.ylabel('Athlete')\n    plt.xticks(rotation=45)  # Rotate x-axis labels for legibility\n\n    return plt;\n\nchart = plot(data) # data already contains the data to be plotted. Always include this line. No additional code beyond this line.\n```",
        //             "sql_query": "SELECT \"Final_Result\", \"Name\" FROM \"100_metres_Men\" WHERE \"Final_Result\" IS NOT NULL AND \"Final_Result\" != 'NA' ORDER BY \"Final_Result\" ASC LIMIT 3;",
        //             "sql_result": "[(9.63, 'Usain Bolt'), (9.69, 'Usain Bolt'), (9.75, 'Yohan Blake')]",
        //             "sub_sql_query": "SELECT * FROM \"100_metres_Men\" WHERE \"Final_Result\" IS NOT NULL AND \"Final_Result\" != 'NA' ORDER BY \"Final_Result\" ASC LIMIT 3;",
        //             "sub_table": "|   Year | Name        |   Year_of_Birth |   Age | NOC   | Preliminary_Round_Result   |   Round_One_Result |   Quarter_Final_Result |   Semifinal_Result |   Final_Result | Medal   |\n|-------:|:------------|----------------:|------:|:------|:---------------------------|-------------------:|-----------------------:|-------------------:|---------------:|:--------|\n|   2012 | Usain Bolt  |            1986 |    26 | JAM   |                            |              10.09 |                        |               9.87 |           9.63 | Gold    |\n|   2008 | Usain Bolt  |            1986 |    22 | JAM   |                            |              10.2  |                   9.92 |               9.85 |           9.69 | Gold    |\n|   2012 | Yohan Blake |            1989 |    23 | JAM   |                            |              10    |                        |               9.85 |           9.75 | Silver  |",
        //             "table_context": "The \"Name\" column contains these related attribute values:Usain Bolt, Petar Petrov, Aleksey Khlopotnov, A. Papadakis\nThe \"Medal\" column contains these related attribute values:Gold, Bronze, Silver, NA\n",
        //             "table_schema": "\nCREATE TABLE \"100_metres_Men\" (\n\t\"Year\" BIGINT, \n\t\"Name\" TEXT, \n\t\"Year_of_Birth\" FLOAT, \n\t\"Age\" FLOAT, \n\t\"NOC\" TEXT, \n\t\"Preliminary_Round_Result\" FLOAT, \n\t\"Round_One_Result\" FLOAT, \n\t\"Quarter_Final_Result\" FLOAT, \n\t\"Semifinal_Result\" FLOAT, \n\t\"Final_Result\" FLOAT, \n\t\"Medal\" TEXT\n)\n\n/*\n3 rows from 100_metres_Men table:\nYear\tName\tYear_of_Birth\tAge\tNOC\tPreliminary_Round_Result\tRound_One_Result\tQuarter_Final_Result\tSemifinal_Result\tFinal_Result\tMedal\n2021\tLamont Marcell Jacobs\t1994.0\t27.0\tITA\tNone\t9.94\tNone\t9.84\t9.8\tGold\n2021\tFred Kerley\t1995.0\t26.0\tUSA\tNone\t9.97\tNone\t9.96\t9.84\tSilver\n2021\tAndre De Grasse\t1994.0\t27.0\tCAN\tNone\t9.91\tNone\t9.98\t9.89\tBronze\n*/"
        //         },
        //         "table_name": "100_meters_men"
        //     },
        //     "msg": "success"
        // }
        return res.data.output
    }

    static async get_question({ table_name, number_question }) {
        // http://172.16.0.148:9999/ChatBI/TableQA/getQuestions
        const response = await fetch(`/ChatBI/TableQA/getQuestions`, { method: 'POST', body: JSON.stringify({ table_name, number_question }) })
        if (!response.ok) {
            console.log('table qa failed')
            return
        }
        const res = await response.json()
        // const res = {
        //     "code": "200",
        //     "msg": "success",
        //     "data": {
        //         "table_name": "100_meters_men",
        //         "input": "who is the best player in the men's 100m event?",
        //         "output": ["list the top five players in this event", "Which athletes finished within 9.8 in the men's 100m at the Olympics?", "When was the first time a Chinese athlete participated in the men's 100m final at the Olympics? Who was the athlete?"]
        //     }
        // }
        return res.data
    }
}

// TableQAService.get_menu_items()
// TableQAService.get_table_data()